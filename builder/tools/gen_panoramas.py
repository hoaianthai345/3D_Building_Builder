"""Generate REAL 360 panoramas via Blockade Labs Skybox AI (optional, needs key).

Reads each room's seeded ``panorama.prompt``, asks Skybox to generate an
equirectangular image, downloads it to <artifacts>/<id>/pano/<room_id>.jpg, and
sets ``panorama.image`` + status="ready" in the bundle JSON.

Requires:  export BLOCKADE_API_KEY=...      (https://www.blockadelabs.com/ API)
Usage:     python -m builder.tools.gen_panoramas --id <bundle_id> [--limit N]

NOTE: untested without a key. Verify the current Skybox API fields/endpoints and
the desired ``skybox_style_id`` against Blockade's docs before a full run; use
--limit to try one room first.
"""

from __future__ import annotations

import argparse
import json
import os
import time

import requests

API = "https://backend.blockadelabs.com/api/v1"


def _generate(api_key: str, prompt: str, style_id: int | None) -> str:
    body = {"prompt": prompt}
    if style_id is not None:
        body["skybox_style_id"] = style_id
    r = requests.post(f"{API}/skybox", headers={"x-api-key": api_key}, json=body, timeout=60)
    r.raise_for_status()
    req_id = r.json().get("id") or r.json().get("request_id")

    # poll until complete
    for _ in range(120):
        time.sleep(5)
        s = requests.get(f"{API}/imagine/requests/{req_id}", headers={"x-api-key": api_key}, timeout=60)
        s.raise_for_status()
        data = s.json().get("request", s.json())
        status = data.get("status")
        if status in {"complete", "completed"}:
            return data.get("file_url") or data.get("file_url_isolated")
        if status in {"error", "abort"}:
            raise RuntimeError(f"Skybox failed: {data}")
    raise TimeoutError("Skybox generation timed out")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate 360 panoramas via Skybox AI")
    p.add_argument("--id", required=True)
    p.add_argument("--artifacts", default="frontend/public/artifacts")
    p.add_argument("--style-id", type=int, default=None, help="Skybox style id (optional)")
    p.add_argument("--limit", type=int, default=None, help="cap number of rooms (try 1 first)")
    args = p.parse_args()

    api_key = os.getenv("BLOCKADE_API_KEY")
    if not api_key:
        raise SystemExit("Set BLOCKADE_API_KEY (https://www.blockadelabs.com/).")

    json_path = os.path.join(args.artifacts, f"{args.id}.json")
    with open(json_path, encoding="utf-8") as fh:
        bundle = json.load(fh)

    pano_dir = os.path.join(args.artifacts, args.id, "pano")
    os.makedirs(pano_dir, exist_ok=True)

    rooms = [r for f in bundle["structure"]["floors"] for r in f["rooms"]
             if (r.get("panorama") or {}).get("status") != "ready"]
    if args.limit:
        rooms = rooms[: args.limit]

    for i, room in enumerate(rooms, 1):
        prompt = (room.get("panorama") or {}).get("prompt", "")
        print(f"[{i}/{len(rooms)}] {room['id']} ...")
        url = _generate(api_key, prompt, args.style_id)
        img = requests.get(url, timeout=120).content
        rel = f"{args.id}/pano/{room['id']}.jpg"
        with open(os.path.join(args.artifacts, rel), "wb") as fh:
            fh.write(img)
        room["panorama"]["image"] = rel
        room["panorama"]["status"] = "ready"
        with open(json_path, "w", encoding="utf-8") as fh:  # save incrementally
            json.dump(bundle, fh, ensure_ascii=False, indent=2)

    print(f"[ok] generated {len(rooms)} panoramas -> {pano_dir}")


if __name__ == "__main__":
    main()
