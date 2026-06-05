"""Prompt builders for the real LLM provider. MockLLM ignores these strings and
uses the structured context instead, so the two stay behaviourally aligned."""

from __future__ import annotations

from .schemas import GenerateRequest, BuildingSpec


def spec_prompt(req: GenerateRequest) -> str:
    return (
        "Trích thông số dựng mô hình tòa nhà từ mô tả sau. "
        "Trả JSON với khóa: floors (int), rooms_per_floor (int), occupancy (int), "
        "layout_hint (chuỗi ngắn tiếng Việt không dấu, ví dụ central-core).\n\n"
        f"Tên dự án: {req.project_name}\n"
        f"Loại không gian: {req.space_type.value}\n"
        f"Mô tả: {req.description}\n"
        f"Thông số đã cho (có thể trống): floors={req.floors}, "
        f"rooms_per_floor={req.rooms_per_floor}, occupancy={req.occupancy}\n"
        "Nếu thông số đã cho khác trống thì giữ nguyên, chỉ suy luận phần còn thiếu."
    )


def rooms_prompt(spec: BuildingSpec, req: GenerateRequest) -> str:
    return (
        "Đề xuất danh sách phòng cho MỘT tầng điển hình. Trả JSON với khóa rooms là "
        "mảng các object {name (tiếng Việt), type, weight (số, tỉ lệ diện tích tương đối), "
        "description (1 câu)}. type thuộc: reception, meeting, open_work, manager, service, "
        "apartment, shop, fnb, classroom, lab, office, default.\n\n"
        f"Loại không gian: {spec.space_type.value}\n"
        f"Số phòng mỗi tầng: {spec.rooms_per_floor}\n"
        f"Mô tả: {req.description}\n"
        f"Trả đúng {spec.rooms_per_floor} phần tử, phòng nên khác kích thước (weight khác nhau)."
    )


def describe_prompt(spec: BuildingSpec, req: GenerateRequest) -> str:
    return (
        "Viết nội dung giới thiệu cho một dự án số hóa 3D. Trả JSON với khóa: "
        "title (chuỗi), summary (1 đoạn ngắn hấp dẫn), highlights (mảng 3-5 chuỗi), "
        "digitization_tips (mảng 2-5 chuỗi lưu ý khi số hóa 3D loại không gian này).\n\n"
        f"Tên dự án: {req.project_name}\n"
        f"Loại không gian: {spec.space_type.value}\n"
        f"Quy mô: {spec.floors} tầng, {spec.rooms_per_floor} phòng/tầng, "
        f"sức chứa {spec.occupancy} người\n"
        f"Nhóm khách hàng mục tiêu: {req.target_audience}\n"
        f"Mô tả gốc: {req.description}\n"
        "Giọng văn chuyên nghiệp, cụ thể, tránh sáo ngữ. Tiếng Việt."
    )
