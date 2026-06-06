import os

import trimesh

from builder.procedural import build_glb
from builder.schemas import BuildingSpec, ModelInfo, SpaceType


def _spec(floors=5, rooms=6):
    return BuildingSpec(
        space_type=SpaceType.office,
        floors=floors,
        rooms_per_floor=rooms,
        occupancy=floors * rooms * 4,
        footprint_w=24.0,
        footprint_d=16.0,
    )


def test_build_glb_writes_valid_file(tmp_path):
    out = tmp_path / "b.glb"
    info = build_glb(_spec(), str(out))

    assert isinstance(info, ModelInfo)
    assert out.exists() and out.stat().st_size > 0
    assert info.backend == "procedural"
    assert info.tri_count > 0
    assert info.size_kb > 0


def test_room_nodes_match_floors_and_rooms(tmp_path):
    floors, rooms = 5, 6
    out = tmp_path / "b.glb"
    build_glb(_spec(floors, rooms), str(out))

    scene = trimesh.load(str(out))
    # one selectable floor mesh named room_<floor>_<idx> per room (walls are wall_*)
    room_nodes = [n for n in scene.geometry if n.startswith("room_")]
    assert len(room_nodes) == floors * rooms


def test_model_height_matches_spec(tmp_path):
    out = tmp_path / "b.glb"
    spec = _spec(8, 6)
    build_glb(spec, str(out))
    scene = trimesh.load(str(out))
    height = scene.bounds[1][1] - scene.bounds[0][1]
    # reaches the top floor + roof, plus a rooftop penthouse (< ~2 storeys extra)
    assert spec.total_height < height < spec.total_height + 2 * spec.floor_height
