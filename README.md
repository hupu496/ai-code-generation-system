# AI Code Generation System - LangGraph Edition

An AI-powered automated software development system using **LangGraph** and **Gemini** models to convert project descriptions into complete, tested, and GitHub-hosted software projects.

## Architecture

```
User Input → Project Flow Config → LangGraph Workflow → AI Providers (Gemini, Groq, etc.) → Generated Code → Tests → GitHub
```

### Key Components

1. **LangGraph Workflow** - Orchestrates the entire code generation pipeline
2. **Gemini AI Provider** - Primary model (gemini-2.0-flash-exp) via Google AI Studio
3. **Multi-Provider Routing** - Specialist routing for different task types
4. **Module-Based Execution** - Topological sort with dependency management
5. **Integrated Testing** - Unit and integration tests per module

## Prerequisites

- Python 3.11+
- Virtual environment (venv)
- API Keys for AI providers

## Quick Start

### 1. Setup Virtual Environment

```powershell
# Create and activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```powershell
# Copy example env file
copy .env.example .env

# Edit .env with your API keys (at minimum GEMINI_API_KEY or GROQ_API_KEY)
notepad .env
```

**Required API Keys:**
- **GEMINI_API_KEY** - Get from [Google AI Studio](https://aistudio.google.com/app/apikey) (primary)
- **GROQ_API_KEY** - Get from [Groq Console](https://console.groq.com/keys) (fallback, free tier)

**Optional API Keys:**
- `GITHUB_TOKEN` - GitHub Models (free)
- `OPENAI_API_KEY` - OpenAI direct
- `DEEPSEEK_API_KEY` - DeepSeek API
- `NVIDIA_API_KEY` - NVIDIA NIM
- `TOGETHER_API_KEY` - Together AI
- `HUGGINGFACE_API_KEY` - HuggingFace Inference

### 3. Run Tests

```powershell
# Run system tests
python test_system.py
```

### 4. Execute Project Generation

```powershell
# Run the LangGraph workflow
python main_langgraph.py
```

## Project Structure

```
ai-code-generation-system/
├── main_langgraph.py          # Main entry point (LangGraph)
├── main.py                    # Original executor (legacy)
├── test_system.py             # System tests
├── langgraph_state.py         # LangGraph state schema
├── langgraph_nodes.py         # LangGraph workflow nodes
├── ai_providers.py            # AI provider management
├── project_flow.json          # Project module definitions
├── ai-router.json             # AI provider routing config
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── inspect_db.py              # Database inspection utilities
├── inspect_db2.py             # Database inspection utilities
├── import_leads.py            # Lead import utility
└── README.md                  # This file
```

## Configuration

### project_flow.json
Defines the project modules, dependencies, and execution order:
- 8 modules: database_setup, models, gmail_responder, remote_installer, api_routes, frontend_ui, main_app, integration_testing
- Each module specifies files to generate and tests to run
- Task types route to specialist AI providers

### ai-router.json
Configures the AI provider chain and specialist routing:
- Primary: Groq (llama-3.3-70b-versatile) - free, no rate limits
- Specialists: DeepSeek (frontend), Gemini (design), Nemotron (reasoning), etc.
- Fallback chain with automatic retry

## LangGraph Workflow

The workflow executes as a state machine:

```
load_config → topological_sort → route_provider → execute_module → run_tests
                                                    ↓
                                            [continue] → next_module → route_provider
                                                    ↓
                                            [integration_tests] → integration_tests → push_github → generate_summary
                                                    ↓
                                            [failed] → generate_summary
```

### State Schema
- `modules` - List of module specifications with status
- `ai_providers` - Available AI providers with health status
- `specialist_routing` - Task-type to provider mapping
- `completed_modules` / `failed_modules` - Tracking
- `execution_summary` - Final results

## AI Provider Routing

| Task Type | Specialist Provider | Model |
|-----------|-------------------|-------|
| frontend_finishing | deepseek | deepseek-chat |
| photo_design / poster_design | gemini | gemini-2.0-flash-exp |
| heavy_reasoning | nemotron-3-ultra | nvidia/nemotron-3-ultra |
| fast_inference | nemotron-3.5-lightning | nvidia/nemotron-3.5-lightning |
| creative_coding | big-pickle | bigpickle/bigpickle |
| general_coding | muse-spark-1.3 | muse/muse-spark-1.3 |
| fintech_coding | ling-3.0-flash-fin | ling/ling-3.0-flash-fin |
| default/fallback | opencode (Groq) | llama-3.3-70b-versatile |

## Output

Generated code is saved to the configured output directory (`D:\ComsysProject\output\LocalLeadsProject\` by default):

```
output/
└── LocalLeadsProject/
    ├── leads.db
    ├── map_project_db.json
    ├── models/
    │   ├── __init__.py
    │   ├── lead.py
    │   ├── contact.py
    │   └── interaction.py
    ├── gmail_responder.py
    ├── gmail_auth.py
    ├── email_templates.py
    ├── remote_installer.py
    ├── deployment_config.py
    ├── api/
    │   ├── __init__.py
    │   └── routes/
    │       ├── leads.py
    │       ├── contacts.py
    │       ├── interactions.py
    │       └── email.py
    ├── templates/
    │   ├── index.html
    │   ├── dashboard.html
    │   ├── leads_list.html
    │   └── email_composer.html
    ├── static/
    │   ├── css/style.css
    │   └── js/
    │       ├── app.js
    │       ├── leads.js
    │       └── email.js
    ├── app.py
    ├── config.py
    ├── extensions.py
    └── tests/
        └── integration/
            ├── test_full_flow.py
            ├── test_email_flow.py
            └── test_api_flow.py
```

## Commands Reference

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configuration
copy .env.example .env
notepad .env

# Testing
python test_system.py

# Execution
python main_langgraph.py

# Legacy execution (original)
python main.py

# Database utilities
python inspect_db.py
python inspect_db2.py
python import_leads.py

# Code quality
black .
flake8 .
isort .
```

## Google AI Studio Integration

The system uses **Gemini 2.0 Flash Experimental** via Google AI Studio:
- Free tier available
- High-quality code generation
- Supports long contexts (1M tokens)
- Fast inference

Get your API key: https://aistudio.google.com/app/apikey

## Canvas Integration

For visual workflow design, the LangGraph workflow can be exported to **LangGraph Studio** or visualized via:
- LangGraph Studio (local): `langgraph dev`
- LangGraph Cloud: Deploy to LangGraph Platform

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Run `pip install -r requirements.txt`
2. **API Key Errors**: Check `.env` file has valid keys
3. **Rate Limits**: System auto-retries with fallback providers
4. **Permission Errors**: Run PowerShell as Administrator for venv creation

### Logs

Check execution logs in console output. Summary saved to:
`D:\ComsysProject\output\execution_summary.json`

## License

MIT License - Feel free to use and modify.

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit PR with tests