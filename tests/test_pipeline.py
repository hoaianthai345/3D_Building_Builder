import os

from builder import procedural
from builder.pipeline import bundle_from_glb, generate, slugify
from builder.schemas import BuildingSpec, GenerateRequest, SpaceType


def test_slugify_strips_vietnamese_accents():
    assert slugify("Tòa Nhà Số Hóa") == "toa-nha-so-hoa"


def test_generate_full_bundle(tmp_path):
    req = GenerateRequest(
        project_name="Sunrise Office Tower",
        space_type=SpaceType.office,
        description="Tòa văn phòng 5 tầng, mỗi tầng 6 phòng, khoảng 120 người",
        target_audience="Doanh nghiệp SME",
    )
    bundle = generate(req, out_dir=str(tmp_path))

    # spec inferred from the natural-language prompt
    assert bundle.spec.floors == 5
    assert bundle.spec.rooms_per_floor == 6

    # describer contract: 3-5 highlights, >=2 tips
    assert 3 <= len(bundle.describer.highlights) <= 5
    assert len(bundle.describer.digitization_tips) >= 2
    assert bundle.describer.title

    # structure tree (v1.1): floors x rooms, ids match GLB node names
    assert bundle.structure is not None
    assert len(bundle.structure.floors) == 5
    assert len(bundle.structure.floors[0].rooms) == 6
    assert bundle.structure.floors[0].rooms[0].id == "room_0_0"
    assert all(r.area > 0 for f in bundle.structure.floors for r in f.rooms)

    # artifacts on disk
    assert (tmp_path / f"{bundle.id}.glb").exists()
    assert (tmp_path / f"{bundle.id}.json").exists()
    assert (tmp_path / "index.json").exists()


def test_bundle_from_glb_generative(tmp_path):
    # build a glb, then wrap it as a generative-style bundle (no structure)
    glb = tmp_path / "ext.glb"
    procedural.build_glb(
        BuildingSpec(space_type=SpaceType.office, floors=3, rooms_per_floor=4,
                     occupancy=40, footprint_w=20, footprint_d=14),
        str(glb))
    req = GenerateRequest(project_name="Gen Tower", space_type=SpaceType.office,
                          description="tòa nhà từ ảnh", target_audience="")
    bundle = bundle_from_glb(req, str(glb), out_dir=str(tmp_path), backend="generative")

    assert bundle.model.backend == "generative"
    assert bundle.structure is None
    assert bundle.model.tri_count > 0
    assert 3 <= len(bundle.describer.highlights) <= 5
    assert (tmp_path / f"{bundle.id}.glb").exists()
    assert (tmp_path / f"{bundle.id}.json").exists()


def test_explicit_params_override_description(tmp_path):
    req = GenerateRequest(
        project_name="Override Case",
        description="ghi 5 tầng trong mô tả",
        floors=9,
        rooms_per_floor=3,
    )
    bundle = generate(req, out_dir=str(tmp_path))
    assert bundle.spec.floors == 9
    assert bundle.spec.rooms_per_floor == 3
