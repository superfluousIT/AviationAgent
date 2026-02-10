# AviationAgent

An intelligent aviation information agent built on Azure AI Foundry that leverages the AviationStack API to provide real-time and historical flight data through a simple web application.

## Overview

AviationAgent is an AI-powered agent designed to deliver comprehensive aviation information through natural language interactions. Built on Microsoft's Azure AI Foundry platform, this agent provides a conversational interface to access global aviation data powered by the AviationStack API.

## Features

- **Real-Time Flight Information**: Get current flight status, departure and arrival details
- **Natural Language Interface**: Ask questions in plain English
- **Web-Based UI**: Simple and intuitive chat interface
- **Azure AI Integration**: Powered by Azure OpenAI with function calling
- **Service Principal Authentication**: Secure enterprise authentication
- **AviationStack API Integration**: Access to comprehensive flight data

## Technology Stack

- **Backend**: Python with Flask
- **AI Platform**: Azure OpenAI (GPT-4)
- **Authentication**: Azure Service Principal
- **API Provider**: AviationStack
- **Frontend**: HTML/CSS/JavaScript

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.8+** installed
2. **Azure AI Foundry** account with:
   - Azure OpenAI resource deployed
   - Service principal credentials (or API key)
   - GPT-4 (or GPT-3.5-turbo) deployment
3. **AviationStack API key** (free tier available at [aviationstack.com](https://aviationstack.com))

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/superfluousIT/AviationAgent.git
cd AviationAgent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Azure AI Foundry Service Principal Credentials
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_SUBSCRIPTION_ID=your-subscription-id-here
AZURE_RESOURCE_GROUP=your-resource-group-here
AZURE_PROJECT_NAME=your-project-name-here

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# AviationStack API Configuration
AVIATIONSTACK_API_KEY=your-aviationstack-api-key-here
AVIATIONSTACK_BASE_URL=http://api.aviationstack.com/v1

# Application Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
```

## Getting Your Credentials

### Azure Service Principal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Note down:
   - Application (client) ID → `AZURE_CLIENT_ID`
   - Directory (tenant) ID → `AZURE_TENANT_ID`
5. Go to **Certificates & secrets** > **New client secret**
6. Copy the secret value → `AZURE_CLIENT_SECRET`
7. Assign appropriate roles to your service principal for Azure OpenAI access

### Azure OpenAI

1. Create an Azure OpenAI resource in [Azure Portal](https://portal.azure.com)
2. Deploy a model (e.g., GPT-4 or GPT-3.5-turbo)
3. Get your endpoint from the resource overview → `AZURE_OPENAI_ENDPOINT`
4. Get your API key from **Keys and Endpoint** section → `AZURE_OPENAI_API_KEY`
5. Note your deployment name → `AZURE_OPENAI_DEPLOYMENT_NAME`

### AviationStack API

1. Sign up at [aviationstack.com](https://aviationstack.com)
2. Get your API key from the dashboard → `AVIATIONSTACK_API_KEY`
3. Free tier includes 100 API calls per month

## Usage

### Running the Application

Start the Flask development server:

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. You'll see a chat interface with example queries
3. Type your question or click on an example query
4. The AI agent will process your request and fetch flight information

### Example Queries

- "Show me flights from JFK to LAX"
- "What's the status of flight AA100?"
- "Find American Airlines flights"
- "Show me active flights from London Heathrow"
- "Find flights to Dubai"

## Project Structure

```
AviationAgent/
├── app.py                  # Flask web application
├── aviation_agent.py       # AI agent implementation
├── aviation_client.py      # AviationStack API client
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── templates/
│   └── index.html         # Web UI
└── README.md              # This file
```

## API Endpoints

### `GET /`
Renders the main web interface.

### `POST /api/chat`
Send a message to the AI agent.

**Request Body:**
```json
{
  "message": "Show me flights from JFK"
}
```

**Response:**
```json
{
  "response": "Here are the flights from JFK...",
  "session_id": "abc123..."
}
```

### `POST /api/reset`
Reset the conversation history.

**Response:**
```json
{
  "message": "Conversation reset successfully"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Aviation Agent"
}
```

## Free Tier Limitations

This project is designed to work with free tier services:

### AviationStack Free Tier
- 100 API requests per month
- Access to flights endpoint
- Real-time and historical data
- No commercial use

### Azure OpenAI
- Pay-as-you-go pricing applies
- Consider using GPT-3.5-turbo for lower costs
- Implement rate limiting for production use

## Security Best Practices

⚠️ **Important**: Never commit your `.env` file to version control!

- The `.gitignore` file is configured to exclude `.env` files
- Use Azure Key Vault for production deployments
- Rotate your credentials regularly
- Use managed identities when deploying to Azure

## Deployment

### Deploy to Azure App Service

1. Create an App Service in Azure Portal
2. Configure environment variables in **Configuration** > **Application settings**
3. Deploy using Git, GitHub Actions, or Azure CLI:

```bash
az webapp up --name your-app-name --resource-group your-rg --runtime "PYTHON:3.11"
```

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
```

Build and run:

```bash
docker build -t aviation-agent .
docker run -p 8000:8000 --env-file .env aviation-agent
```

## Troubleshooting

### "AviationStack API key is required"
- Ensure `AVIATIONSTACK_API_KEY` is set in your `.env` file
- Check that `.env` file is in the same directory as `app.py`

### "Error processing request"
- Verify your Azure OpenAI credentials are correct
- Check that your deployment name matches the one in `.env`
- Ensure your service principal has access to the Azure OpenAI resource

### No flight data returned
- AviationStack free tier has limited requests
- Check your API usage at aviationstack.com dashboard
- Verify airport/airline codes are valid (e.g., "JFK", "AA")

## API Documentation

- [AviationStack API Documentation](https://aviationstack.com/documentation)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
- Check the [AviationStack FAQ](https://aviationstack.com/faq)
- Review [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- Open an issue in this repository

## Acknowledgments

- [AviationStack](https://aviationstack.com) for providing aviation data API
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry) for the AI platform
- [Flask](https://flask.palletsprojects.com/) for the web framework
