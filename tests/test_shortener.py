import pytest

from shortener import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app({"DB_PATH": str(tmp_path / "test.db"), "APP_VERSION": "test-sha", "TESTING": True})
    return app.test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_version(client):
    assert client.get("/version").get_json() == {"version": "test-sha"}


def test_shorten_redirect_and_stats(client):
    res = client.post("/api/shorten", json={"url": "https://example.com/some/long/path"})
    assert res.status_code == 201
    code = res.get_json()["code"]
    assert len(code) == 6

    redirect = client.get(f"/{code}")
    assert redirect.status_code == 302
    assert redirect.headers["Location"] == "https://example.com/some/long/path"

    stats = client.get(f"/api/links/{code}").get_json()
    assert stats["clicks"] == 1


@pytest.mark.parametrize("bad", ["", "not a url", "javascript:alert(1)", "ftp://example.com"])
def test_rejects_bad_urls(client, bad):
    assert client.post("/api/shorten", json={"url": bad}).status_code == 400


def test_rejects_non_json_body(client):
    assert client.post("/api/shorten", data="url=https://example.com").status_code == 400


def test_rejects_self_link(client):
    assert client.post("/api/shorten", json={"url": "http://localhost/abc123"}).status_code == 400


def test_unknown_code_is_404(client):
    assert client.get("/abcdef").status_code == 404
    assert client.get("/nope").status_code == 404
