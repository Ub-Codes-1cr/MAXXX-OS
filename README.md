# MAXXX OS

**Local-First AI Orchestration Agent for Social Media Management**

MAXXX OS is a privacy-focused, anti-API alternative to social media management tools. It uses local LLMs (Ollama + Hermes/Qwen) and Playwright browser automation to post to 20+ platforms without cloud dependencies.

## Features

- **Zero Cloud APIs** - All processing happens locally
- **20 Platform Support** - X, LinkedIn, GitHub, Reddit, Instagram, YouTube, and more
- **Local LLM Intelligence** - Hermes 3 for autonomous decision-making
- **Browser Automation** - Uses your real Chrome profile (no re-login needed)
- **Golden Lint Rules** - 40 rules across 20 platforms for optimal posting
- **Voice Input** - Speak your content ideas
- **Analytics** - Track post performance
- **Scheduling** - Queue posts for optimal timing

## Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)
3. **Chrome Browser** - With logged-in social accounts

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/maxxx-os.git
cd maxxx-os

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Pull Ollama models
ollama pull hermes3:8b
ollama pull qwen2.5:7b

# Start Ollama (if not running)
ollama serve
```

### Running

```bash
# Start the UI
python -m streamlit run main.py

# Or use the orchestrator directly
python orchestrator.py "Your content idea" x
```

## Architecture

```
maxxx-os/
├── brain.py              # AI orchestration (Hermes agent)
├── agent.py              # ReAct agent loop
├── tools.py              # Tool definitions for agent
├── orchestrator.py       # High-level task management
├── draft_generator.py    # Content generation pipeline
├── golden_lint.py        # 40-rule validation system
├── playwright_engine.py  # Browser automation
├── ollama_client.py      # Local LLM integration
├── vault_reader.py       # Obsidian vault reader
├── voice_pipeline.py     # Speech-to-text
├── memory.py             # Conversation memory
├── analytics.py          # Performance tracking
├── scheduler.py          # Post scheduling
├── media_handler.py      # Image/media processing
├── retry_handler.py      # Error recovery
├── config.py             # Configuration management
├── logger.py             # Logging system
├── main.py               # Streamlit UI
└── vault/                # Platform rules & brand voice
    ├── 00-Core/
    └── 10-Platforms/
```

## Team Collaboration

### Branch Strategy

- `main` - Stable, tested code
- `dev` - Integration branch
- Feature branches: `feature/frontend`, `feature/llm`, `feature/browser`, `feature/analytics`

### Pull Request Process

1. Create feature branch from `dev`
2. Make changes
3. Test locally
4. Submit PR to `dev`
5. Review and merge

## Platform Support

| Platform | Status | Auto-Post |
|----------|--------|-----------|
| X (Twitter) | ✅ | Staged |
| LinkedIn | ✅ | Staged |
| GitHub | ✅ | Staged |
| Reddit | ✅ | Staged |
| Dev.to | ✅ | Staged |
| Instagram | ✅ | Staged |
| YouTube | ✅ | Staged |
| Threads | ✅ | Staged |
| Facebook | ✅ | Staged |
| + 11 more | ✅ | Staged |

## License

MIT

## Acknowledgments

- Built for hackathon submission
- Powered by Ollama, Playwright, and Streamlit
