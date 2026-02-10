"""
Azure AI Agent for Aviation Information

This module implements an AI agent using Azure OpenAI that can interact with
the AviationStack API to provide flight information.
"""

import os
import json
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from aviation_client import AviationStackClient


class AviationAgent:
    """AI Agent for handling aviation-related queries."""
    
    def __init__(self):
        """Initialize the Aviation Agent with Azure OpenAI and AviationStack clients."""
        # Initialize AviationStack client
        self.aviation_client = AviationStackClient()
        
        # Initialize Azure OpenAI client
        self.client = self._initialize_azure_client()
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        
        # Define available tools for the agent
        self.tools = self._define_tools()
        
        # Store conversation history
        self.messages = []
    
    def _initialize_azure_client(self) -> AzureOpenAI:
        """
        Initialize Azure OpenAI client with service principal authentication.
        
        Returns:
            Configured AzureOpenAI client
        """
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        
        # Use API key if provided, otherwise fall back to managed identity
        if api_key:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-15-preview"
            )
        else:
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
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                
                client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_ad_token=token.token,
                    api_version="2024-02-15-preview"
                )
            else:
                raise ValueError("Either AZURE_OPENAI_API_KEY or service principal credentials are required")
        
        return client
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define the tools (functions) available to the AI agent.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_flight_information",
                    "description": "Get real-time or historical flight information from the AviationStack API. Can search by flight number, airline, airports, or status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "flight_iata": {
                                "type": "string",
                                "description": "Flight IATA code (e.g., 'AA100', 'BA456')"
                            },
                            "airline_iata": {
                                "type": "string",
                                "description": "Airline IATA code (e.g., 'AA' for American Airlines, 'BA' for British Airways)"
                            },
                            "dep_iata": {
                                "type": "string",
                                "description": "Departure airport IATA code (e.g., 'JFK', 'LAX', 'LHR')"
                            },
                            "arr_iata": {
                                "type": "string",
                                "description": "Arrival airport IATA code (e.g., 'JFK', 'LAX', 'LHR')"
                            },
                            "flight_status": {
                                "type": "string",
                                "description": "Flight status filter",
                                "enum": ["scheduled", "active", "landed", "cancelled", "incident", "diverted"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 10, max: 100)",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool (function call) and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            JSON string of the result
        """
        if tool_name == "get_flight_information":
            result = self.aviation_client.get_flights(**arguments)
            return json.dumps(result)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_message: The user's message/query
            
        Returns:
            The agent's response
        """
        # Add user message to conversation history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # System message for the agent
        if len(self.messages) == 1:
            self.messages.insert(0, {
                "role": "system",
                "content": """You are an aviation information assistant powered by the AviationStack API. 
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
            })
        
        try:
            # Make initial API call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call a function
            if response_message.tool_calls:
                # Add assistant's message to conversation
                self.messages.append(response_message)
                
                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the function
                    function_response = self._execute_tool(function_name, function_args)
                    
                    # Add function response to conversation
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    })
                
                # Get final response from the model
                second_response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=self.messages
                )
                
                final_message = second_response.choices[0].message.content
            else:
                final_message = response_message.content
            
            # Add assistant's response to conversation history
            self.messages.append({
                "role": "assistant",
                "content": final_message
            })
            
            return final_message
            
        except Exception as e:
            error_message = f"Error processing request: {str(e)}"
            self.messages.append({
                "role": "assistant",
                "content": error_message
            })
            return error_message
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.messages = []
