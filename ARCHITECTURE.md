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
│  - Azure AI Agents SDK      │
│  - Function calling         │
│  - Tool execution           │
└──────┬──────────────────────┘
       │
       ├──────────────┬────────────────┐
       ▼              ▼                ▼
┌─────────────┐ ┌──────────┐ ┌─────────────────┐
│  Azure AI   │ │ Aviation │ │ Session         │
│  Projects   │ │ Client   │ │ Management      │
│  SDK v2     │ │          │ │                 │
│ Responses   │ │ Flights  │ │ Per-user agents │
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

**Purpose**: AI agent orchestrator using Azure AI Projects SDK v2 with the OpenAI Responses API

**Key Features**:
- Azure AI Foundry new Agents API (not classic/assistants)
- OpenAI Responses API for multi-turn conversations
- Service principal authentication support
- Manual function calling with tool-call loop

**Function Tools**:
The agent registers FunctionTool definitions with the agent, then handles tool calls manually:

```python
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition, AgentReference

# Tools defined in agent definition
definition = PromptAgentDefinition(model=model, instructions=..., tools=[function_tool])
agent = project_client.agents.create(name=..., definition=definition)

# Chat uses OpenAI Responses API with agent reference
response = openai_client.responses.create(
    input=user_message, model=model,
    extra_body={"agent": AgentReference(name=agent.name).as_dict()}
)
```

**Authentication Flow**:
1. Try service principal credentials if configured
2. Fall back to DefaultAzureCredential (managed identity, etc.)
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
   - Calls OpenAI Responses API with agent reference
   - Model decides to use `get_flight_information` function tool

5. **Function Execution** (manual tool-call loop):
   - Agent detects `function_call` items in response output
   - Executes `aviation_client.get_flights(dep_iata='JFK', arr_iata='LAX')`
   - Sends tool outputs back via follow-up `responses.create()`

6. **Response Generation**:
   - Function results processed by the model
   - Agent generates natural language response
   - Text extracted from `response.output_text`

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
# Azure AI Agents (Required)
AZURE_AI_PROJECT_ENDPOINT=https://your-ai-services-account.services.ai.azure.com/api/projects/your-project-name
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o

# Azure Service Principal (Recommended)
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
- Agent token usage
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

### Azure AI
- Model-dependent limits
- Token-based pricing
- Function tool overhead

### Best Practices
- Cache repeated queries
- Batch requests when possible
- Monitor usage dashboards
- Set up alerts for limits
