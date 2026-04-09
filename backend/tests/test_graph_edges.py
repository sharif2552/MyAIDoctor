from backend.graph.edges import after_intake, after_researcher, after_skeptic


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


def test_after_intake_routes_to_researcher_when_medication_flag():
    state = {"needs_initial_medication_research": True}
    assert after_intake(state) == "researcher"


def test_after_intake_routes_to_actor_otherwise():
    state = {"needs_initial_medication_research": False}
    assert after_intake(state) == "actor"


def test_after_researcher_routes_to_actor_when_flagged():
    state = {"post_research_route": "actor"}
    assert after_researcher(state) == "actor"


def test_after_researcher_routes_to_skeptic_by_default():
    state = {"post_research_route": "skeptic"}
    assert after_researcher(state) == "skeptic"


def test_after_researcher_defaults_to_skeptic():
    state = {"post_research_route": ""}
    assert after_researcher(state) == "skeptic"
