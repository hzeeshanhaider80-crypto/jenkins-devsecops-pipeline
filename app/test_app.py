import app as app_module


def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health():
    res = client().get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_home_shows_visits(monkeypatch):
    monkeypatch.setattr(app_module, "get_visits", lambda: 42)
    res = client().get("/")
    assert res.status_code == 200
    assert b"42" in res.data


def test_home_without_redis(monkeypatch):
    monkeypatch.setattr(app_module, "get_visits", lambda: None)
    res = client().get("/")
    assert b"Redis unavailable" in res.data
