import pytest

from backend.utils.llm import get_llm


def test_get_llm_returns_mock_in_local_demo(monkeypatch):
    monkeypatch.setenv("LOCAL_DEMO", "1")
    llm = get_llm()
    assert hasattr(llm, "invoke")


def test_get_llm_raises_without_provider(monkeypatch):
    monkeypatch.delenv("LOCAL_DEMO", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ALLOW_MOCK_FALLBACK", raising=False)
    with pytest.raises(RuntimeError):
        get_llm()


def test_mock_skeptic_output_shape(monkeypatch):
    monkeypatch.setenv("LOCAL_DEMO", "1")
    llm = get_llm()

    class Msg:
        def __init__(self, content):
            self.content = content

    class SystemMessage(Msg):
        pass

    class HumanMessage(Msg):
        pass

    response = llm.invoke(
        [
            SystemMessage("You are the Skeptical Specialist — a devil's advocate physician."),
            HumanMessage("Patient symptoms: hi"),
        ]
    )
    assert "critique" in response.content
