---
title: alter_ego
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.46.0
app_file: app.py
pinned: false
license: mit
python_version: 3.12
---
# Alter Ego - Personal AI Assistant Chatbot

A modular, professional AI chatbot application that represents Aayush Vijayvergiya and can answer questions about his background, skills, and experience.

## Features

- **Modular Architecture**: Well-organized codebase following Python best practices
- **OpenAI Integration**: Uses GPT-4o-mini for intelligent conversations
- **Function Calling**: Records user interest and unknown questions via OpenAI tools
- **Notification System**: Pushover integration for real-time alerts
- **Document Processing**: Automatic PDF and text processing for context
- **Web Interface**: Gradio-based chat interface
- **Type Safety**: Full type hints throughout the codebase
- **Testing**: Comprehensive test suite with pytest

## Project Structure

```
alter_ego_01/
├── src/alter_ego/           # Main application package
│   ├── __init__.py          # Package initialization
│   ├── app.py               # Main application class
│   ├── config.py            # Configuration management
│   ├── tools.py             # OpenAI tool definitions
│   ├── models/              # Data models
│   │   └── __init__.py      # Model definitions
│   ├── services/            # Business logic services
│   │   ├── __init__.py      # Services initialization
│   │   ├── chat_service.py  # Chat handling
│   │   ├── document_service.py # Document processing
│   │   ├── notification_service.py # Notifications
│   │   └── tool_handler.py  # OpenAI tool execution
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   └── test_alter_ego.py    # Application tests
├── static/                  # Static files
│   ├── AayushVijayvergiya_LinkedIn.pdf
│   └── summary.txt
├── main.py                  # Entry point
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd alter_ego_01
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PUSHOVER_USER=your_pushover_user_key  # Optional
   PUSHOVER_TOKEN=your_pushover_token    # Optional
   ```

4. **Add your documents**:
   - Place LinkedIn PDF in `static/`
   - Add summary text in `static/summary.txt`

## Usage

### Run the application:
```bash
# Using uv
uv run python main.py

# Or direct execution
python main.py
```

### Run tests:
```bash
# Install dev dependencies first
uv add --dev pytest pytest-cov

# Run tests
uv run pytest tests/
```

### Development tools:
```bash
# Code formatting
uv add --dev black isort
uv run black src/ tests/
uv run isort src/ tests/

# Type checking
uv add --dev mypy
uv run mypy src/
```

## Configuration

The application uses environment variables for configuration:

- `OPENAI_API_KEY`: Required - Your OpenAI API key
- `PUSHOVER_USER`: Optional - Pushover user key for notifications
- `PUSHOVER_TOKEN`: Optional - Pushover token for notifications

## Architecture

### Services Layer
- **ChatService**: Handles OpenAI conversations and tool calling
- **DocumentService**: Processes PDF and text documents for context
- **NotificationService**: Manages Pushover notifications
- **ToolHandler**: Executes OpenAI function calls

### Models
- Type-safe data models using dataclasses
- Clear separation of concerns
- Easy to extend and maintain

### Configuration
- Centralized configuration management
- Environment variable validation
- Path resolution for static files

## License

This project is licensed under the MIT License.
