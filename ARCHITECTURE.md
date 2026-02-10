# Aviation Agent Architecture

## Overview

This document describes the architecture and design of the Aviation Agent application.

## System Architecture

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────┐
│    Flask Web Application    │
│         (app.py)            │
├─────────────────────────────┤
│  Routes:                    │
│  - GET  /                   │
│  - POST /api/chat           │
│  - POST /api/reset          │
│  - GET  /health             │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    Aviation Agent           │
│   (aviation_agent.py)       │
├─────────────────────────────┤
│  - Conversation management  │
│  - Azure OpenAI integration │
│  - Function calling         │
│  - Tool execution           │
└──────┬──────────────────────┘
       │
       ├──────────────┬────────────────┐
       ▼              ▼                ▼
┌─────────────┐ ┌──────────┐ ┌─────────────────┐
│  Azure      │ │ Aviation │ │ Session         │
│  OpenAI     │ │ Client   │ │ Management      │
│             │ │          │ │                 │
│ GPT-4       │ │ Flights  │ │ Per-user agents │
│ Function    │ │ API      │ │ Conversation    │
│ Calling     │ │          │ │ History         │
└─────────────┘ └────┬─────┘ └─────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │ AviationStack│
              │     API      │
              │              │
              │ /v1/flights  │
              └──────────────┘
```

## Components

### 1. Web Application (app.py)

**Purpose**: Flask-based web server providing the HTTP interface

**Key Features**:
- Session management for multi-user support
- RESTful API endpoints
- Static file serving for UI
- Health check endpoint

**Endpoints**:
- `GET /` - Main UI page
- `POST /api/chat` - Send message to agent
- `POST /api/reset` - Reset conversation
- `GET /health` - Service health check

### 2. Aviation Agent (aviation_agent.py)

**Purpose**: AI agent orchestrator using Azure OpenAI

**Key Features**:
- Azure OpenAI integration with function calling
- Service principal authentication support
- Conversation history management
- Tool/function execution

**Function Calling**:
The agent uses OpenAI's function calling feature to decide when to fetch flight data:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_flight_information",
        "parameters": { ... }
    }
}]
```

**Authentication Flow**:
1. Try API key authentication first (simpler)
2. Fall back to service principal if configured
3. Use ClientSecretCredential for token acquisition

### 3. Aviation Client (aviation_client.py)

**Purpose**: AviationStack API client for flight data

**Key Features**:
- RESTful API client for flights endpoint
- Query parameter handling
- Error handling and timeouts
- Free tier optimization (limit=10 default)

**Supported Queries**:
- Flight number (IATA/ICAO)
- Airline (name, IATA, ICAO)
- Departure airport (IATA/ICAO)
- Arrival airport (IATA/ICAO)
- Flight status

### 4. Web UI (templates/index.html)

**Purpose**: Single-page chat interface

**Key Features**:
- Real-time chat interface
- Example queries
- Loading states
- Responsive design
- Session persistence

## Data Flow

### Typical User Query Flow

1. **User Input**: User types "Show me flights from JFK to LAX"

2. **Frontend**: 
   - JavaScript captures input
   - Sends POST to `/api/chat`
   - Displays loading state

3. **Flask Backend**:
   - Receives request
   - Retrieves session-specific agent
   - Passes message to agent

4. **Aviation Agent**:
   - Adds message to conversation history
   - Calls Azure OpenAI API
   - Model decides to use `get_flight_information` function

5. **Function Execution**:
   - Agent calls `aviation_client.get_flights(dep_iata='JFK', arr_iata='LAX')`
   - Client makes HTTP request to AviationStack API
   - Returns JSON response

6. **Response Generation**:
   - Function result added to conversation
   - Second OpenAI call to generate natural language response
   - Response formatted for user

7. **Frontend Display**:
   - Receives response
   - Renders in chat interface
   - Updates conversation history

## Security Considerations

### Credential Management

1. **Environment Variables**: All credentials stored in `.env` file
2. **Git Ignore**: `.env` files excluded from version control
3. **Service Principal**: Azure authentication via service principal
4. **Session Keys**: Random session keys for user isolation

### Best Practices Implemented

- ✅ Credentials in environment variables
- ✅ `.gitignore` configured for sensitive files
- ✅ Service principal authentication support
- ✅ Session-based user isolation
- ✅ HTTPS recommended for production
- ✅ Input validation on API endpoints
- ✅ Error handling without exposing internals

## Configuration

### Required Environment Variables

```env
# Azure OpenAI (Required)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# OR Azure Service Principal (Alternative)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-secret

# AviationStack (Required)
AVIATIONSTACK_API_KEY=your-key-here

# Application (Optional)
PORT=5000
FLASK_DEBUG=True
```

## Deployment Considerations

### Local Development
- Use `.env` file for credentials
- Flask debug mode enabled
- Single-threaded development server

### Production Deployment
- Use Azure Key Vault or managed secrets
- Production WSGI server (gunicorn)
- HTTPS with valid certificate
- Environment-based configuration
- Monitoring and logging
- Rate limiting
- CORS configuration if needed

### Azure App Service
- Configure application settings (replaces `.env`)
- Use managed identity instead of service principal
- Enable Application Insights
- Configure scaling rules

## Future Enhancements

### Potential Improvements
1. Add more AviationStack endpoints (airlines, airports, routes)
2. Implement caching to reduce API calls
3. Add user authentication
4. Persistent conversation storage
5. Rate limiting per user
6. Streaming responses
7. Voice interface
8. Mobile app
9. Analytics dashboard
10. Multi-language support

### v1.0 Limitations
- Flights endpoint only
- No conversation persistence
- Basic error handling
- Free tier constraints
- Single model deployment

## Performance Optimization

### Current Optimizations
- Session-based agent reuse
- Async-capable architecture
- Timeout on API calls
- Limited result sets (default: 10)

### Recommended for Scale
- Redis for session storage
- Response caching
- Connection pooling
- Load balancing
- CDN for static assets
- Database for conversation history

## Testing Strategy

### Unit Tests (Future)
- `aviation_client.py` - API client logic
- `aviation_agent.py` - Agent orchestration
- `app.py` - Flask routes

### Integration Tests (Future)
- End-to-end conversation flows
- API error handling
- Authentication flows

### Manual Testing
- UI functionality
- Example queries
- Error scenarios
- Free tier limits
- Session management

## Monitoring and Observability

### Recommended Metrics
- API response times
- AviationStack API usage
- OpenAI token usage
- Error rates
- User sessions
- Query patterns

### Logging Points
- API requests/responses
- Authentication events
- Function calls
- Errors and exceptions
- User queries (privacy-safe)

## API Rate Limits

### AviationStack Free Tier
- 100 requests/month
- No rate limit per second
- Flights endpoint only

### Azure OpenAI
- Model-dependent limits
- Token-based pricing
- Function call overhead

### Best Practices
- Cache repeated queries
- Batch requests when possible
- Monitor usage dashboards
- Set up alerts for limits
