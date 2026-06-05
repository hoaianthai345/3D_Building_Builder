"""Deterministic floor-plan layout: subdivide a rectangular plate into N rooms.

The LLM supplies room *types* and relative *weights* (so rooms are non-uniform);
this engine does the geometric packing via weighted slice-and-dice (recursive
binary split along the longer side). Output rectangles preserve input order.
"""

from __future__ import annotations

from typing import List, Tuple

Rect = Tuple[float, float, float, float]  # (x, z, w, d) min-corner + size, meters


def subdivide(x: float, z: float, w: float, d: float, weights: List[float]) -> List[Rect]:
    n = len(weights)
    if n == 0:
        return []
    if n == 1:
        return [(x, z, w, d)]

    total = float(sum(weights))
    # split weights into two contiguous groups closest to half the total
    half = total / 2.0
    acc = 0.0
    k = 0
    while k < n - 1 and acc + weights[k] <= half:
        acc += weights[k]
        k += 1
    k = max(1, min(k, n - 1))

    frac_a = sum(weights[:k]) / total
    if w >= d:  # split along X (the longer side)
        wa = w * frac_a
        left = subdivide(x, z, wa, d, weights[:k])
        right = subdivide(x + wa, z, w - wa, d, weights[k:])
    else:       # split along Z
        da = d * frac_a
        left = subdivide(x, z, w, da, weights[:k])
        right = subdivide(x, z + da, w, d - da, weights[k:])
    return left + right


def plate_rooms(footprint_w: float, footprint_d: float, weights: List[float],
                margin: float = 0.0) -> List[Rect]:
    """Lay out rooms on a plate centered at the origin (XZ plane)."""
    x0 = -footprint_w / 2 + margin
    z0 = -footprint_d / 2 + margin
    return subdivide(x0, z0, footprint_w - 2 * margin, footprint_d - 2 * margin, weights)
