from unittest.mock import Mock
from test_learning import account


def test_provider_failure_is_visible_without_disclosing_accounts(client, monkeypatch):
    account(client, "mailtest", "student")
    monkeypatch.setattr("app.services.mailer.configured", lambda: True)
    monkeypatch.setattr("app.services.mailer.check_available", Mock(side_effect=RuntimeError("private provider data")))
    send = Mock()
    monkeypatch.setattr("app.services.mailer.send_email", send)
    first = client.post("/api/auth/forgot-password", json={"email": "mailtest@example.com"})
    other = client.post("/api/auth/forgot-password", json={"email": "unknown@example.com"})
    assert first.status_code == other.status_code == 503
    assert first.json() == other.json()
    assert "private provider data" not in first.text
    assert "Письмо не отправлено" in first.json()["detail"]
    send.assert_not_called()
