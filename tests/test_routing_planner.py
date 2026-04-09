import app


def _reset_state():
    for key in list(app.st.session_state.keys()):
        del app.st.session_state[key]
    app.init_state()


class _DummyResponse:
    def __init__(self, content: str):
        self.content = content


class _PlannerLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, _messages):
        return _DummyResponse(self._content)


def test_plan_user_route_parses_direct_answer(monkeypatch):
    _reset_state()
    monkeypatch.setattr(
        app,
        "get_llm",
        lambda temperature=0: _PlannerLLM(
            '{"route":"direct_answer","reply":"Hello there","reason":"smalltalk"}'
        ),
    )
    route = app.plan_user_route("hi", [])
    assert route["route"] == "direct_answer"
    assert route["reply"] == "Hello there"


def test_run_graph_uses_tool_research_route(monkeypatch):
    _reset_state()
    monkeypatch.setattr(
        app,
        "plan_user_route",
        lambda message, prior: {"route": "tool_research", "reply": "", "reason": "factual"},
    )
    monkeypatch.setattr(
        app,
        "run_toolcalling_research",
        lambda query: ("Found current facts with sources.", [{"title": "A", "url": "https://x", "snippet": "y"}]),
    )
    app.run_graph("latest measles deaths")
    assistant_msgs = [m for m in app.st.session_state.messages if m.get("role") == "assistant"]
    assert any("Found current facts" in m.get("content", "") for m in assistant_msgs)
    assert any("I searched the web and found" in m.get("content", "") for m in assistant_msgs)


def test_run_graph_direct_answer_route_skips_graph(monkeypatch):
    _reset_state()
    monkeypatch.setattr(
        app,
        "plan_user_route",
        lambda message, prior: {"route": "direct_answer", "reply": "Direct reply", "reason": "smalltalk"},
    )
    monkeypatch.setattr(app, "get_graph", lambda: (_ for _ in ()).throw(RuntimeError("graph should not run")))
    app.run_graph("hello there")
    assistant_msgs = [m for m in app.st.session_state.messages if m.get("role") == "assistant"]
    assert any(m.get("content") == "Direct reply" for m in assistant_msgs)
