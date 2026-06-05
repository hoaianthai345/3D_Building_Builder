"""Generate CPU placeholder 360 panoramas for a scene (offline, no API).

Makes a simple equirectangular image per room (tinted by room type, with the room
name), writes them to <artifacts>/<id>/pano/<room_id>.jpg, and sets each
Room.panorama.image + status="ready" in the bundle JSON. Lets the "Bước vào"
viewer work in the demo before real AI panoramas exist. Replace later with
gen_panoramas.py (Skybox AI).

    python -m builder.tools.gen_placeholder_panoramas --id sunrise-office-tower-5f-6r
"""

from __future__ import annotations

import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

_TYPE_HEX = {
    "reception": "#cdd9f5", "meeting": "#9db4e8", "open_work": "#dfe6f6",
    "manager": "#b6c6ee", "service": "#e3e0d6", "apartment": "#dfe6f6",
    "shop": "#cdd9f5", "fnb": "#ecdcc4", "classroom": "#d7e3d6",
    "lab": "#cfe0e6", "office": "#dfe6f6", "default": "#dde2ea",
}
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _make_panorama(name: str, room_type: str, w: int = 1024, h: int = 512) -> Image.Image:
    floor = _hex(_TYPE_HEX.get(room_type, _TYPE_HEX["default"]))
    ceil = (245, 244, 240)
    img = Image.new("RGB", (w, h))
    px = img.load()
    horizon = h // 2
    for y in range(h):
        if y < horizon:  # ceiling -> wall
            t = y / horizon
            col = tuple(int(ceil[i] + (floor[i] - ceil[i]) * t * 0.5) for i in range(3))
        else:            # wall -> floor (darker)
            t = (y - horizon) / (h - horizon)
            col = tuple(int(floor[i] * (1 - 0.35 * t)) for i in range(3))
        for x in range(w):
            px[x, y] = col

    draw = ImageDraw.Draw(img)
    draw.line([(0, horizon), (w, horizon)], fill=(255, 255, 255), width=2)
    # orientation cues: evenly spaced "windows" along the wall
    for cx in range(w // 8, w, w // 4):
        draw.rectangle([cx - 26, horizon - 70, cx + 26, horizon - 10], outline=(255, 255, 255), width=2)

    label = f"{name}"
    sub = "360 placeholder - generate real image with Skybox AI"
    f1, f2 = _font(30), _font(16)
    tb = draw.textbbox((0, 0), label, font=f1)
    draw.text(((w - (tb[2] - tb[0])) / 2, horizon + 40), label, fill=(31, 30, 28), font=f1)
    sb = draw.textbbox((0, 0), sub, font=f2)
    draw.text(((w - (sb[2] - sb[0])) / 2, horizon + 84), sub, fill=(90, 86, 78), font=f2)
    return img


def main() -> None:
    p = argparse.ArgumentParser(description="Generate CPU placeholder 360 panoramas")
    p.add_argument("--id", required=True, help="bundle id (without .json)")
    p.add_argument("--artifacts", default="frontend/public/artifacts")
    args = p.parse_args()

    json_path = os.path.join(args.artifacts, f"{args.id}.json")
    with open(json_path, encoding="utf-8") as fh:
        bundle = json.load(fh)

    pano_dir = os.path.join(args.artifacts, args.id, "pano")
    os.makedirs(pano_dir, exist_ok=True)

    count = 0
    for floor in bundle["structure"]["floors"]:
        for room in floor["rooms"]:
            img = _make_panorama(room["name"], room["type"])
            rel = f"{args.id}/pano/{room['id']}.jpg"
            img.save(os.path.join(args.artifacts, rel), quality=78)
            room.setdefault("panorama", {"prompt": "", "image": "", "status": "pending"})
            room["panorama"]["image"] = rel
            room["panorama"]["status"] = "ready"
            count += 1

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, ensure_ascii=False, indent=2)
    print(f"[ok] {count} placeholder panoramas -> {pano_dir}")
    print(f"[ok] updated {json_path}")


if __name__ == "__main__":
    main()
