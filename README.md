# AviationAgent

An intelligent aviation information agent built on Azure AI Foundry that leverages the AviationStack API to provide real-time flight data through a simple web application.

## Overview

AviationAgent is an AI-powered agent designed to deliver comprehensive aviation information through natural language interactions. Built on the Azure AI Agents SDK (new Agents API), this agent provides a conversational interface to access global aviation data powered by the AviationStack API.

## Features

- 🤖 **AI-Powered Conversations**: Natural language interface using the Azure AI Agents SDK
- ✈️ **Real-Time Flight Data**: Access live flight information via AviationStack API
- 🌐 **Simple Web Interface**: Clean, intuitive chat-based UI
- 🔐 **Secure Authentication**: Azure Service Principal support
- 🆓 **Free Tier Compatible**: Works with free tiers of both services

## Quick Start

### Prerequisites
- Python 3.8+
- Azure AI Foundry account with a project endpoint
- AviationStack API key (free tier available)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/superfluousIT/AviationAgent.git
cd AviationAgent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
```
http://localhost:5000
```

## Configuration

The application requires the following environment variables in your `.env` file:

### Azure AI Agents
- `AZURE_AI_PROJECT_ENDPOINT` - Your Azure AI project endpoint
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` - Model deployment name (e.g., gpt-4o)

### Service Principal (Recommended)
- `AZURE_TENANT_ID` - Azure tenant ID
- `AZURE_CLIENT_ID` - Service principal client ID
- `AZURE_CLIENT_SECRET` - Service principal secret

### AviationStack API
- `AVIATIONSTACK_API_KEY` - Your AviationStack API key

See `.env.example` for a complete template.

## Usage Examples

Once running, try asking:
- "Show me flights from JFK to LAX"
- "What's the status of flight AA100?"
- "Find American Airlines flights"
- "Show me active flights from London Heathrow"

## Project Structure

```
AviationAgent/
├── app.py                 # Flask web application
├── aviation_agent.py      # AI agent using Azure AI Agents SDK
├── aviation_client.py     # AviationStack API client
├── templates/
│   └── index.html        # Web interface
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── SETUP.md              # Detailed setup guide
└── README.md             # This file
```

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions, credential configuration, and deployment guide
- **[AviationStack API](https://aviationstack.com/documentation)** - API documentation
- **[Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/)** - Azure AI documentation

## Technology Stack

- **Backend**: Python with Flask
- **AI Platform**: Azure AI Projects SDK v2 (`azure-ai-projects`)
- **Authentication**: Azure Service Principal
- **API Provider**: AviationStack
- **Frontend**: HTML/CSS/JavaScript

## Current Implementation (v1.0)

This first version focuses on the **flights API** only, providing:
- Real-time flight status and tracking
- Flight search by number, airline, or route
- Departure and arrival information
- Natural language query processing

## Free Tier Limitations

### AviationStack Free Tier
- 100 API requests per month
- Access to flights endpoint only
- Real-time and historical data

### Azure AI
- Pay-as-you-go pricing
- Consider using lower-cost model deployments

## Security

⚠️ **Important**: Never commit credentials to version control!

- `.env` files are excluded via `.gitignore`
- Use Azure Key Vault for production
- Rotate credentials regularly

## Support

For detailed setup instructions, troubleshooting, and deployment guides, see **[SETUP.md](SETUP.md)**.

## License

This project is provided as-is for educational and development purposes.
