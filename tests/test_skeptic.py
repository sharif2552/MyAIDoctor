from agents import skeptic


class DummyResponse:
    def __init__(self, content):
        self.content = content


class DummyLLM:
    def __init__(self, content):
        self.content = content

    def invoke(self, _messages):
        return DummyResponse(self.content)


def test_run_skeptic_normalizes_shape(monkeypatch):
    monkeypatch.setattr(skeptic, "get_llm", lambda temperature=0.3: DummyLLM('{"critique":"ok"}'))
    out = skeptic.run_skeptic("symptoms", [], [], [])
    assert out["critique"] == "ok"
    assert out["needs_clarification"] is False
    assert out["needs_research"] is False
    assert out["resolved"] is False


def test_run_skeptic_handles_invalid_json(monkeypatch):
    monkeypatch.setattr(skeptic, "get_llm", lambda temperature=0.3: DummyLLM("not-json"))
    out = skeptic.run_skeptic("symptoms", [], [], [])
    assert out["critique"] == "not-json"
