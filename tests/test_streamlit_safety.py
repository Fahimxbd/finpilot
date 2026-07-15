from pathlib import Path


def test_public_app_has_cost_and_execution_safety_boundaries() -> None:
    source = Path("streamlit_app.py").read_text(encoding="utf-8")
    assert 'FINPILOT_ENABLE_LLM"] = "false"' in source
    assert "MAX_LIVE_CALLS_PER_SESSION = 10" in source
    assert "MAX_UPLOAD_BYTES = 8 * 1024 * 1024" in source
    assert "use_llm=False" in source
    forbidden = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "place_order(", "submit_order(")
    assert not any(token in source for token in forbidden)
