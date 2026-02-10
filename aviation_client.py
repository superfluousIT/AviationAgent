"""
AviationStack API Client for Flight Data

This module provides a client for interacting with the AviationStack API,
specifically for the flights endpoint. It's designed to work with the free tier.
"""

import os
import requests
from typing import Dict, Any, Optional, List


class AviationStackClient:
    """Client for interacting with the AviationStack API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the AviationStack client.
        
        Args:
            api_key: AviationStack API key (defaults to env variable)
            base_url: Base URL for the API (defaults to env variable)
        """
        self.api_key = api_key or os.getenv('AVIATIONSTACK_API_KEY')
        self.base_url = base_url or os.getenv('AVIATIONSTACK_BASE_URL', 'http://api.aviationstack.com/v1')
        
        if not self.api_key:
            raise ValueError("AviationStack API key is required")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the AviationStack API.
        
        Args:
            endpoint: API endpoint (e.g., 'flights')
            params: Query parameters
            
        Returns:
            JSON response from the API
            
        Raises:
            requests.RequestException: If the request fails
        """
        # Add API key to params
        params['access_key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": {
                    "code": "api_error",
                    "message": f"Failed to fetch data from AviationStack: {str(e)}"
                }
            }
    
    def get_flights(self, 
                    flight_iata: Optional[str] = None,
                    flight_icao: Optional[str] = None,
                    airline_name: Optional[str] = None,
                    airline_iata: Optional[str] = None,
                    airline_icao: Optional[str] = None,
                    dep_iata: Optional[str] = None,
                    dep_icao: Optional[str] = None,
                    arr_iata: Optional[str] = None,
                    arr_icao: Optional[str] = None,
                    flight_status: Optional[str] = None,
                    limit: int = 10) -> Dict[str, Any]:
        """
        Get flight information from the AviationStack API.
        
        Args:
            flight_iata: Flight IATA code (e.g., 'AA100')
            flight_icao: Flight ICAO code
            airline_name: Airline name
            airline_iata: Airline IATA code (e.g., 'AA')
            airline_icao: Airline ICAO code
            dep_iata: Departure airport IATA code (e.g., 'JFK')
            dep_icao: Departure airport ICAO code
            arr_iata: Arrival airport IATA code (e.g., 'LAX')
            arr_icao: Arrival airport ICAO code
            flight_status: Flight status (scheduled, active, landed, cancelled, etc.)
            limit: Maximum number of results (default: 10, max: 100 for free tier)
            
        Returns:
            Dictionary containing flight data or error information
        """
        params = {}
        
        # Add only non-None parameters
        if flight_iata:
            params['flight_iata'] = flight_iata
        if flight_icao:
            params['flight_icao'] = flight_icao
        if airline_name:
            params['airline_name'] = airline_name
        if airline_iata:
            params['airline_iata'] = airline_iata
        if airline_icao:
            params['airline_icao'] = airline_icao
        if dep_iata:
            params['dep_iata'] = dep_iata
        if dep_icao:
            params['dep_icao'] = dep_icao
        if arr_iata:
            params['arr_iata'] = arr_iata
        if arr_icao:
            params['arr_icao'] = arr_icao
        if flight_status:
            params['flight_status'] = flight_status
        
        # Limit results (free tier has a max of 100)
        params['limit'] = min(limit, 100)
        
        return self._make_request('flights', params)
    
    def search_flights(self, query: str) -> Dict[str, Any]:
        """
        Search for flights based on a natural language query.
        This is a helper method to parse common queries.
        
        Args:
            query: Natural language query (e.g., "flights from JFK to LAX")
            
        Returns:
            Dictionary containing flight data
        """
        # Simple keyword extraction for common patterns
        query_lower = query.lower()
        params = {}
        
        # Extract airport codes (simple pattern matching)
        words = query_lower.split()
        
        # Look for "from X to Y" pattern
        if 'from' in words:
            from_idx = words.index('from')
            if from_idx + 1 < len(words):
                potential_code = words[from_idx + 1].upper()
                if len(potential_code) == 3:
                    params['dep_iata'] = potential_code
        
        if 'to' in words:
            to_idx = words.index('to')
            if to_idx + 1 < len(words):
                potential_code = words[to_idx + 1].upper()
                if len(potential_code) == 3:
                    params['arr_iata'] = potential_code
        
        # Look for flight numbers (e.g., "AA100", "BA456")
        for word in words:
            word_upper = word.upper()
            if len(word_upper) >= 4 and word_upper[:2].isalpha() and word_upper[2:].isdigit():
                params['flight_iata'] = word_upper
                break
        
        # Look for airline codes (2-letter codes)
        for word in words:
            word_upper = word.upper()
            if len(word_upper) == 2 and word_upper.isalpha():
                params['airline_iata'] = word_upper
                break
        
        return self.get_flights(**params)
