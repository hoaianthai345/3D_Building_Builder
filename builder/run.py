"""CLI entry point. Build a scene bundle (GLB + JSON) from a prompt + params.

Examples
--------
    python -m builder.run --name "Sunrise Office Tower" --space office \\
        --prompt "5 tầng, mỗi tầng 6 phòng, khoảng 120 người" \\
        --audience "Doanh nghiệp SME" --out artifacts

    # then copy artifacts/* into frontend/public/artifacts/ for the demo
"""

from __future__ import annotations

import argparse

from .pipeline import generate, generate_from_image
from .schemas import GenerateRequest, SpaceType


def main() -> None:
    p = argparse.ArgumentParser(description="AI 3D Scene Describer — build one scene bundle")
    p.add_argument("--name", required=True, help="Tên dự án / không gian")
    p.add_argument("--space", default="office", choices=[s.value for s in SpaceType])
    p.add_argument("--prompt", default="", help="Mô tả ngôn ngữ tự nhiên")
    p.add_argument("--audience", default="", help="Nhóm khách hàng mục tiêu")
    p.add_argument("--floors", type=int, default=None)
    p.add_argument("--rooms", type=int, default=None, dest="rooms_per_floor")
    p.add_argument("--occupancy", type=int, default=None)
    p.add_argument("--out", default="artifacts", help="Thư mục xuất artifact")
    p.add_argument("--image", default=None,
                   help="Ảnh đầu vào -> backend generative (TRELLIS, cần GPU). Bỏ trống = procedural (CPU).")
    args = p.parse_args()

    req = GenerateRequest(
        project_name=args.name,
        space_type=SpaceType(args.space),
        description=args.prompt,
        target_audience=args.audience,
        floors=args.floors,
        rooms_per_floor=args.rooms_per_floor,
        occupancy=args.occupancy,
    )
    if args.image:  # generative backend (GPU)
        bundle = generate_from_image(req, args.image, out_dir=args.out)
    else:           # procedural backend (CPU, default)
        bundle = generate(req, out_dir=args.out)
    print(f"[ok] {bundle.id}")
    print(f"     spec   : {bundle.spec.floors} tầng x {bundle.spec.rooms_per_floor} phòng, "
          f"{bundle.spec.footprint_w}x{bundle.spec.footprint_d} m")
    print(f"     model  : {bundle.model.glb} ({bundle.model.tri_count} tris, {bundle.model.size_kb} KB)")
    print(f"     llm    : {bundle.meta.llm_provider} | build {bundle.meta.build_ms} ms")
    print(f"     title  : {bundle.describer.title}")
    print(f"     out    : {args.out}/{bundle.id}.json + .glb")


if __name__ == "__main__":
    main()
