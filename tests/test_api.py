from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["llm_provider"] == "mock"


def test_generate_endpoint_returns_bundle_and_serves_glb():
    payload = {
        "project_name": "API Test Tower",
        "space_type": "office",
        "description": "8 tầng, mỗi tầng 5 phòng, 150 người",
        "target_audience": "Khách thuê doanh nghiệp",
    }
    r = client.post("/api/generate", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["spec"]["floors"] == 8
    assert body["spec"]["rooms_per_floor"] == 5
    assert 3 <= len(body["describer"]["highlights"]) <= 5
    assert body["model"]["tri_count"] > 0

    glb = body["model"]["glb"]
    g = client.get(f"/artifacts/{glb}")
    assert g.status_code == 200
    assert len(g.content) > 0


def test_generate_validation_error():
    # missing required project_name -> 422
    r = client.post("/api/generate", json={"space_type": "office"})
    assert r.status_code == 422


def test_generate_rejects_blank_project_name():
    r = client.post(
        "/api/generate",
        json={
            "project_name": "   ",
            "space_type": "office",
            "description": "5 tầng, mỗi tầng 6 phòng",
        },
    )
    assert r.status_code == 422


def test_generate_rejects_blank_description():
    r = client.post(
        "/api/generate",
        json={
            "project_name": "Blank Description Tower",
            "space_type": "office",
            "description": "   ",
        },
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "description is required"
