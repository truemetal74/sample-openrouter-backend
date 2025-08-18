# Sample OpenRouter Backend

A production-ready FastAPI application that provides a single API endpoint for LLM interactions via OpenRouter. Built with Python 3.13, FastAPI, and Pydantic v2.

> **Note**: This project was renamed from "no-bs-back" to "sample-openrouter-backend" to better reflect its purpose as a reference implementation.

## 🚀 Features

- **Single API Endpoint**: `/ask-llm` for all LLM interactions
- **Prompt Management**: Server-stored prompt templates with variable substitution
- **OpenRouter Integration**: Support for multiple AI models with automatic retry and rate limit handling
- **Rate Limiting**: IP-based rate limiting with whitelist functionality
- **Authentication**: JWT-based access control
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Comprehensive Logging**: All inbound requests and returned data logged independently of endpoint implementation
- **Request ID Tracking**: Automatic request ID extraction from headers or generation for distributed tracing
- **Docker Support**: Containerized deployment
- **GCP Ready**: Deployment scripts for Google Cloud Platform

## 📋 Requirements

- Python 3.13+
- FastAPI
- OpenRouter API key
- Docker (for containerized deployment)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd sample-openrouter-backend
```

### 2. Create and activate virtual environment
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
SECRET_KEY=your_secret_key_here

# Optional (with defaults)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODELS=["openai/gpt-4","openai/gpt-3.5-turbo","anthropic/claude-3-opus"]
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
MAX_RETRIES=3
RETRY_DELAY_BASE=1.0
ACCESS_TOKEN_EXPIRE_MINUTES=60
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
ENABLE_DETAILED_LOGGING=true
TRUSTED_IPS=["127.0.0.1","::1"]

# CORS Configuration
CORS_ALLOW_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

## 🚀 Running the Application

### Development Mode
```bash
# Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use the main module
python app/main.py
```

### Production Mode
```bash
uvicorn uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t sample-openrouter-backend .
docker run -p 8080:8080 --env-file .env sample-openrouter-backend
```

## 🔑 Authentication

### Generate Access Token
Use the provided script to generate access tokens:

```bash
# Windows
python scripts\generate_token.py --user-id your_user_id

# Generate token valid for 7 days
python scripts\generate_token.py --user-id your_user_id --days 7

# Generate token valid for 12 hours
python scripts\generate_token.py --user-id your_user_id --hours 12
```

### Using the Token
Include the token in your API requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt_text": "Hello, how are you?"}' \
     http://localhost:8080/ask-llm
```

## 📡 API Usage

### Main Endpoint: `/ask-llm`

#### Using Stored Prompt Templates
```json
{
  "prompt_name": "company_analysis",
  "data": {
    "company_name": "TechCorp",
    "industry": "Software",
    "additional_context": "Focus on AI capabilities"
  }
}
```

#### Using Direct Prompt Text
```json
{
  "prompt_text": "Analyze this company: {company_name} in {industry}",
  "data": {
    "company_name": "TechCorp",
    "industry": "Software"
  }
}
```

#### Specifying Model
```json
{
  "prompt_text": "What is the capital of France?",
  "model": "openai/gpt-4"
}
```

### Available Endpoints

- `POST /ask-llm` - Main LLM interaction endpoint
- `POST /auth/token` - Generate access token
- `GET /prompts` - List available prompt templates
- `GET /models` - List available OpenRouter models
- `GET /health` - Health check
- `GET /` - Service information
- `GET /docs` - Interactive API documentation (Swagger UI)

### Available Prompt Templates

- `company_analysis` - Analyze company market position and opportunities
- `text_summary` - Provide comprehensive text summaries
- `code_review` - Review code for quality and security
- `general_question` - Answer general questions

## 🚀 Deployment

### Google Cloud Platform

1. **Update the deployment script**:
   Edit `deploy_gcp.sh` and set your `PROJECT_ID`

2. **Run the deployment**:
   ```bash
   chmod +x deploy_gcp.sh
   ./deploy_gcp.sh
   ```

3. **Set environment variables** in Cloud Run:
   - `OPENROUTER_API_KEY`
   - `SECRET_KEY`
   - `OPENROUTER_MODELS`

### Manual Deployment

1. **Build Docker image**:
   ```bash
   docker build -t sample-openrouter-backend .
   ```

2. **Push to registry**:
   ```bash
   docker tag sample-openrouter-backend gcr.io/PROJECT_ID/sample-openrouter-backend
   docker push gcr.io/PROJECT_ID/sample-openrouter-backend
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy sample-openrouter-backend \
     --image gcr.io/PROJECT_ID/sample-openrouter-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🔧 Configuration

### Rate Limiting
- Default: 10 requests per minute per IP
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- Trusted IPs can bypass rate limiting

### Retry Logic
- Automatic retry on HTTP 429 (rate limit) errors
- Exponential backoff with configurable base delay
- Maximum retry attempts configurable via `MAX_RETRIES`

### Models
- Configurable list of OpenRouter models
- Automatic fallback to first configured model if none specified
- Model validation before API calls

### Logging Configuration
- **Log Level**: Configurable via `LOG_LEVEL` environment variable
- **Detailed Logging**: Enable/disable detailed request/response logging via `ENABLE_DETAILED_LOGGING`
- **Request ID Headers**: Supports `X-Request-ID` and `X-Cloud-Trace-Context` headers
- **Sensitive Headers**: Automatically obfuscates authorization and recaptcha headers
- **Header Logging**: Logs content-type, user-agent, accept, x-forwarded-for, host, and referer headers

### CORS Configuration
- **Allowed Origins**: Configurable via `CORS_ALLOW_ORIGINS` (default: `["*"]` for all origins)
- **Credentials**: Configurable via `CORS_ALLOW_CREDENTIALS` (default: `true`)
- **Methods**: Configurable via `CORS_ALLOW_METHODS` (default: `["*"]` for all methods)
- **Headers**: Configurable via `CORS_ALLOW_HEADERS` (default: `["*"]` for all headers)

## 📊 Monitoring & Logging

### Comprehensive Logging Middleware
The application includes a custom HTTP logging middleware that provides:

- **Request/Response Logging**: All inbound requests and returned data are logged independently of endpoint implementation
- **Request ID Tracking**: Automatically extracts existing `x-request-id` headers or generates new ones for distributed tracing
- **Header Logging**: Logs relevant headers with sensitive information obfuscation (e.g., authorization tokens)
- **Client IP Detection**: Extracts client IP from various proxy headers
- **Binary Data Handling**: Properly handles multipart/form-data and binary content
- **Error Logging**: Comprehensive error logging with request context

### Additional Features
- **Structured Logging**: All requests logged with unique IDs
- **Token Usage Tracking**: Monitor API consumption
- **Request Tracing**: Unique request ID for each API call
- **Health Checks**: Built-in health monitoring endpoint
- **Sensitive Header Obfuscation**: Protects sensitive information like authorization tokens

## 🔒 Security Features

- **JWT Authentication**: Secure access token system
- **Input Validation**: Pydantic-based request validation
- **Rate Limiting**: Protection against abuse
- **Error Sanitization**: No internal details exposed to clients
- **CORS Support**: Configurable cross-origin requests

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8080/health
```

### Test with Stored Prompt
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt_name": "general_question", "data": {"question": "What is 2+2?"}}' \
     http://localhost:8080/ask-llm
```

## 📁 Project Structure

```
sample-openrouter-backend/
├── app/                    # Application code
│   ├── __init__.py
│   ├── api.py             # FastAPI application and endpoints
│   ├── auth.py            # Authentication and JWT handling
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exception classes
│   ├── logging_middleware.py # Helper functions for logging
│   ├── main.py            # Application entry point
│   ├── models.py          # Pydantic models
│   ├── openrouter_client.py # OpenRouter API client
│   ├── prompts.py         # Prompt management system
│   ├── rate_limiter.py    # Rate limiting implementation
│   └── services.py        # Business logic services
├── scripts/
│   ├── generate_token.py  # Token generation utility
│   ├── setup.bat          # Windows setup script
│   └── setup.ps1          # PowerShell setup script
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── deploy_gcp.sh         # GCP deployment script
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
├── project.prd            # Project requirements document
├── QUICKSTART.md          # Quick start guide
└── README.md             # This file
```

### Key Components

- **`app/logging_middleware.py`**: Helper functions for request ID extraction and header obfuscation
- **`app/api.py`**: Main FastAPI application with all endpoints and middleware configuration
- **`app/services.py`**: Business logic layer for LLM interactions
- **`app/openrouter_client.py`**: Client for OpenRouter API integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Open an issue in the repository

## 🔄 Updates

- **v1.0.0**: Initial release with core functionality
- Support for OpenRouter integration
- Rate limiting and authentication
- Comprehensive request/response logging middleware
- Request ID tracking and distributed tracing support
- Docker and GCP deployment support
