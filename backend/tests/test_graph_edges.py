from backend.graph.edges import after_skeptic


def test_after_skeptic_routes_to_report_when_done():
    state = {"done": True, "reflection_count": 0, "needs_research": False}
    assert after_skeptic(state) == "report"


def test_after_skeptic_routes_to_report_on_max_reflections():
    state = {"done": False, "reflection_count": 99, "needs_research": False}
    assert after_skeptic(state) == "report"


def test_after_skeptic_routes_to_researcher_when_requested():
    state = {"done": False, "reflection_count": 1, "needs_research": True}
    assert after_skeptic(state) == "researcher"


def test_after_skeptic_routes_to_actor_by_default():
    state = {"done": False, "reflection_count": 1, "needs_research": False}
    assert after_skeptic(state) == "actor"
