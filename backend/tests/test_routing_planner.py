from backend.app.services import orchestrator


class _DummyResponse:
    def __init__(self, content: str):
        self.content = content


class _PlannerLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, _messages):
        return _DummyResponse(self._content)


def test_plan_user_route_parses_direct_answer(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "get_llm",
        lambda temperature=0: _PlannerLLM(
            '{"route":"direct_answer","reply":"Hello there","reason":"smalltalk"}'
        ),
    )
    route = orchestrator.plan_user_route("hi", [])
    assert route["route"] == "direct_answer"
    assert route["reply"] == "Hello there"


def test_plan_user_route_falls_back_on_invalid_json(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "get_llm",
        lambda temperature=0: _PlannerLLM("not-json"),
    )
    route = orchestrator.plan_user_route("what is flu", ["earlier question"])
    assert route["route"] == "diagnostic_flow"
    assert route["reason"] == "fallback"


def test_plan_user_route_forces_tool_research_for_explicit_command(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "get_llm",
        lambda temperature=0: _PlannerLLM('{"route":"direct_answer","reply":"No tools","reason":"bad route"}'),
    )
    route = orchestrator.plan_user_route("do tavily search to give me the exact date", [])
    assert route["route"] == "tool_research"
    assert "research_command" in route["reason"]
