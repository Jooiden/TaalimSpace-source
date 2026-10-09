from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.services.frontend import mount_frontend


def test_single_origin_frontend_never_masks_api_or_serves_secrets(tmp_path):
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text("<html>EduSpace</html>")
    (root / "app.js").write_text("console.log('EduSpace')")
    (root / ".env").write_text("private")
    app = FastAPI()
    @app.get("/api/health")
    def health():
        return {"status": "ok"}
    mount_frontend(app, root)
    with TestClient(app) as client:
        assert client.get("/student/lessons").text == "<html>EduSpace</html>"
        assert client.get("/app.js").status_code == 200
        assert client.get("/api/health").json() == {"status": "ok"}
        for path in ["/api/missing", "/.env", "/missing.js", "/assets/missing"]:
            assert client.get(path).status_code == 404
