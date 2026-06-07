"""Offline, deterministic LLM. Parses building params from Vietnamese text and
produces marketing copy from templates keyed by space type. No network, no key.

This keeps the whole pipeline runnable on Colab / CI / a fresh checkout, and gives
the demo sensible content even before a real ANTHROPIC_API_KEY is wired in.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from .base import LLMClient

_SPACE_VI = {
    "office": "văn phòng",
    "residential": "tòa nhà ở",
    "retail": "trung tâm bán lẻ",
    "mixed": "phức hợp đa năng",
    "education": "cơ sở giáo dục",
}

# Per-space highlight + tip templates. {n} placeholders filled in _describe.
_HIGHLIGHTS = {
    "office": [
        "Lõi giao thông trung tâm giúp luồng di chuyển ngắn và chia thuê linh hoạt theo phòng",
        "Mặt kính lớn tối ưu ánh sáng tự nhiên cho {rooms} phòng làm việc mỗi tầng",
        "Sảnh lễ tân tầng trệt định vị hình ảnh chuyên nghiệp cho khách thuê",
        "Quy mô {occupancy} chỗ phù hợp chia nhỏ cho nhiều doanh nghiệp cùng tòa",
    ],
    "residential": [
        "Bố cục {rooms} căn mỗi tầng tối ưu thông gió và ánh sáng cho từng hộ",
        "Lõi thang trung tâm rút ngắn hành lang, tăng diện tích sử dụng riêng tư",
        "Mặt đứng nhịp cửa đều tạo nhận diện hiện đại cho khu dân cư",
        "Quy mô {floors} tầng cân bằng giữa mật độ và không gian sống thoáng",
    ],
    "retail": [
        "Mặt tiền kính rộng tối đa khả năng trưng bày và thu hút khách qua đường",
        "Tầng thông sàn linh hoạt chia {rooms} gian hàng theo nhu cầu thuê",
        "Luồng khách được dẫn hướng quanh lõi trung tâm giúp tăng tiếp xúc gian hàng",
        "Sức chứa {occupancy} khách phù hợp cao điểm cuối tuần",
    ],
    "mixed": [
        "Khối đế bán lẻ kết hợp khối tháp văn phòng/ở tạo dòng tiền đa lớp",
        "Phân tầng chức năng rõ ràng giúp vận hành và an ninh tách biệt",
        "Mặt đứng đồng bộ giữ nhận diện thống nhất cho cả phức hợp",
        "Quy mô {floors} tầng, {occupancy} người khai thác công năng cả ngày",
    ],
    "education": [
        "Phòng học bố trí dọc hành lang sáng, giảm ồn chéo giữa {rooms} phòng mỗi tầng",
        "Lõi trung tâm gom thang và khu kỹ thuật, tối ưu lối thoát hiểm",
        "Mặt kính lớn đưa ánh sáng tự nhiên vào không gian học tập",
        "Sức chứa {occupancy} người đáp ứng quy mô lớp và sự kiện chung",
    ],
}

_TIPS = {
    "office": [
        "Quét kỹ lõi thang và hành lang vì đây là khu vực dễ thiếu điểm ảnh khi số hóa",
        "Chụp mặt kính vào lúc nắng dịu để tránh lóa và phản chiếu gây nhiễu mesh",
        "Đặt mốc tỷ lệ tại sảnh lễ tân để căn chỉnh kích thước mô hình chính xác",
    ],
    "residential": [
        "Quét từng tầng điển hình rồi nhân bản để tiết kiệm thời gian xử lý",
        "Chú ý ban công và lan can vì chi tiết mảnh dễ vỡ mesh khi tái dựng",
        "Giữ nhất quán hướng Bắc giữa các tầng để ghép mô hình không lệch",
    ],
    "retail": [
        "Ưu tiên độ phân giải cao ở mặt tiền và biển hiệu vì đây là điểm nhìn chính",
        "Quét ngoài giờ mở cửa để giảm người di chuyển gây bóng ma trong point cloud",
        "Đặt mốc tỷ lệ tại cửa chính để mô hình đúng kích thước thực",
    ],
    "mixed": [
        "Tách quy trình số hóa theo từng khối chức năng để dễ kiểm soát chất lượng",
        "Đồng bộ hệ tọa độ chung giữa khối đế và khối tháp trước khi ghép",
        "Chụp kỹ ranh giới chuyển tầng công năng vì hình học ở đó phức tạp",
    ],
    "education": [
        "Quét một phòng học mẫu thật chi tiết rồi tái sử dụng cho các phòng giống nhau",
        "Chú ý ánh sáng đều khi quét hành lang dài để tránh vệt tối làm hỏng texture",
        "Đặt mốc tỷ lệ tại cửa lớp để giữ kích thước mô hình chuẩn xác",
    ],
}


# Room program templates per space type: (name, type, weight, description).
_ROOM_POOL = {
    "office": [
        ("Sảnh lễ tân", "reception", 1.4, "Khu đón tiếp và chờ, tạo ấn tượng đầu tiên."),
        ("Khu làm việc mở", "open_work", 2.0, "Không gian làm việc linh hoạt nhiều chỗ ngồi."),
        ("Phòng họp", "meeting", 1.0, "Phòng họp kín cho trao đổi nhóm."),
        ("Phòng quản lý", "manager", 0.9, "Phòng làm việc riêng cho cấp quản lý."),
        ("Pantry", "service", 0.6, "Khu pha chế và nghỉ ngắn cho nhân viên."),
    ],
    "residential": [
        ("Căn hộ góc", "apartment", 1.6, "Căn hộ góc hai mặt thoáng, nhiều ánh sáng."),
        ("Căn hộ tiêu chuẩn", "apartment", 1.2, "Căn hộ điển hình bố cục gọn gàng."),
        ("Căn studio", "apartment", 0.8, "Căn nhỏ phù hợp người ở một mình."),
        ("Khu kỹ thuật", "service", 0.5, "Hộp kỹ thuật và lõi thang chung tầng."),
    ],
    "retail": [
        ("Gian hàng lớn", "shop", 1.8, "Gian thuê chính diện tích lớn, mặt tiền rộng."),
        ("Gian hàng nhỏ", "shop", 1.0, "Gian thuê tiêu chuẩn cho thương hiệu nhỏ."),
        ("Khu F&B", "fnb", 1.3, "Khu ẩm thực và chỗ ngồi cho khách."),
        ("Khu kỹ thuật", "service", 0.5, "Kho và khu hậu cần cho gian hàng."),
    ],
    "education": [
        ("Phòng học", "classroom", 1.4, "Phòng học tiêu chuẩn bố trí theo dãy bàn."),
        ("Phòng thực hành", "lab", 1.2, "Phòng thực hành trang bị bàn thí nghiệm."),
        ("Văn phòng giáo viên", "office", 0.9, "Khu làm việc của giáo viên."),
        ("Khu kỹ thuật", "service", 0.5, "Kho thiết bị và lõi kỹ thuật."),
    ],
    "mixed": [
        ("Gian bán lẻ", "shop", 1.5, "Gian thương mại ở khối đế."),
        ("Khu làm việc mở", "open_work", 1.6, "Không gian văn phòng linh hoạt."),
        ("Căn hộ", "apartment", 1.2, "Căn ở phía khối tháp."),
        ("Khu kỹ thuật", "service", 0.5, "Hộp kỹ thuật và giao thông đứng."),
    ],
}


# Industry-toned templates for the offline vision describer (mock can't see the
# image, so it returns plausible industry-appropriate copy).
_VISION_TPL = {
    "real_estate": {
        "title": "Không gian sống đẳng cấp, sẵn sàng để cảm nhận",
        "description": (
            "Bước vào không gian này, khách hàng cảm nhận ngay sự thoáng đãng và chỉn chu "
            "trong từng đường nét. Ánh sáng tự nhiên cùng vật liệu hoàn thiện tạo nên cảm "
            "giác sang trọng mà vẫn ấm cúng, rất phù hợp cho nhu cầu an cư và đầu tư."
        ),
        "highlights": [
            "Bố cục mở tối ưu công năng và tầm nhìn",
            "Ánh sáng tự nhiên dồi dào suốt cả ngày",
            "Vật liệu hoàn thiện cao cấp, bền đẹp theo thời gian",
            "Vị trí và tiện ích thuận tiện cho cuộc sống hiện đại",
        ],
    },
    "retail": {
        "title": "Mặt bằng bán lẻ thu hút, tối ưu trải nghiệm mua sắm",
        "description": (
            "Không gian được tổ chức để dẫn dắt dòng khách mượt mà, tối đa hóa khả năng "
            "trưng bày và tương tác với sản phẩm. Ánh sáng và bố cục làm nổi bật điểm nhấn "
            "thương hiệu, khuyến khích khách dừng lại lâu hơn và mua sắm nhiều hơn."
        ),
        "highlights": [
            "Luồng di chuyển dẫn khách qua các điểm trưng bày chính",
            "Khu vực điểm nhấn làm nổi bật sản phẩm chủ lực",
            "Ánh sáng tôn lên màu sắc và chất liệu hàng hóa",
            "Mặt tiền và lối vào thu hút khách qua đường",
        ],
    },
    "exhibition": {
        "title": "Không gian triển lãm dẫn dắt hành trình khám phá",
        "description": (
            "Không gian được thiết kế cho một hành trình tham quan có chủ đích: luồng di "
            "chuyển rõ ràng, ánh sáng định hướng sự chú ý vào hiện vật, và các điểm dừng "
            "tạo nhịp cảm xúc cho người xem từ lúc bước vào đến khi rời đi."
        ),
        "highlights": [
            "Luồng tham quan mạch lạc, dẫn dắt theo câu chuyện",
            "Ánh sáng trưng bày làm nổi bật hiện vật",
            "Điểm dừng tạo nhịp và khoảng lặng cho trải nghiệm",
            "Không gian linh hoạt cho nhiều loại nội dung trưng bày",
        ],
    },
}


def _first_int(pattern: str, text: str) -> int | None:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


class MockLLM(LLMClient):
    name = "mock"

    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        if purpose == "spec":
            return self._spec(context)
        if purpose == "describe":
            return self._describe(context)
        if purpose == "rooms":
            return self._rooms(context)
        if purpose == "vision_describe":
            return self._vision(context)
        if purpose == "tour":
            return self._tour(context)
        raise ValueError(f"unknown purpose: {purpose}")

    # -- ordered stop descriptions -> guide narration ---------------------- #
    def _tour(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        project = str(ctx.get("project_name") or "không gian tham quan").strip()
        industry = str(ctx.get("industry") or "real_estate")
        stops = list(ctx.get("stops") or [])
        n = max(len(stops), 1)

        if industry == "retail":
            intro = f"Chào mừng bạn đến với {project}. Tôi sẽ dẫn bạn qua {n} khu vực chính, tập trung vào luồng khách, điểm trưng bày và trải nghiệm mua sắm."
            outro = f"Cảm ơn bạn đã tham quan {project}. Lộ trình này có thể dùng làm kịch bản giới thiệu mặt bằng, đào tạo nhân sự hoặc tư vấn khách thuê."
        elif industry == "exhibition":
            intro = f"Chào mừng bạn đến với {project}. Hành trình hôm nay gồm {n} điểm dừng, mỗi điểm mở ra một lớp nội dung và cảm xúc khác nhau."
            outro = f"Cảm ơn bạn đã đồng hành trong hành trình tại {project}. Đây là tuyến tham quan có thể mở rộng thêm hiện vật, âm thanh và chỉ dẫn tương tác."
        else:
            intro = f"Xin chào và chào mừng quý khách đến với {project}. Tôi sẽ đóng vai hướng dẫn viên, đưa quý khách qua {n} không gian nổi bật của dự án."
            outro = f"Cảm ơn quý khách đã tham quan {project}. Hy vọng phần thuyết minh đã giúp quý khách hình dung rõ hơn về công năng, cảm giác không gian và giá trị của dự án."

        narrated = []
        for i, stop in enumerate(stops, start=1):
            desc = stop.get("describe") or {}
            title = str(desc.get("title") or f"Điểm dừng {i}").strip()
            description = str(desc.get("description") or "").strip()
            highlights = [str(h).strip() for h in desc.get("highlights", []) if str(h).strip()]
            hi = " ".join(f"Điểm đáng chú ý là {h.rstrip('.')}." for h in highlights[:2])
            transition = "Tiếp theo, chúng ta sẽ di chuyển sang điểm kế tiếp để thấy rõ hơn sự liên kết trong toàn bộ lộ trình."
            if i == len(stops):
                transition = "Đây là điểm dừng cuối, nơi tổng hợp lại cảm nhận chính của toàn bộ hành trình."
            narrated.append({
                "id": str(stop.get("id") or f"s{i}"),
                "narration": f"Điểm dừng {i}: {title}. {description} {hi} {transition}".strip(),
            })

        return {"intro": intro, "stops": narrated, "outro": outro}

    # -- image (ignored by mock) + industry -> stop describe ---------------- #
    def _vision(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        industry = str(ctx.get("industry") or "real_estate")
        tpl = _VISION_TPL.get(industry, _VISION_TPL["real_estate"])
        return {
            "title": tpl["title"],
            "description": tpl["description"],
            "highlights": list(tpl["highlights"]),
        }

    # -- spec -> room program for a typical floor -------------------------- #
    def _rooms(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        space = str(ctx.get("space_type") or "office")
        space = getattr(space, "value", space)
        n = int(ctx.get("rooms_per_floor") or 4)
        pool = _ROOM_POOL.get(space, _ROOM_POOL["office"])
        rooms = []
        for i in range(n):
            name, rtype, weight, desc = pool[i % len(pool)]
            rooms.append({"name": name, "type": rtype, "weight": weight, "description": desc})
        return {"rooms": rooms}

    # -- NL + params -> spec hints ----------------------------------------- #
    def _spec(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        desc = str(ctx.get("description") or "")
        floors = ctx.get("floors") or _first_int(r"(\d+)\s*tầng", desc) or 3
        rooms = ctx.get("rooms_per_floor") or _first_int(r"(\d+)\s*(?:phòng|gian|căn|lớp)", desc) or 4
        occ = ctx.get("occupancy")
        if occ is None:
            occ = _first_int(r"(\d+)\s*(?:người|nhân sự|chỗ|khách|học sinh|sinh viên)", desc)
        if occ is None:
            occ = int(rooms) * int(floors) * 4
        return {
            "floors": int(floors),
            "rooms_per_floor": int(rooms),
            "occupancy": int(occ),
            "layout_hint": "central-core",
        }

    # -- spec -> marketing copy -------------------------------------------- #
    def _describe(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        space = str(ctx.get("space_type") or "office")
        space = getattr(space, "value", space)  # accept Enum or str
        vi = _SPACE_VI.get(space, "không gian")
        floors = int(ctx.get("floors") or 3)
        rooms = int(ctx.get("rooms_per_floor") or 4)
        occ = int(ctx.get("occupancy") or rooms * floors * 4)
        name = str(ctx.get("project_name") or "Dự án").strip()
        audience = str(ctx.get("target_audience") or "").strip()

        fill = {"floors": floors, "rooms": rooms, "occupancy": occ}
        highlights = [h.format(**fill) for h in _HIGHLIGHTS.get(space, _HIGHLIGHTS["office"])]
        tips = [t for t in _TIPS.get(space, _TIPS["office"])]

        title = f"{name} — Không gian {vi} {floors} tầng hiện đại"
        aud = f" hướng tới {audience}" if audience else ""
        summary = (
            f"{name} là {vi} quy mô {floors} tầng, mỗi tầng khoảng {rooms} phòng, "
            f"sức chứa chừng {occ} người{aud}. Mô hình được tổ chức quanh lõi giao thông "
            f"trung tâm với mặt đứng nhịp cửa đều, tối ưu ánh sáng tự nhiên và tạo nhận "
            f"diện chuyên nghiệp ngay từ ấn tượng đầu tiên."
        )
        return {
            "title": title,
            "summary": summary,
            "highlights": highlights,
            "digitization_tips": tips,
        }
