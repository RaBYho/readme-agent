# README Generator Agent

A CLI tool that automatically generates high-quality README.md files for local projects by analyzing their structure and strategic files, then leveraging OpenRouter's LLM models.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Features

- Automatically scans project directories to build a comprehensive context
- Detects and analyzes strategic files (requirements.txt, package.json, Dockerfile, etc.)
- Extracts relevant source code samples to provide concrete feature descriptions
- Identifies project licenses when present
- Generates appropriate technology badges based on detected files
- Supports multiple output languages for the generated README
- Dry-run mode for debugging and context inspection
- Configurable LLM model selection via OpenRouter

## Prerequisites

- Python 3.x
- OpenRouter API key (free account available at [openrouter.ai](https://openrouter.ai))

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/readme-agent.git
cd readme-agent
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Alternatively, you can set the environment variable directly in your shell:
```bash
export OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Usage

Basic usage:
```bash
python main.py /path/to/your/project
```

Advanced options:
```bash
python main.py . --model "meta-llama/llama-3.1-70b-instruct" --lang "English" --output docs/README.md
```

Dry-run mode (shows extracted context without calling the LLM):
```bash
python main.py . --dry-run
```

## Project Structure

```
readme-agent/
├── .env
├── .env.example
├── .gitignore
├── badges.py
├── config.py
├── llm_client.py
├── main.py
├── parser.py
├── prompts.py
└── requirements.txt
```

- `main.py`: CLI entry point
- `parser.py`: Project scanning and context extraction
- `llm_client.py`: OpenRouter API client
- `prompts.py`: README generation templates
- `badges.py`: Technology badge generation
- `config.py`: Centralized configuration

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.