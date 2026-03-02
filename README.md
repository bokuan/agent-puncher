# Agent Puncher

Agent Puncher is a powerful LLM gateway tool designed to capture, process, and log LLM API requests, providing complete request forwarding, logging, and web interface functionality. Through Agent Puncher, users can view the agent's interaction process in real-time, enabling a deeper understanding of how agents work.

## Features

- 🚀 **Request Forwarding**：Forward requests to external LLM APIs (such as OpenAI, Anthropic, etc.)
- 📊 **Detailed Logging**：Record all requests and responses, including prompts, response content, token usage, etc.
- 🔄 **Streaming Response**：Support streaming response processing, returning generated results in real-time
- 🖥️ **Web Interface**：Built-in simple web interface for easy viewing and management
- ⚙️ **Configuration Management**：Support managing LLM API settings through API or configuration files
- 📱 **CORS Support**：Built-in CORS middleware to support cross-domain requests

## Technology Stack

- **Backend**：Python 3.10+, FastAPI
- **Database**：SQLite
- **Frontend**：HTML, CSS, JavaScript
- **Dependencies**：aiohttp, uvicorn

## Installation and Usage

### 1. Clone the project

```bash
git clone git@github.com:bokuan/agent-puncher.git
cd agent-puncher
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API settings

You can configure LLM API information in two ways：

#### Method 1: Edit configuration file

Edit the `config.json` file to set your LLM API information：

```json
{
  "external_api_base_url": "https://api.openai.com/v1",
  "external_api_key": "your-api-key-here",
  "web_model": "gpt-3.5-turbo"
}
```

#### Method 2: Set through Web interface

Set API information directly on the web page, including API base URL, API key, and default model.

### 4. Start the service

```bash
python main.py
```

The service will start at `http://127.0.0.1:5685`.

## Project Structure

```
agent-puncher/
├── web/           # Frontend code
│   ├── app.js          # Frontend application logic
│   ├── index.html      # Frontend interface
│   └── style.css       # Frontend styles
├── __pycache__/        # Python compilation cache
├── .env                # Environment variables file
├── .gitignore          # Git ignore file
├── config.json         # Configuration file
├── config.py           # Configuration management module
├── database.py         # Database operation module
├── llm_gateway.db      # SQLite database file
├── main.py             # Main application entry
├── README.md           # English documentation
├── README_zh-CN.md     # Chinese documentation
└── requirements.txt    # Dependency file
```

## API Calls

- **POST http://127.0.0.1:5685/v1/chat/completions**
  - OpenAI API-compatible chat completion endpoint
  - Supports both streaming and non-streaming responses
  - Automatically records all requests and responses, including request and response metadata

## Web Interface

Visit `http://127.0.0.1:5685/web/` to view the built-in web interface, which can be used for：
- Sending chat requests
- Viewing history
- Managing configuration

## Logging

The system records the following information：
- Timestamp
- Prompt content
- Response content
- Token usage
- External API URL
- Request headers
- Request body

Logs are stored in the SQLite database `llm_gateway.db`.

## Notes

1. Please keep your API key secure and do not commit it to version control
2. The project uses SQLite database by default, suitable for development and small-scale use
3. For production environments, it is recommended to use a more powerful database system
4. To modify the port or host, please edit the `uvicorn.run` configuration in the `main.py` file

## Contribution

Welcome to submit issues and Pull Requests！

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
