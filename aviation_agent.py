"""
Azure AI Foundry Agent for Aviation Information

This module implements an AI agent using the new Azure AI Foundry Agents API
(azure-ai-projects v2) with the OpenAI Responses API pattern to interact with
the AviationStack API and provide flight information.

This creates "new" agents in Azure AI Foundry (not classic/assistants agents).
"""

import os
import json
import logging
from typing import Any, Optional
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    FunctionTool,
    AgentReference,
    FunctionToolCallOutputItemParam,
)
from aviation_client import AviationStackClient

logger = logging.getLogger(__name__)

# Module-level aviation client for use by tool functions
_aviation_client = None


def get_aviation_client() -> AviationStackClient:
    """Get or create the aviation client singleton."""
    global _aviation_client
    if _aviation_client is None:
        _aviation_client = AviationStackClient()
    return _aviation_client


# Function tool definitions for the agent
TOOL_FUNCTIONS = {
    "get_flight_information": {
        "callable": None,  # set below
        "definition": FunctionTool(
            name="get_flight_information",
            description=(
                "Get real-time or historical flight information from the AviationStack API. "
                "Can search by flight number, airline, airports, or status."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "flight_iata": {
                        "type": "string",
                        "description": "Flight IATA code (e.g., 'AA100', 'BA456')",
                    },
                    "airline_iata": {
                        "type": "string",
                        "description": "Airline IATA code (e.g., 'AA' for American Airlines)",
                    },
                    "dep_iata": {
                        "type": "string",
                        "description": "Departure airport IATA code (e.g., 'JFK', 'LAX')",
                    },
                    "arr_iata": {
                        "type": "string",
                        "description": "Arrival airport IATA code (e.g., 'JFK', 'LAX')",
                    },
                    "flight_status": {
                        "type": "string",
                        "description": "Flight status filter (scheduled, active, landed, cancelled, incident, diverted)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, max: 100)",
                        "default": 10,
                    },
                },
                "required": [],
            },
            strict=False,
        ),
    }
}


def _execute_get_flight_information(arguments: dict) -> str:
    """Execute the get_flight_information tool with parsed arguments."""
    client = get_aviation_client()
    kwargs = {k: v for k, v in arguments.items() if v is not None}
    result = client.get_flights(**kwargs)
    return json.dumps(result)


TOOL_FUNCTIONS["get_flight_information"]["callable"] = _execute_get_flight_information


class AviationAgent:
    """AI Agent for handling aviation-related queries using the new Azure AI Foundry Agents API."""

    AGENT_NAME = "AviationAssistant"
    AGENT_INSTRUCTIONS = """You are an aviation information assistant powered by the AviationStack API. 
You can help users find real-time and historical flight information, including:
- Flight status and tracking
- Departure and arrival information
- Airline details
- Airport information

When users ask about flights, use the get_flight_information tool to retrieve data.
Always provide clear, helpful responses and explain any limitations (like free tier restrictions).
If airport or airline codes are mentioned, use them to search. Common codes include:
- Airports: JFK (New York), LAX (Los Angeles), LHR (London), CDG (Paris), DXB (Dubai)
- Airlines: AA (American), BA (British Airways), DL (Delta), UA (United), LH (Lufthansa)
"""

    MAX_TOOL_ROUNDS = 5  # max rounds of tool calls per chat turn

    def __init__(self):
        """Initialize the Aviation Agent with the new Agents API (azure-ai-projects v2)."""
        self._credential = self._build_credential()

        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT is required")

        self.endpoint = endpoint
        self.model_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")

        # Build tool list for the agent definition
        self._tools = [TOOL_FUNCTIONS[name]["definition"] for name in TOOL_FUNCTIONS]

        # Create project client and OpenAI client (context-managed)
        self.project_client = AIProjectClient(
            endpoint=self.endpoint, credential=self._credential
        )

        # Register or update the agent in Azure AI Foundry (new agents, not classic)
        self.agent = self._create_or_update_agent()

        # Get an authenticated OpenAI client for the Responses API
        self.openai_client = self.project_client.get_openai_client()

        # Per-session previous_response_id to enable multi-turn
        self._previous_response_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Credential / setup helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_credential():
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        if all([tenant_id, client_id, client_secret]):
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
        return DefaultAzureCredential()

    def _create_or_update_agent(self):
        """
        Create a new agent version in Azure AI Foundry (new Agents API).

        Uses agents.create() which creates a new-style agent that appears under
        the "Agents" section in the portal (not "Classic Agents").
        """
        definition = PromptAgentDefinition(
            model=self.model_name,
            instructions=self.AGENT_INSTRUCTIONS,
            tools=self._tools,
        )

        try:
            # Try to create a new version of an existing agent
            agent = self.project_client.agents.create_version(
                agent_name=self.AGENT_NAME,
                definition=definition,
            )
            logger.info("Created agent version: %s v%s", agent.name, agent.version)
        except Exception:
            # Agent doesn't exist yet — create it
            agent = self.project_client.agents.create(
                name=self.AGENT_NAME,
                definition=definition,
            )
            logger.info("Created new agent: %s v%s", agent.name, agent.version)

        return agent

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def _execute_tool_call(self, name: str, arguments_json: str) -> str:
        """Dispatch a function tool call to the local implementation."""
        tool_entry = TOOL_FUNCTIONS.get(name)
        if not tool_entry:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            args = json.loads(arguments_json) if arguments_json else {}
            return tool_entry["callable"](args)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        Uses the OpenAI Responses API with an agent reference so the request
        is routed through the registered Azure AI Foundry agent.

        Args:
            user_message: The user's message/query

        Returns:
            The agent's response text
        """
        try:
            # Build the initial response request
            # Note: instructions and tools come from the agent definition;
            # passing them here when an agent reference is set is not allowed.
            response = self.openai_client.responses.create(
                input=user_message,
                model=self.model_name,
                previous_response_id=self._previous_response_id,
                extra_body={
                    "agent": AgentReference(name=self.agent.name).as_dict()
                },
            )

            # Handle tool-call loop
            for _ in range(self.MAX_TOOL_ROUNDS):
                # Collect any function_call outputs in this response
                tool_calls = [
                    item for item in response.output
                    if item.type == "function_call"
                ]
                if not tool_calls:
                    break

                # Execute each tool call and build output items
                tool_outputs = []
                for call in tool_calls:
                    result = self._execute_tool_call(call.name, call.arguments)
                    tool_outputs.append(
                        FunctionToolCallOutputItemParam(
                            call_id=call.call_id,
                            output=result,
                        ).as_dict()
                    )

                # Send tool outputs back and get next response
                response = self.openai_client.responses.create(
                    input=tool_outputs,
                    model=self.model_name,
                    previous_response_id=response.id,
                    extra_body={
                        "agent": AgentReference(name=self.agent.name).as_dict()
                    },
                )

            # Save response id for multi-turn conversation
            self._previous_response_id = response.id

            # Extract the text output
            return response.output_text or "No response generated."

        except Exception as e:
            logger.exception("Error processing request")
            return f"Error processing request: {str(e)}"

    def reset_conversation(self):
        """Reset the conversation by clearing the response chain."""
        self._previous_response_id = None
