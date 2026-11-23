import logging

from app import app


def test_ai_call_writes_one_clean_log_line(caplog):
    app.config["TESTING"] = True
    with caplog.at_level(logging.INFO):
        app.test_client().post(
            "/chat",
            json={"customer_email": "ravi.kumar@example.com", "message": "Where is my order 10231?"},
        )
    text = " ".join(record.getMessage() for record in caplog.records)
    for field in ["request_id=", "model=", "latency_ms=", "input_tokens=", "output_tokens=", "cost_inr="]:
        assert field in text
    # No personal data in the log
    assert "ravi.kumar@example.com" not in text
    assert "98480" not in text
    assert "Ravi Kumar" not in text
