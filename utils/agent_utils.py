import json


class SystemMessage:
    def __init__(self, content: str):
        self.content = content


class HumanMessage:
    def __init__(self, content: str):
        self.content = content


def get_message_types():
    try:
        from langchain_core.messages import HumanMessage as LCHumanMessage
        from langchain_core.messages import SystemMessage as LCSystemMessage

        return LCSystemMessage, LCHumanMessage
    except Exception:
        return SystemMessage, HumanMessage


def strip_json_code_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def safe_json_loads(raw: str) -> dict:
    try:
        data = json.loads(strip_json_code_fence(raw))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
