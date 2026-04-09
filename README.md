MyAIDoctor — Multi-Agent Medical Diagnostic System

This project is a demo multi-agent diagnostic assistant built with a LangGraph workflow and Streamlit UI.

Running in demo mode (no API keys required):

- Set LOCAL_DEMO=1 in your environment (or create a .env file with LOCAL_DEMO=1)
- Install dependencies from requirements.txt
- Run streamlit:

```bash
# In WSL/bash (from project root)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LOCAL_DEMO=1
streamlit run app.py
```

The demo mode uses a MockLLM that returns deterministic, structured responses so you can exercise the full UI and LangGraph flow without external API keys.
