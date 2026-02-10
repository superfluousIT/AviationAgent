"""
Azure AI Foundry Agent for Aviation Information

This module implements an AI agent using Azure AI Foundry Agent Service that can interact with
the AviationStack API to provide flight information.
"""

import os
import json
from typing import Dict, Any, List, Optional
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet, AgentThreadCreationOptions, ThreadMessageOptions
from aviation_client import AviationStackClient


# Module-level aviation client for use by tool functions
_aviation_client = None


def get_aviation_client() -> AviationStackClient:
    """Get or create the aviation client singleton."""
    global _aviation_client
    if _aviation_client is None:
        _aviation_client = AviationStackClient()
    return _aviation_client


def get_flight_information(
    flight_iata: Optional[str] = None,
    airline_iata: Optional[str] = None,
    dep_iata: Optional[str] = None,
    arr_iata: Optional[str] = None,
    flight_status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Get real-time or historical flight information from the AviationStack API.
    Can search by flight number, airline, airports, or status.
    
    :param flight_iata: Flight IATA code (e.g., 'AA100', 'BA456')
    :param airline_iata: Airline IATA code (e.g., 'AA' for American Airlines)
    :param dep_iata: Departure airport IATA code (e.g., 'JFK', 'LAX')
    :param arr_iata: Arrival airport IATA code (e.g., 'JFK', 'LAX')
    :param flight_status: Flight status filter (scheduled, active, landed, cancelled, incident, diverted)
    :param limit: Maximum number of results to return (default: 10, max: 100)
    :return: JSON string with flight information
    """
    client = get_aviation_client()
    
    # Build kwargs, excluding None values
    kwargs = {}
    if flight_iata:
        kwargs['flight_iata'] = flight_iata
    if airline_iata:
        kwargs['airline_iata'] = airline_iata
    if dep_iata:
        kwargs['dep_iata'] = dep_iata
    if arr_iata:
        kwargs['arr_iata'] = arr_iata
    if flight_status:
        kwargs['flight_status'] = flight_status
    if limit:
        kwargs['limit'] = limit
    
    result = client.get_flights(**kwargs)
    return json.dumps(result)


class AviationAgent:
    """AI Agent for handling aviation-related queries using Azure AI Foundry."""
    
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
    
    def __init__(self):
        """Initialize the Aviation Agent with Azure AI Foundry project client."""
        # Initialize AI Project client
        self.project_client = self._initialize_project_client()
        
        # Get model deployment name
        self.model_name = os.getenv('AZURE_AI_MODEL_DEPLOYMENT_NAME', 'gpt-4o')
        
        # Create toolset with function tools
        self.toolset = self._create_toolset()
        
        # Enable auto function calls on the agents client
        self.project_client.agents.enable_auto_function_calls(tools=self.toolset)
        
        # Create or get the agent
        self.agent = self._get_or_create_agent()
        
        # Store current thread for conversation continuity
        self.current_thread_id = None
    
    def _initialize_project_client(self) -> AIProjectClient:
        """
        Initialize Azure AI Foundry project client with service principal authentication.
        
        Returns:
            Configured AIProjectClient
        """
        endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
        
        if not endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT is required")
        
        # Use service principal credentials
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if all([tenant_id, client_id, client_secret]):
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            # Fall back to default credential (managed identity, etc.)
            credential = DefaultAzureCredential()
        
        return AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
    
    def _create_toolset(self) -> ToolSet:
        """
        Create a toolset with the available function tools.
        
        Returns:
            Configured ToolSet
        """
        toolset = ToolSet()
        
        # Create function tool with the flight information function
        function_tool = FunctionTool(functions={get_flight_information})
        toolset.add(function_tool)
        
        return toolset
    
    def _get_or_create_agent(self):
        """
        Get existing agent or create a new one in Azure AI Foundry.
        
        Returns:
            The agent object
        """
        agents_client = self.project_client.agents
        
        # Try to find existing agent by name
        existing_agents = agents_client.list_agents()
        for agent in existing_agents:
            if agent.name == self.AGENT_NAME:
                # Update the agent with latest configuration
                return agents_client.update_agent(
                    agent_id=agent.id,
                    model=self.model_name,
                    instructions=self.AGENT_INSTRUCTIONS,
                    tools=self.toolset.get_definitions_and_resources().get("tools", [])
                )
        
        # Create new agent
        return agents_client.create_agent(
            model=self.model_name,
            name=self.AGENT_NAME,
            instructions=self.AGENT_INSTRUCTIONS,
            toolset=self.toolset
        )
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_message: The user's message/query
            
        Returns:
            The agent's response
        """
        try:
            agents_client = self.project_client.agents
            
            # Create thread options with the user message
            thread_options = AgentThreadCreationOptions(
                messages=[
                    ThreadMessageOptions(
                        role="user",
                        content=user_message
                    )
                ]
            )
            
            # Run the agent - this handles tool execution automatically
            run = agents_client.create_thread_and_process_run(
                agent_id=self.agent.id,
                thread=thread_options,
                toolset=self.toolset
            )
            
            # Store thread ID for potential future use
            self.current_thread_id = run.thread_id
            
            # Check run status
            if run.status == "failed":
                error_msg = run.last_error.message if run.last_error else "Unknown error"
                return f"Error processing request: {error_msg}"
            
            # Get the assistant's response
            response_content = agents_client.messages.get_last_message_text_by_role(
                thread_id=run.thread_id,
                role="assistant"
            )
            
            # Extract text value from MessageTextContent object
            if response_content and response_content.text:
                return response_content.text.value
            return "No response generated."
            
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def reset_conversation(self):
        """Reset the conversation by clearing the current thread."""
        self.current_thread_id = None
