from fastapi.testclient import TestClient

import backend.main as backend_main
from backend.main import app
from builder.schemas import IndustryTone, StopDescribe
from builder.tour import assemble_tour, generate_tour
from builder.vision_describer import describe_image
from builder.llm.factory import llm_from_runtime_key

client = TestClient(app)


def test_vision_describe_mock_by_industry():
    d = describe_image("", "image/png", IndustryTone.retail)
    assert isinstance(d, StopDescribe)
    assert 3 <= len(d.highlights) <= 5
    assert d.title and d.description


def test_assemble_tour_weaves_narration():
    d = describe_image("", "image/png", IndustryTone.real_estate)
    tour = assemble_tour("Sunrise Tower", IndustryTone.real_estate, [
        {"id": "s1", "image": "/a.jpg", "kind": "panorama", "describe": d},
        {"id": "s2", "image": "/b.jpg", "kind": "photo", "describe": d},
    ])
    assert tour.id.endswith("-tour")
    assert len(tour.stops) == 2
    assert tour.intro and tour.outro
    assert all(s.narration for s in tour.stops)


def test_generate_tour_uses_mock_llm_guide_voice():
    d = describe_image("", "image/png", IndustryTone.real_estate)
    tour = generate_tour("Sunrise Tower", IndustryTone.real_estate, [
        {"id": "s1", "image": "/a.jpg", "kind": "panorama", "describe": d},
    ])
    assert "hướng dẫn viên" in tour.intro.lower()
    assert "Điểm dừng 1" in tour.stops[0].narration


def test_api_describe_image_and_tour():
    r = client.post(
        "/api/describe-image",
        files={"file": ("v.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        data={"industry": "exhibition"},
    )
    assert r.status_code == 200, r.text
    desc = r.json()
    assert 3 <= len(desc["highlights"]) <= 5

    tr = client.post("/api/tour", json={
        "project_name": "Expo Center",
        "industry": "exhibition",
        "stops": [{"id": "s1", "image": "/x.jpg", "kind": "panorama", "describe": desc}],
    })
    assert tr.status_code == 200, tr.text
    t = tr.json()
    assert t["intro"] and t["stops"][0]["narration"]


def test_api_describe_image_url_rejects_non_http():
    r = client.post("/api/describe-image-url", json={
        "url": "file:///etc/passwd",
        "industry": "real_estate",
    })
    assert r.status_code == 400


def test_api_describe_image_rejects_empty_upload():
    r = client.post(
        "/api/describe-image",
        files={"file": ("empty.png", b"", "image/png")},
        data={"industry": "real_estate"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "image file is empty"


def test_api_tour_rejects_unknown_runtime_provider():
    d = describe_image("", "image/png", IndustryTone.real_estate)
    r = client.post("/api/tour", json={
        "project_name": "Runtime Provider Test",
        "industry": "real_estate",
        "llm_provider": "unknown",
        "llm_api_key": "sk-test",
        "stops": [{"id": "s1", "image": "/x.jpg", "kind": "photo", "describe": d.model_dump()}],
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "unsupported llm provider"


def test_api_llm_models_returns_default_without_key():
    r = client.post("/api/llm/models", json={"provider": "groq", "api_key": ""})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "groq"
    assert body["source"] == "default"
    assert "meta-llama/llama-4-scout-17b-16e-instruct" in body["models"]


def test_api_llm_models_rejects_unknown_provider():
    r = client.post("/api/llm/models", json={"provider": "unknown", "api_key": "sk-test"})
    assert r.status_code == 400
    assert r.json()["detail"] == "unsupported llm provider"


def test_api_llm_models_fetches_groq_models(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "data": [
                    {"id": "llama-3.3-70b-versatile"},
                    {"id": "whisper-large-v3"},
                    {"id": "custom-vision-model"},
                ]
            }

    def fake_get(url, timeout, headers):
        assert url == "https://api.groq.com/openai/v1/models"
        assert headers["authorization"] == "Bearer gsk-test"
        return FakeResponse()

    monkeypatch.setattr(backend_main.requests, "get", fake_get)
    r = client.post("/api/llm/models", json={"provider": "groq", "api_key": "gsk-test"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "provider"
    assert body["models"][0] == "meta-llama/llama-4-scout-17b-16e-instruct"
    assert "custom-vision-model" in body["models"]
    assert "whisper-large-v3" not in body["models"]


def test_api_tour_projects_returns_local_mode_when_supabase_missing(monkeypatch):
    monkeypatch.setattr(backend_main, "SUPABASE_URL", "")
    monkeypatch.setattr(backend_main, "SUPABASE_SERVICE_ROLE_KEY", "")

    r = client.get("/api/tour-projects")
    assert r.status_code == 200, r.text
    assert r.json() == {"configured": False, "projects": []}


def test_api_tour_projects_upserts_to_supabase(monkeypatch):
    project = {
        "id": "tour-1",
        "name": "Council Room Tour",
        "industry": "exhibition",
        "stops": [],
        "updatedAt": "2026-06-08T01:00:00.000Z",
    }

    class FakeResponse:
        status_code = 201

        def json(self):
            return [{"payload": project}]

    def fake_post(url, timeout, headers, json):
        assert url == "https://example.supabase.co/rest/v1/tour_projects?on_conflict=id"
        assert headers["apikey"] == "service-key"
        assert headers["authorization"] == "Bearer service-key"
        assert "resolution=merge-duplicates" in headers["prefer"]
        assert json == [{
            "id": "tour-1",
            "payload": project,
            "updated_at": "2026-06-08T01:00:00.000Z",
        }]
        return FakeResponse()

    monkeypatch.setattr(backend_main, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(backend_main, "SUPABASE_SERVICE_ROLE_KEY", "service-key")
    monkeypatch.setattr(backend_main.requests, "post", fake_post)

    r = client.put("/api/tour-projects/tour-1", json={"project": project})
    assert r.status_code == 200, r.text
    assert r.json() == {"configured": True, "project": project}


def test_api_tour_projects_allows_vercel_preflight_for_put():
    r = client.options(
        "/api/tour-projects/tour-1",
        headers={
            "origin": "https://3-d-building-builder.vercel.app",
            "access-control-request-method": "PUT",
            "access-control-request-headers": "content-type",
        },
    )
    assert r.status_code == 200, r.text
    assert r.headers["access-control-allow-origin"] == "https://3-d-building-builder.vercel.app"


def test_api_tour_asset_image_returns_unconfigured_without_storage(monkeypatch):
    monkeypatch.setattr(backend_main, "SUPABASE_URL", "")
    monkeypatch.setattr(backend_main, "SUPABASE_SERVICE_ROLE_KEY", "")

    r = client.post(
        "/api/tour-assets/image",
        files={"file": ("view.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["configured"] is False


def test_api_tour_asset_image_uploads_to_supabase_storage(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "{}"

    def fake_post(url, timeout, headers, data):
        assert url.startswith("https://example.supabase.co/storage/v1/object/tour-assets/photos/")
        assert url.endswith(".png")
        assert timeout == 35
        assert headers["apikey"] == "service-key"
        assert headers["authorization"] == "Bearer service-key"
        assert headers["content-type"] == "image/png"
        assert headers["x-upsert"] == "true"
        assert data == b"\x89PNG\r\n\x1a\n"
        return FakeResponse()

    monkeypatch.setattr(backend_main, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(backend_main, "SUPABASE_SERVICE_ROLE_KEY", "service-key")
    monkeypatch.setattr(backend_main, "SUPABASE_STORAGE_BUCKET", "tour-assets")
    monkeypatch.setattr(backend_main.requests, "post", fake_post)

    r = client.post(
        "/api/tour-assets/image",
        files={"file": ("view.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["configured"] is True
    assert body["storage"] == "supabase"
    assert body["bucket"] == "tour-assets"
    assert body["url"].startswith("https://example.supabase.co/storage/v1/object/public/tour-assets/photos/")
    assert body["url"].endswith(".png")


def test_runtime_google_provider_can_be_created_from_user_key():
    llm = llm_from_runtime_key("gemini", "test-key", "gemini-3.5-flash")
    assert llm.name == "gemini"


def test_api_tts_returns_wav_when_engine_available(monkeypatch, tmp_path):
    wav = tmp_path / "voice.wav"
    wav.write_bytes(b"RIFF....WAVEfmt ")

    def fake_synthesize(text: str, out_dir: str, voice: str):
        assert "Xin chào" in text
        return wav

    monkeypatch.setattr(backend_main, "synthesize", fake_synthesize)
    r = client.post("/api/tts", json={"text": "Xin chào tour tham quan", "voice": ""})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/wav")
    assert r.content.startswith(b"RIFF")


def test_api_tts_generate_returns_persisted_audio_url(monkeypatch, tmp_path):
    wav = tmp_path / "voice.wav"
    wav.write_bytes(b"RIFF....WAVEfmt ")

    def fake_synthesize(text: str, out_dir: str, voice: str):
        assert out_dir == backend_main.ARTIFACTS_DIR
        return wav

    monkeypatch.setattr(backend_main, "synthesize", fake_synthesize)
    monkeypatch.setattr(backend_main, "SUPABASE_URL", "")
    monkeypatch.setattr(backend_main, "SUPABASE_SERVICE_ROLE_KEY", "")
    r = client.post("/api/tts/generate", json={"text": "Xin chào tour tham quan", "voice": ""})
    assert r.status_code == 200
    body = r.json()
    assert body["audio_url"].endswith("/voice.wav")
    assert body["filename"] == "voice.wav"
    assert body["storage"] == "local"
