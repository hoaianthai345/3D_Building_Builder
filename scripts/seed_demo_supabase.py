"""Seed a demo house tour into Supabase.

Usage:
    python scripts/seed_demo_supabase.py

Required env:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    SUPABASE_TOUR_PROJECTS_TABLE=tour_projects
    SUPABASE_STORAGE_BUCKET=3D

The script uploads one reusable guide audio file into Supabase Storage and
upserts a saved tour project whose manifest/audio URLs point to Supabase.
"""

from __future__ import annotations

import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIO = ROOT / "frontend/public/audio/landing-guide.mp3"


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def object_path(path: str) -> str:
    return "/".join(quote(part.strip("/"), safe="") for part in path.split("/") if part.strip("/"))


def supabase_headers(content_type: str = "application/json") -> dict[str, str]:
    key = env("SUPABASE_SERVICE_ROLE_KEY")
    return {
        "apikey": key,
        "authorization": f"Bearer {key}",
        "content-type": content_type,
    }


def public_url(path: str) -> str:
    base = env("SUPABASE_URL").rstrip("/")
    bucket = quote(env("SUPABASE_STORAGE_BUCKET", "3D"), safe="")
    return f"{base}/storage/v1/object/public/{bucket}/{object_path(path)}"


def upload_file(local_path: Path, remote_path: str) -> str:
    base = env("SUPABASE_URL").rstrip("/")
    bucket = quote(env("SUPABASE_STORAGE_BUCKET", "3D"), safe="")
    content_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
    res = requests.post(
        f"{base}/storage/v1/object/{bucket}/{object_path(remote_path)}",
        timeout=45,
        headers={
            **supabase_headers(content_type),
            "cache-control": "3600",
            "x-upsert": "true",
        },
        data=local_path.read_bytes(),
    )
    if res.status_code >= 400:
        raise RuntimeError(f"Storage upload failed {res.status_code}: {res.text[:300]}")
    return public_url(remote_path)


def route_signature(project: dict) -> str:
    return json.dumps(
        {
            "name": project["name"],
            "industry": project["industry"],
            "stops": [
                {
                    "index": index,
                    "id": stop["id"],
                    "src": stop["src"],
                    "kind": stop["kind"],
                    "source": stop["source"],
                    "remoteUrl": stop.get("remoteUrl", ""),
                }
                for index, stop in enumerate(project["stops"])
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def build_project(audio_url: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    stops = [
        {
            "id": "home-living",
            "src": "/landing/councilroom-pan.jpg",
            "kind": "panorama",
            "source": "sample",
        },
        {
            "id": "home-bedroom",
            "src": "/artifacts/sunrise-office-tower-5f-6r/pano/room_0_3.jpg",
            "kind": "panorama",
            "source": "sample",
        },
        {
            "id": "home-kitchen",
            "src": "/artifacts/sunrise-office-tower-5f-6r/pano/room_0_4.jpg",
            "kind": "panorama",
            "source": "sample",
        },
    ]
    tour = {
        "id": "demo-home-tour",
        "project_name": "Tour xem nhà mẫu Lake View",
        "industry": "real_estate",
        "created_at": now,
        "intro": "Xin chào quý khách, mời quý khách cùng tham quan căn hộ mẫu Lake View. Tour này đã có sẵn lời dẫn và audio để có thể mở lại ngay.",
        "outro": "Cảm ơn quý khách đã tham quan căn hộ mẫu Lake View. Hy vọng tour 3D đã giúp quý khách hình dung rõ hơn về không gian sống.",
        "stops": [
            {
                "id": "home-living",
                "image": stops[0]["src"],
                "kind": "panorama",
                "describe": {
                    "title": "Phòng khách rộng mở với cảm giác đón tiếp sang trọng",
                    "description": "Khu vực sinh hoạt chính tạo ấn tượng đầu tiên nhờ bố cục thoáng, ánh sáng dễ chịu và điểm nhìn rộng.",
                    "highlights": [
                        "Không gian mở giúp khách dễ hình dung công năng sinh hoạt",
                        "Ánh sáng và vật liệu tạo cảm giác cao cấp",
                        "Góc nhìn panorama phù hợp cho trải nghiệm xem nhà từ xa",
                    ],
                },
                "narration": "Điểm dừng đầu tiên là phòng khách. Đây là khu vực tạo cảm xúc ban đầu cho người xem nhờ bố cục mở, ánh sáng dễ chịu và cảm giác tiếp đón sang trọng.",
            },
            {
                "id": "home-bedroom",
                "image": stops[1]["src"],
                "kind": "panorama",
                "describe": {
                    "title": "Phòng ngủ riêng tư, cân bằng giữa nghỉ ngơi và tiện nghi",
                    "description": "Không gian phòng ngủ nhấn mạnh sự yên tĩnh, riêng tư và khả năng bố trí nội thất gọn gàng.",
                    "highlights": [
                        "Bố cục dễ kê giường, tủ và bàn nhỏ",
                        "Tạo cảm giác riêng tư cho người sử dụng",
                        "Phù hợp để khách hàng đánh giá tiện nghi sống thực tế",
                    ],
                },
                "narration": "Tiếp theo là phòng ngủ. Không gian này được giới thiệu như khu vực nghỉ ngơi riêng tư, nơi người xem có thể đánh giá khả năng bố trí giường, tủ và các tiện nghi cá nhân.",
            },
            {
                "id": "home-kitchen",
                "image": stops[2]["src"],
                "kind": "panorama",
                "describe": {
                    "title": "Khu bếp và tiện ích phụ trợ gọn gàng",
                    "description": "Khu bếp hoặc khu tiện ích phụ trợ cần được mô tả rõ về luồng thao tác, sự sạch sẽ và tính tiện dụng.",
                    "highlights": [
                        "Luồng sử dụng rõ ràng cho sinh hoạt hằng ngày",
                        "Dễ đánh giá hệ tủ, mặt bếp và khu lưu trữ",
                        "Tăng độ tin cậy cho tour vì thể hiện cả công năng phụ trợ",
                    ],
                },
                "narration": "Điểm dừng cuối trong căn hộ là khu bếp và tiện ích phụ trợ. Đây là nơi khách hàng quan tâm đến tính thực dụng: luồng thao tác, khu lưu trữ và cảm giác sạch sẽ.",
            },
        ],
    }
    audio = {
        "intro": audio_url,
        "stop:home-living": audio_url,
        "stop:home-bedroom": audio_url,
        "stop:home-kitchen": audio_url,
        "outro": audio_url,
    }
    tour["audio"] = audio
    tour["audioGeneratedAt"] = now
    tour["manifest"] = {
        "version": "tour-manifest-v1",
        "project_name": tour["project_name"],
        "total_segments": 5,
        "audio_segments": 5,
        "final_segment_id": "outro",
        "created_at": now,
        "steps": [
            {"id": "intro", "label": "Mở đầu", "sequence": 1, "image": stops[0]["src"], "kind": "panorama", "has_audio": True},
            {"id": "stop:home-living", "label": "Điểm 1", "source_stop_id": "home-living", "sequence": 2, "image": stops[0]["src"], "kind": "panorama", "has_audio": True},
            {"id": "stop:home-bedroom", "label": "Điểm 2", "source_stop_id": "home-bedroom", "sequence": 3, "image": stops[1]["src"], "kind": "panorama", "has_audio": True},
            {"id": "stop:home-kitchen", "label": "Điểm 3", "source_stop_id": "home-kitchen", "sequence": 4, "image": stops[2]["src"], "kind": "panorama", "has_audio": True},
            {"id": "outro", "label": "Kết", "sequence": 5, "image": stops[2]["src"], "kind": "panorama", "has_audio": True},
        ],
    }
    project = {
        "id": "demo-home-tour-lake-view",
        "name": tour["project_name"],
        "industry": "real_estate",
        "stops": stops,
        "savedTour": tour,
        "updatedAt": now,
    }
    project["savedTour"]["routeSignature"] = route_signature(project)
    return project


def upsert_project(project: dict) -> None:
    base = env("SUPABASE_URL").rstrip("/")
    table = env("SUPABASE_TOUR_PROJECTS_TABLE", "tour_projects")
    row = {"id": project["id"], "payload": project, "updated_at": project["updatedAt"]}
    res = requests.post(
        f"{base}/rest/v1/{table}?on_conflict=id",
        timeout=30,
        headers={**supabase_headers(), "prefer": "resolution=merge-duplicates,return=representation"},
        json=[row],
    )
    if res.status_code >= 400:
        raise RuntimeError(f"Project upsert failed {res.status_code}: {res.text[:300]}")


def main() -> None:
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    if not env("SUPABASE_URL") or not env("SUPABASE_SERVICE_ROLE_KEY"):
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    audio_path = Path(env("DEMO_TOUR_AUDIO_FILE", str(DEFAULT_AUDIO)))
    if not audio_path.exists():
        raise SystemExit(f"Demo audio file not found: {audio_path}")

    audio_url = upload_file(audio_path, "demo/home-tour/guide.mp3")
    project = build_project(audio_url)
    upsert_project(project)
    print("Seeded Supabase demo tour:")
    print(f"- project id: {project['id']}")
    print(f"- audio url: {audio_url}")


if __name__ == "__main__":
    main()
