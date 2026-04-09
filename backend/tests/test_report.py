from backend.utils.report import build_report


def test_build_report_minimal():
    symptoms = "Right-sided headache for 3 days, photophobia, nausea"
    differential = [
        {"condition": "Migraine", "confidence": 70, "supporting_evidence": ["photophobia"], "against": [], "icd_hint": "G43.9"},
        {"condition": "Tension-type headache", "confidence": 20, "supporting_evidence": [], "against": [], "icd_hint": "G44.2"},
    ]
    research_results = [
        {"title": "Migraine — Mayo Clinic", "url": "https://mayoclinic.org/article", "snippet": "Migraine symptoms include...", "full_content": "Migraine is a common cause of unilateral throbbing headache."}
    ]
    user_answers = ["No visual changes"]
    skeptic_critique = "Need to know if aura present"

    report = build_report(symptoms, differential, research_results, user_answers, skeptic_critique)

    assert "summary_of_findings" in report
    assert report["differential_diagnosis"][0]["condition"] == "Migraine"
    assert report["treatment_recommendations"] == []
    assert report["metadata"]["questions_asked"] == 1
    assert report["metadata"]["sources_reviewed"] == 1
