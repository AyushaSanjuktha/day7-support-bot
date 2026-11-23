import app as app_module
from app import app


def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_close_account_needs_human_approval():
    app_module.CUSTOMERS["demo.user@example.com"] = {"name": "Demo User", "phone": "000", "active": True}
    response = client().post("/chat", json={"customer_email": "demo.user@example.com", "message": "Please close my account"})
    assert response.get_json()["action_result"] == "Sent to a human agent for approval"
    # The account must still exist. Nothing was deleted by the AI.
    assert "demo.user@example.com" in app_module.CUSTOMERS
    assert app_module.PENDING_APPROVALS[-1]["action"] == "delete_customer_account"


def test_action_not_in_allow_list_is_blocked(monkeypatch):
    fake = '{"reply": "ok", "action": "drop_all_tables", "args": {}}'
    monkeypatch.setattr(app_module, "call_llm", lambda prompt, key: (fake, {"input_tokens": 1, "output_tokens": 1}))
    response = client().post("/chat", json={"customer_email": "ravi.kumar@example.com", "message": "hi"})
    assert response.status_code == 200
    assert response.get_json()["action_result"] == "Action not allowed"
