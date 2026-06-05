"""Enrich the Aurora mixed-use tower artifact with room copy and 360 prompts.

This script intentionally changes only content fields in the existing bundle:
room names, room descriptions, panorama prompts, and describer copy. Geometry,
room ids, model metadata, input, and spec are preserved.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from builder.schemas import SceneBundle  # noqa: E402


ARTIFACT = ROOT / "frontend/public/artifacts/aurora-mixed-use-tower-30f-6r.json"
EM_DASH = "\u2014"
STYLE = "modern minimalist Aurora Tower style, warm oak wood, clear glass, brushed brass details, muted blue accents, light stone floors"


RETAIL_PLANS = {
    1: [
        (
            "Sảnh thương mại Aurora T1-01",
            "Không gian đón khách ở tầng trệt kết nối trực tiếp với phố và lối vào tháp. Khu này ưu tiên mặt tiền rộng, quầy thông tin rõ ràng và luồng di chuyển dễ đọc cho nhà đầu tư, khách mua sắm và khách thuê văn phòng.",
            "a premium ground floor retail arrival lobby with a concierge desk, boutique display islands, double height glass storefronts",
            "soft daylight through full height street glazing and warm recessed ceiling light",
        ),
        (
            "Boutique thời trang T1-02",
            "Gian boutique nhỏ được bố trí cho thương hiệu thời trang hoặc phụ kiện cao cấp cần nhận diện nhanh từ sảnh. Bố cục gọn, có mảng trưng bày sát kính và khu thử đồ kín đáo để phục vụ khách mua sắm vãng lai.",
            "a compact luxury fashion boutique with oak display rails, mirror panels, fitting room curtains, curated shelves",
            "bright storefront daylight with warm gallery spotlights",
        ),
        (
            "Cafe mặt phố T1-03",
            "Khu cafe là điểm dừng chân đầu tiên cho cư dân, khách văn phòng và khách bán lẻ. Không gian dùng vật liệu ấm, bàn nhỏ linh hoạt và tầm nhìn ra phố để tạo nhịp hoạt động cả ngày.",
            "a street facing cafe with a stone service counter, warm wood tables, banquette seating, glass storefront views",
            "morning daylight from the facade mixed with soft pendant lighting",
        ),
        (
            "Hậu cần bán lẻ T1-04",
            "Phòng hậu cần phục vụ tiếp nhận hàng, lưu kho ngắn hạn và vận hành kỹ thuật cho khối đế. Dù là khu phụ trợ, không gian vẫn cần sạch, sáng và dễ kiểm soát để giảm gián đoạn cho các gian thuê.",
            "a clean retail back of house utility room with storage racks, service cabinets, labeled delivery zones",
            "even neutral ceiling lighting with a small clerestory daylight strip",
        ),
        (
            "Showroom phong cách sống T1-05",
            "Showroom diện tích lớn phù hợp cho nội thất, công nghệ hoặc sản phẩm phong cách sống. Mặt bằng mở giúp thương hiệu dựng nhiều cụm trải nghiệm, đồng thời giữ tầm nhìn xuyên suốt từ sảnh chính.",
            "a lifestyle showroom with modular product displays, lounge vignettes, glass partitions, refined stone and wood finishes",
            "balanced daylight and warm museum quality track lighting",
        ),
        (
            "Quầy pop-up T1-06",
            "Gian pop-up nhỏ dành cho chiến dịch ngắn hạn, kiosk thương hiệu hoặc dịch vụ tiện ích. Vị trí này tạo thêm nhịp thương mại ở tầng trệt mà không làm nghẽn tuyến di chuyển chính.",
            "a small premium pop up retail kiosk with flexible counters, illuminated shelving, branded display niches",
            "clear daylight from nearby glazing and focused warm accent lights",
        ),
    ],
    2: [
        (
            "Gian wellness T2-01",
            "Tầng 2 chuyển sang trải nghiệm mua sắm chậm hơn với dịch vụ chăm sóc sức khỏe và làm đẹp. Phòng lớn này phù hợp cho spa, clinic nhẹ hoặc showroom wellness phục vụ cư dân và khách văn phòng.",
            "a wellness retail suite with reception counter, calming treatment lounge, soft fabric panels, indoor planters",
            "diffused daylight and warm indirect cove lighting",
        ),
        (
            "Studio mỹ phẩm T2-02",
            "Studio nhỏ dành cho tư vấn mỹ phẩm, nước hoa hoặc chăm sóc cá nhân. Không gian cần cảm giác riêng tư hơn tầng trệt nhưng vẫn đủ mở để khách dễ bước vào từ hành lang thương mại.",
            "a compact beauty consultation studio with display shelving, testing counter, soft mirrors, pale stone surfaces",
            "soft daylight with flattering warm vanity lighting",
        ),
        (
            "Nhà hàng casual dining T2-03",
            "Khu F&B tầng 2 phục vụ bữa trưa văn phòng và bữa tối của cư dân. Bố cục ưu tiên chỗ ngồi thoải mái, quầy phục vụ rõ ràng và vật liệu bền cho cường độ vận hành cao.",
            "a casual dining restaurant with booth seating, open service counter, wood ceiling slats, glass balustrade views",
            "late afternoon daylight and warm pendant lamps over tables",
        ),
        (
            "Kho vận hành F&B T2-04",
            "Phòng kỹ thuật và kho khô hỗ trợ trực tiếp cho nhà hàng tầng 2. Các kệ lưu trữ, tủ thiết bị và bề mặt dễ vệ sinh giúp đội vận hành phục vụ ổn định trong giờ cao điểm.",
            "a tidy food and beverage support room with dry storage shelving, stainless prep surfaces, service cabinets",
            "bright neutral task lighting",
        ),
        (
            "Concept store T2-05",
            "Concept store tạo điểm nhấn cho khối đế bằng hàng trưng bày chọn lọc, góc tư vấn và trải nghiệm sản phẩm. Đây là phòng có giá trị cho khách thuê muốn kết hợp bán lẻ với câu chuyện thương hiệu.",
            "a premium concept store with curated display tables, warm wood wall bays, glass consultation alcove, brass accents",
            "soft daylight from atrium glazing and warm retail spotlights",
        ),
        (
            "Gian dịch vụ nhanh T2-06",
            "Gian dịch vụ nhanh dành cho tiện ích hằng ngày như giặt ủi, giao nhận hoặc sửa chữa nhỏ. Phòng nhỏ nhưng cần nhận diện rõ, quầy tiếp khách gọn và tuyến vào ra không xung đột với khu ăn uống.",
            "a compact service retail unit with a clean front counter, parcel shelves, utility cabinets, blue accent signage",
            "even daylight with crisp linear ceiling lights",
        ),
    ],
    3: [
        (
            "Sảnh sự kiện bán lẻ T3-01",
            "Tầng 3 đóng vai trò lớp chuyển tiếp giữa khối thương mại và tháp văn phòng. Phòng lớn này có thể dùng cho triển lãm sản phẩm, sự kiện leasing hoặc khu demo dành cho nhà đầu tư.",
            "a flexible retail event gallery with movable display plinths, presentation wall, lounge chairs, glass perimeter",
            "bright skylit daylight effect and adjustable warm gallery lighting",
        ),
        (
            "Phòng trải nghiệm công nghệ T3-02",
            "Không gian nhỏ tập trung vào sản phẩm công nghệ, thiết bị thông minh hoặc trải nghiệm số. Cách tổ chức cần hiện đại, sạch và dễ cập nhật để phục vụ nhiều tenant khác nhau theo mùa.",
            "a compact smart technology experience room with interactive display counters, dark glass screens, warm oak panels",
            "controlled ambient lighting with subtle blue accent glow",
        ),
        (
            "Food hall tầng đế T3-03",
            "Food hall tầng 3 bổ sung lựa chọn ăn uống cho nhân viên văn phòng trước khi vào khối tháp. Khu này có nhiều cụm ngồi, quầy chung và vật liệu ấm để giữ cảm giác cao cấp.",
            "a refined food hall seating zone with shared tables, cafe counter, planter dividers, glass rail views",
            "diffused daylight from atrium side and warm decorative pendants",
        ),
        (
            "Phòng điều phối khối đế T3-04",
            "Phòng điều phối quản lý hậu cần, an ninh nhẹ và lịch sự kiện của ba tầng bán lẻ. Không gian nhỏ nhưng quan trọng cho vận hành, cần tủ hồ sơ, bàn trực và tầm nhìn kiểm soát hành lang.",
            "a retail operations control room with compact workstations, storage cabinets, wall monitors, clean service finishes",
            "neutral task lighting with a soft daylight side window",
        ),
        (
            "Gallery thương hiệu T3-05",
            "Gallery thương hiệu dành cho các hoạt động giới thiệu dự án, căn hộ mẫu rút gọn hoặc trưng bày tenant chiến lược. Đây là điểm chạm hữu ích khi dẫn khách đầu tư lên các tầng cao.",
            "a brand gallery with illuminated wall displays, model tables, lounge seating, stone floor, glass and brass details",
            "warm gallery spotlights with soft ambient daylight",
        ),
        (
            "Phòng tư vấn thuê mặt bằng T3-06",
            "Phòng tư vấn nhỏ hỗ trợ gặp nhanh khách thuê bán lẻ hoặc khách mua dịch vụ. Bố cục gồm bàn trao đổi, màn hình trình chiếu và kệ tài liệu, phù hợp cho các buổi tư vấn ngắn.",
            "a small leasing consultation room with a round table, wall screen, brochure shelves, warm wood and glass finishes",
            "soft daylight with focused warm ceiling lights",
        ),
    ],
}


OFFICE_CYCLES = [
    [
        ("Sảnh lễ tân văn phòng", "Sảnh lễ tân tạo ấn tượng chuyên nghiệp cho khách thuê văn phòng và đối tác đến làm việc. Không gian có quầy tiếp đón, ghế chờ và bảng chỉ dẫn rõ ràng để phân luồng trước khi vào các khu làm việc.", "a corporate office reception lobby with a stone welcome desk, waiting lounge, directory wall, glass partitions", "clear daylight from perimeter windows and warm linear ceiling light"),
        ("Khu làm việc linh hoạt", "Khu làm việc mở dành cho nhóm dự án cần thay đổi cấu hình chỗ ngồi nhanh. Bàn module, tủ thấp và lối đi rõ giúp doanh nghiệp mở rộng hoặc thu gọn mà ít ảnh hưởng vận hành.", "a flexible open office workspace with modular desks, ergonomic chairs, low storage, warm wood acoustic panels", "soft daylight across workstations with balanced indirect office lighting"),
        ("Phòng họp chiến lược", "Phòng họp được thiết kế cho các cuộc trao đổi với khách thuê lớn, nhà đầu tư hoặc ban điều hành. Bàn dài, màn hình trình chiếu và xử lý âm học giúp nội dung trình bày rõ ràng trong các buổi làm việc quan trọng.", "a strategic board meeting room with a long oak table, leather task chairs, wall display, acoustic panels, glass side wall", "controlled daylight with warm dimmable meeting lights"),
        ("Khu pantry văn phòng", "Pantry là điểm nghỉ ngắn cho nhân viên giữa các phiên làm việc. Quầy nước, bàn đứng và vài chỗ ngồi nhỏ tạo môi trường giao tiếp nhẹ mà không ảnh hưởng khu làm việc chính.", "a premium office pantry with coffee bar, high tables, small lounge seats, storage wall, stone counter", "warm pendant lights and soft daylight from a narrow window"),
        ("Không gian làm việc nhóm", "Khu làm việc nhóm dành cho các đội cần trao đổi thường xuyên hơn khu mở thông thường. Bố cục có bảng ghi chú, bàn cụm và vách kính để cân bằng giữa cộng tác và tập trung.", "a team collaboration office zone with clustered desks, writable boards, glass dividers, blue fabric pinboards", "bright daylight with even recessed ceiling lighting"),
        ("Phòng họp nhanh", "Phòng họp nhanh phù hợp cho cuộc gọi video, phỏng vấn ngắn hoặc trao đổi nội bộ. Diện tích vừa phải, bàn tròn và màn hình gắn tường giúp tenant sử dụng hiệu quả trong ngày làm việc dày đặc.", "a compact huddle meeting room with a round table, video screen, acoustic wall panels, warm oak trim", "soft daylight and focused warm ceiling lights"),
    ],
    [
        ("Sảnh tenant cao cấp", "Sảnh tenant trên tầng trung giúp phân tách nhận diện cho các doanh nghiệp đang thuê diện tích lớn. Khu chờ có vật liệu cao cấp và góc tiếp khách nhanh, phù hợp đón đối tác trước khi vào văn phòng.", "a premium tenant elevator lobby with concierge counter, lounge chairs, stone feature wall, brass signage", "clean daylight with warm cove lighting"),
        ("Không gian làm việc tập trung", "Khu làm việc mở được tổ chức yên tĩnh hơn cho các nhóm tài chính, tư vấn hoặc vận hành dữ liệu. Mặt bằng ưu tiên ánh sáng ổn định, khoảng cách bàn hợp lý và ít nhiễu thị giác.", "a quiet focused open office with bench desks, privacy screens, acoustic ceiling baffles, glass perimeter", "even north facing daylight and soft neutral office lighting"),
        ("Phòng họp lớn", "Phòng họp lớn phục vụ đào tạo khách thuê, họp liên phòng ban hoặc trình bày với nhà đầu tư. Không gian có bàn dài, màn hình lớn và vùng lưu thông quanh phòng để hỗ trợ nhiều kiểu thiết lập.", "a large executive conference room with a long table, integrated presentation screen, acoustic timber wall, glass facade", "filtered daylight with warm adjustable conference lighting"),
        ("Lounge nhân viên", "Lounge nhân viên tạo điểm nghỉ rộng hơn pantry, phù hợp trò chuyện không chính thức hoặc làm việc ngắn ngoài bàn chính. Ghế sofa, bàn cafe và cây xanh giúp tầng văn phòng bớt căng thẳng.", "an office staff lounge with sofas, coffee tables, indoor planters, warm wood shelves, glass city view wall", "soft afternoon daylight and warm lounge lighting"),
        ("Studio brainstorm", "Studio brainstorm dành cho các buổi thiết kế dịch vụ, lập kế hoạch sản phẩm hoặc workshop nội bộ. Bề mặt viết, bàn linh hoạt và chỗ đứng quanh phòng giúp nhóm làm việc năng động hơn.", "a creative brainstorm studio with movable tables, writable glass walls, pin up boards, modular stools", "bright diffuse daylight and adjustable track lights"),
        ("Phone booth và phòng gọi", "Cụm phòng gọi hỗ trợ nhân viên thực hiện cuộc gọi riêng hoặc họp video ngắn. Thiết kế nhỏ, cách âm tốt và chiếu sáng dễ chịu giúp tăng chất lượng làm việc trong môi trường mở.", "a compact office phone booth room with acoustic fabric walls, small desk ledge, video call screen, warm wood door frame", "soft controlled task lighting with minimal daylight"),
    ],
    [
        ("Sảnh điều hành tầng cao", "Sảnh điều hành trên các tầng cao tạo cảm giác riêng tư và cao cấp cho tenant chiến lược. Từ khu chờ có thể cảm nhận tầm nhìn thành phố, phù hợp các cuộc gặp đối tác có giá trị lớn.", "an upper floor executive reception lobby with panoramic city windows, marble desk, lounge seating, brass and blue accents", "high altitude daylight with warm recessed ceiling light"),
        ("Khu làm việc giám đốc", "Khu làm việc này dành cho nhóm quản lý hoặc bộ phận cần tính bảo mật cao hơn. Bàn làm việc rộng, tủ lưu trữ kín và vách kính giúp giữ sự minh bạch nhưng vẫn chuyên nghiệp.", "an executive open office suite with larger desks, private storage, glass partitions, warm oak panels, city views", "clear high floor daylight and calm indirect lighting"),
        ("Phòng họp hội đồng", "Phòng họp hội đồng là không gian trang trọng nhất trong khối văn phòng. Vật liệu gỗ ấm, ghế cao cấp và màn hình lớn giúp hỗ trợ ra quyết định, thuyết trình tài chính và gặp nhà đầu tư.", "an executive boardroom with a polished oak table, high back chairs, large media wall, acoustic wood panels, skyline view", "controlled daylight with warm cinematic boardroom lighting"),
        ("Pantry lounge tầng cao", "Pantry lounge tầng cao kết hợp quầy nước với chỗ ngồi thư giãn nhìn ra thành phố. Đây là tiện ích giữ chân khách thuê văn phòng cao cấp và tạo khoảng nghỉ có chất lượng trong ngày làm việc.", "an upper floor pantry lounge with coffee bar, banquette seating, skyline windows, stone counter, brass shelving", "late afternoon skyline daylight and warm pendant lighting"),
        ("Khu dự án bảo mật", "Khu dự án bảo mật dành cho nhóm làm việc với hồ sơ nhạy cảm hoặc chiến dịch quan trọng. Vách kính mờ, bàn nhóm và tủ khóa giúp kiểm soát truy cập mà vẫn giữ tinh thần cộng tác.", "a secure project war room with clustered desks, frosted glass walls, lockable storage, wall planning boards", "even task lighting with muted daylight through frosted glass"),
        ("Phòng tiếp khách VIP", "Phòng tiếp khách VIP hỗ trợ cuộc gặp riêng trước hoặc sau các phiên họp lớn. Không gian mềm hơn phòng họp, có ghế lounge, bàn thấp và tủ trưng bày để tạo cảm giác tin cậy cho đối tác.", "a VIP client lounge with lounge chairs, low stone table, display shelving, warm wood wall, glass skyline backdrop", "soft daylight and warm hospitality lighting"),
    ],
]


RESIDENTIAL_CYCLES = [
    [
        ("Căn hộ góc gia đình", "Căn hộ góc nhận ánh sáng từ hai hướng, phù hợp cư dân cao cấp cần phòng khách thoáng và góc ăn riêng. Bố cục ưu tiên tầm nhìn thành phố, vật liệu ấm và cảm giác yên tĩnh sau khối văn phòng bên dưới.", "a premium corner apartment living and dining room with two sided city views, warm oak millwork, soft neutral sofa, glass balcony doors", "high floor daylight and warm residential ambient lighting"),
        ("Căn hộ một phòng ngủ", "Căn hộ một phòng ngủ dành cho chuyên gia trẻ hoặc khách thuê dài hạn cần không gian gọn nhưng đủ tiện nghi. Phòng khách liên thông bếp nhỏ giúp tối ưu diện tích mà vẫn giữ cảm giác cao cấp.", "a refined one bedroom apartment living area with compact kitchen, oak cabinetry, stone backsplash, soft sofa, city window", "gentle daylight through full height windows and warm cove lighting"),
        ("Studio cao cấp", "Studio cao cấp phù hợp người ở một mình, khách công tác dài hạn hoặc cư dân muốn pied-a-terre trong trung tâm. Không gian cần thông minh, có giường gấp gọn, bàn làm việc và khu bếp nhỏ đồng bộ.", "a premium studio apartment with integrated bed nook, compact work desk, small kitchen wall, warm wood storage, glass city window", "soft morning daylight and warm concealed lighting"),
        ("Phòng kỹ thuật căn hộ", "Phòng kỹ thuật tầng căn hộ chứa tủ điện nhẹ, hệ thống thông gió và lối tiếp cận bảo trì. Không gian được giữ sạch, có nhãn thiết bị rõ để vận hành ổn định mà không ảnh hưởng trải nghiệm cư dân.", "a clean residential floor service room with electrical cabinets, ventilation equipment, labeled access panels, durable light stone floor", "bright neutral maintenance lighting"),
        ("Căn hộ góc panorama", "Căn hộ góc panorama nhấn mạnh trải nghiệm nhìn rộng trên cao, phù hợp nhóm cư dân ưu tiên chất lượng sống và sự riêng tư. Khu sinh hoạt chung mở ra cửa kính lớn, tạo cảm giác sang trọng nhưng không phô trương.", "a panoramic corner apartment lounge with wraparound city windows, low sofa, warm oak media wall, dining nook, muted blue textiles", "golden hour daylight and warm indirect residential lighting"),
        ("Căn hộ tiêu chuẩn tiện nghi", "Căn hộ tiêu chuẩn được bố trí hiệu quả cho cư dân làm việc tại tháp hoặc khu trung tâm. Các vùng ngủ, bếp và làm việc nhỏ được phân chia bằng nội thất thay vì tường nặng, giúp phòng thoáng hơn.", "a compact high end apartment living space with sofa bed, small dining table, integrated kitchen, oak shelves, glass facade", "clean daylight with warm ceiling cove lighting"),
    ],
    [
        ("Căn hộ wellness góc", "Căn hộ góc wellness dành cho cư dân muốn không gian nghỉ ngơi nhẹ nhàng hơn, có góc đọc sách và cây xanh gần cửa kính. Vật liệu gỗ, đá sáng và vải trung tính giúp căn hộ liên kết với phong cách chung của Aurora.", "a wellness focused corner apartment with reading chair, indoor planters, soft sofa, warm oak cabinetry, panoramic glass windows", "diffused daylight and warm calm residential lighting"),
        ("Căn hộ chuyên gia", "Căn hộ chuyên gia cân bằng giữa sinh hoạt và làm việc tại nhà. Bàn làm việc sát cửa sổ, kệ lưu trữ kín và bếp nhỏ gọn giúp không gian phục vụ tốt lịch làm việc linh hoạt của khách thuê cao cấp.", "a professional one bedroom apartment with window work desk, compact kitchen, storage wall, refined sofa, warm wood and glass finishes", "clear high floor daylight and soft task lighting"),
        ("Studio làm việc tại nhà", "Studio này được tối ưu cho cư dân thường xuyên làm việc từ xa. Góc làm việc có ánh sáng tự nhiên, mảng tường yên tĩnh cho video call và nội thất gọn để căn phòng không bị chật.", "a work from home studio apartment with a dedicated desk, video call backdrop wall, compact bed, small kitchen, oak storage", "bright daylight at the desk and warm ambient lighting"),
        ("Phòng vận hành cư dân", "Phòng vận hành cư dân hỗ trợ bảo trì, kiểm tra thiết bị và lưu dụng cụ cho tầng. Cách tổ chức rõ ràng giúp đội quản lý xử lý sự cố nhanh mà không phải đưa thiết bị qua khu ở chính quá nhiều.",
            "a tidy residential operations room with tool cabinets, service sink, utility shelves, labeled mechanical panels", "neutral task lighting with clean white ceiling fixtures"),
        ("Căn hộ góc sang trọng", "Căn hộ góc sang trọng có khu tiếp khách rộng hơn, phù hợp cư dân thường mời đối tác hoặc gia đình đến thăm. Phòng dùng tông gỗ ấm, đá sáng và điểm nhấn xanh lam để giữ đồng bộ với nhận diện tòa nhà.", "a luxury corner apartment living room with larger seating group, stone coffee table, oak feature wall, glass skyline corners", "late afternoon daylight and warm layered residential lighting"),
        ("Căn hộ một phòng ngủ mở", "Căn hộ một phòng ngủ mở nhấn mạnh sự liền mạch giữa bếp, bàn ăn và phòng khách. Đây là sản phẩm dễ cho thuê nhờ diện tích vừa phải, cảm giác sáng và phong cách phù hợp nhiều nhóm cư dân.", "an open plan one bedroom apartment with kitchen island, dining table, soft sofa, warm oak and muted blue accents, city window", "soft daylight and warm under cabinet lighting"),
    ],
    [
        ("Sky residence góc", "Sky residence ở tầng cao tạo cảm giác riêng tư hơn các tầng căn hộ thông thường. Cửa kính lớn, khu ngồi thấp và vật liệu yên tĩnh làm nổi bật tầm nhìn, phù hợp cư dân cao cấp hoặc khách mua để đầu tư dài hạn.", "a high floor sky residence corner living room with expansive skyline glass, low sectional sofa, oak wall panels, stone fireplace feature", "crisp high altitude daylight and warm indirect lighting"),
        ("Suite một phòng ngủ tầng cao", "Suite một phòng ngủ tầng cao dành cho cư dân muốn tiêu chuẩn hoàn thiện tốt hơn và trải nghiệm khách sạn trong căn hộ. Không gian có bếp gọn, bàn ăn nhỏ và góc thư giãn hướng ra đường chân trời.", "a high floor one bedroom suite with compact luxury kitchen, small dining setting, lounge chair by skyline window, brass details", "clear skyline daylight with warm hotel style lighting"),
        ("Studio sky view", "Studio sky view tập trung vào cảm giác mở dù diện tích nhỏ. Giường, bàn làm việc và bếp được đặt theo trục nhìn ra cửa kính để căn phòng có chiều sâu và phù hợp khách thuê thường xuyên di chuyển.", "a sky view studio apartment with bed alcove, slim work desk, compact kitchen, full height window, warm oak storage", "bright high floor daylight and soft warm ceiling glow"),
        ("Phòng kỹ thuật tầng cao", "Phòng kỹ thuật tầng cao kiểm soát các hệ thống phục vụ khu căn hộ phía trên. Không gian ưu tiên lối tiếp cận rõ, bề mặt bền và ánh sáng đủ mạnh cho đội vận hành làm việc an toàn.", "a high rise residential mechanical service room with organized equipment cabinets, access panels, ventilation grilles, clean stone floor", "bright neutral maintenance lighting"),
        ("Căn hộ góc sky lounge", "Căn hộ góc sky lounge có phòng khách mở rộng như một lounge riêng nhìn ra thành phố. Thiết kế phù hợp nhóm cư dân cao cấp cần không gian tiếp khách sang trọng nhưng vẫn ấm và có tính ở thực.", "a corner apartment sky lounge with wraparound windows, lounge seating, oak bar cabinet, stone sideboard, muted blue rug", "golden skyline daylight with warm dimmable lounge lights"),
        ("Căn hộ executive", "Căn hộ executive phục vụ cư dân quản lý cấp cao hoặc khách thuê dài hạn của doanh nghiệp. Bố cục có khu làm việc nhỏ, bếp sạch và sofa thoải mái để chuyển đổi giữa nghỉ ngơi và công việc.", "an executive apartment living space with small work nook, refined kitchen, tailored sofa, oak shelving, glass city backdrop", "soft daylight and warm residential task lighting"),
    ],
]


PENTHOUSE_PLAN = [
    (
        "Penthouse lounge T30-01",
        "Penthouse lounge là không gian đại diện ở tầng cao nhất, mở ra tầm nhìn rộng cho cư dân cao cấp và các buổi tiếp khách riêng. Vật liệu gỗ ấm, đá sáng và chi tiết kim loại nhẹ tạo cảm giác sang trọng nhưng vẫn thống nhất với toàn bộ Aurora.",
        "a penthouse corner lounge with panoramic skyline glazing, deep sectional sofa, stone feature wall, oak millwork, brushed brass accents",
        "dramatic high floor daylight with warm layered evening lighting",
    ),
    (
        "Penthouse dining T30-02",
        "Khu dining penthouse phục vụ bữa ăn riêng tư và tiếp khách thân mật. Bàn ăn lớn đặt gần cửa kính, bếp phụ gọn và ánh sáng ấm giúp không gian vừa cao cấp vừa có tính sử dụng hằng ngày.",
        "a penthouse dining room with a long oak dining table, stone sideboard, compact show kitchen, skyline windows, brass pendant lights",
        "golden hour daylight and warm pendant lighting",
    ),
    (
        "Penthouse studio T30-03",
        "Studio phụ trong penthouse có thể dùng làm phòng làm việc, phòng đọc hoặc nơi nghỉ cho khách. Không gian nhỏ nhưng hoàn thiện kỹ, có bàn sát kính và hệ tủ âm để giữ mặt bằng gọn.",
        "a penthouse private study studio with a window desk, built in oak shelves, daybed, muted blue chair, glass skyline view",
        "clear high floor daylight with soft task lamp lighting",
    ),
    (
        "Phòng kỹ thuật penthouse T30-04",
        "Phòng kỹ thuật penthouse hỗ trợ điều hòa, điện nhẹ và thiết bị cho tầng đỉnh. Tổ chức sạch, nhãn rõ và lối đi đủ rộng giúp bảo trì nhanh mà không ảnh hưởng khu ở cao cấp.",
        "a clean penthouse service room with mechanical cabinets, labeled panels, storage racks, durable stone floor, tidy maintenance layout",
        "bright neutral service lighting",
    ),
    (
        "Penthouse master suite T30-05",
        "Master suite là phòng nghỉ chính của penthouse, nhấn mạnh sự riêng tư và tầm nhìn đẹp. Khu ngồi nhỏ, vách đầu giường gỗ và vật liệu vải mềm tạo chất lượng sống cao cho cư dân tầng đỉnh.",
        "a penthouse master suite with king bed, lounge chair, oak headboard wall, soft textiles, wraparound skyline glass",
        "soft sunset daylight with warm concealed bedroom lighting",
    ),
    (
        "Penthouse guest suite T30-06",
        "Guest suite hoàn thiện như một phòng khách sạn nhỏ để tiếp đón gia đình hoặc đối tác lưu trú. Bố cục có giường, bàn làm việc nhỏ và tủ âm, giữ tiện nghi đầy đủ nhưng không lấn át master suite.",
        "a penthouse guest suite with queen bed, compact desk, built in wardrobe, warm oak finishes, clear city window",
        "gentle daylight with warm hotel style ambient lighting",
    ),
]


def panorama_prompt(detail: str, lighting: str) -> str:
    return (
        f"360 equirectangular interior panorama of {detail}, {STYLE}, "
        f"{lighting}, photorealistic, wide angle, no people"
    )


def office_plan(floor_number: int) -> list[tuple[str, str, str, str]]:
    plan = OFFICE_CYCLES[(floor_number - 4) % len(OFFICE_CYCLES)]
    enriched: list[tuple[str, str, str, str]] = []
    for slot, (base_name, description, detail, lighting) in enumerate(plan, start=1):
        name = f"{base_name} T{floor_number}-{slot:02d}"
        if floor_number in {10, 15, 20} and slot == 3:
            name = f"Phòng họp lớn T{floor_number}-{slot:02d}"
            description = (
                f"Phòng họp lớn tầng {floor_number} phục vụ các buổi trình bày quan trọng với khách thuê văn phòng, nhà đầu tư và ban quản lý tòa nhà. "
                "Không gian có tỷ lệ trang trọng, xử lý âm học tốt và tầm nhìn cao để nâng chất lượng các cuộc họp chiến lược."
            )
            detail = "a large high rise executive conference room with a long oak table, premium task chairs, panoramic glass, acoustic wood panels, integrated media wall"
            lighting = "controlled daylight with warm dimmable conference lighting"
        if floor_number in {12, 18} and slot == 4:
            name = f"Lounge cộng đồng T{floor_number}-{slot:02d}"
            description = (
                f"Lounge cộng đồng tầng {floor_number} là tiện ích mềm cho khách thuê văn phòng gặp gỡ, nghỉ ngắn hoặc làm việc ngoài bàn chính. "
                "Khu này giúp tăng giá trị cho thuê nhờ tạo trải nghiệm văn phòng cao cấp, thân thiện và có khả năng kết nối giữa các tenant."
            )
            detail = "a shared office community lounge with sofas, cafe counter, planter islands, warm wood shelves, skyline windows"
            lighting = "soft daylight and warm hospitality lighting"
        enriched.append((name, description, detail, lighting))
    return enriched


def residential_plan(floor_number: int) -> list[tuple[str, str, str, str]]:
    if floor_number == 30:
        return PENTHOUSE_PLAN
    plan = RESIDENTIAL_CYCLES[(floor_number - 21) % len(RESIDENTIAL_CYCLES)]
    enriched: list[tuple[str, str, str, str]] = []
    for slot, (base_name, description, detail, lighting) in enumerate(plan, start=1):
        label = f"T{floor_number}-{slot:02d}"
        name = f"{base_name} {label}"
        if floor_number in {28, 29} and slot in {1, 5}:
            name = f"Sky residence premium {label}"
            description = (
                f"Sky residence premium tầng {floor_number} hướng tới cư dân cao cấp muốn tầm nhìn rộng, chất lượng hoàn thiện tốt và sự riêng tư rõ rệt. "
                "Không gian sinh hoạt mở, vật liệu ấm và cửa kính lớn giúp sản phẩm nổi bật trong danh mục căn hộ phía trên của Aurora."
            )
            detail = "a premium sky residence living room with wide skyline glass, refined sectional sofa, oak and stone feature walls, brass details, muted blue textiles"
            lighting = "clear high altitude daylight with warm layered residential lighting"
        enriched.append((name, description, detail, lighting))
    return enriched


def plan_for_floor(floor_number: int) -> list[tuple[str, str, str, str]]:
    if floor_number <= 3:
        return RETAIL_PLANS[floor_number]
    if floor_number <= 20:
        return office_plan(floor_number)
    return residential_plan(floor_number)


def update_describer(bundle: dict[str, Any]) -> None:
    bundle["describer"] = {
        "title": "Aurora Mixed-Use Tower - Phức hợp bán lẻ, văn phòng và căn hộ cao cấp 30 tầng",
        "summary": (
            "Aurora Mixed-Use Tower là phức hợp 30 tầng tổ chức theo ba lớp công năng rõ ràng: khối đế bán lẻ và F&B ở tầng 1 đến 3, "
            "khối văn phòng linh hoạt ở tầng 4 đến 20, và khối căn hộ cao cấp ở tầng 21 đến 30. "
            "Nội dung phòng được làm giàu theo từng tầng để nhà đầu tư, khách thuê văn phòng và cư dân cao cấp có thể đọc được vai trò vận hành, "
            "trải nghiệm không gian và tiềm năng khai thác của từng khu vực trong cùng một mô hình 3D."
        ),
        "highlights": [
            "Ba tầng thương mại tạo mặt tiền hoạt động sôi động, có cafe, food hall, showroom và khu hậu cần riêng.",
            "Mười bảy tầng văn phòng được biến thiên giữa sảnh tenant, khu làm việc mở, phòng họp lớn, lounge và không gian dự án bảo mật.",
            "Mười tầng căn hộ phía trên nhấn mạnh tầm nhìn, sự riêng tư và các biến thể sky residence, suite, studio và penthouse.",
            "Tất cả phòng có prompt 360 tiếng Anh đồng bộ phong cách hiện đại tối giản với gỗ ấm, kính, đá sáng và điểm nhấn xanh lam.",
            "Room id, số phòng, hình học và GLB được giữ nguyên để không phá vỡ viewer hoặc node mapping hiện tại.",
        ],
        "digitization_tips": [
            "Khi sinh panorama ở phase sau, dùng đúng đường dẫn theo room id để giữ liên kết giữa cây cấu trúc và ảnh 360.",
            "Ưu tiên kiểm tra các tầng chuyển công năng 3, 4, 20, 21 và 30 vì nội dung trải nghiệm thay đổi mạnh tại các điểm này.",
            "Giữ cùng bảng vật liệu và ánh sáng trong prompt để các ảnh 360 trông như cùng một công trình, dù công năng phòng khác nhau.",
        ],
    }


def scrub_em_dash(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(EM_DASH, "-")
    if isinstance(value, list):
        return [scrub_em_dash(item) for item in value]
    if isinstance(value, dict):
        return {key: scrub_em_dash(item) for key, item in value.items()}
    return value


def count_em_dash(value: Any) -> int:
    if isinstance(value, str):
        return value.count(EM_DASH)
    if isinstance(value, list):
        return sum(count_em_dash(item) for item in value)
    if isinstance(value, dict):
        return sum(count_em_dash(item) for item in value.values())
    return 0


def collect_room_ids(bundle: dict[str, Any]) -> list[str]:
    floors = bundle.get("structure", {}).get("floors", [])
    return [room["id"] for floor in floors for room in floor.get("rooms", [])]


def enrich(bundle: dict[str, Any]) -> dict[str, Any]:
    before_ids = collect_room_ids(bundle)
    before_counts = [len(floor.get("rooms", [])) for floor in bundle["structure"]["floors"]]

    update_describer(bundle)

    for floor in bundle["structure"]["floors"]:
        floor_number = floor["index"] + 1
        floor["name"] = f"Tầng {floor_number}"
        plan = plan_for_floor(floor_number)
        if len(plan) != len(floor["rooms"]):
            raise ValueError(f"Floor {floor_number} has {len(floor['rooms'])} rooms but plan has {len(plan)} entries")

        for room, (name, description, detail, lighting) in zip(floor["rooms"], plan):
            room["name"] = name
            room["description"] = description
            panorama = room.setdefault("panorama", {})
            panorama["prompt"] = panorama_prompt(detail, lighting)
            panorama["image"] = ""
            panorama["status"] = "pending"

    bundle = scrub_em_dash(bundle)

    after_ids = collect_room_ids(bundle)
    after_counts = [len(floor.get("rooms", [])) for floor in bundle["structure"]["floors"]]
    if before_ids != after_ids:
        raise ValueError("Room ids changed during enrichment")
    if before_counts != after_counts:
        raise ValueError("Room counts changed during enrichment")
    if count_em_dash(bundle) != 0:
        raise ValueError("Artifact still contains em-dash characters")

    for floor in bundle["structure"]["floors"]:
        for room in floor["rooms"]:
            if not room.get("description", "").strip():
                raise ValueError(f"Missing description for {room['id']}")
            prompt = room.get("panorama", {}).get("prompt", "")
            if not prompt.strip():
                raise ValueError(f"Missing panorama prompt for {room['id']}")
            if not prompt.startswith("360 equirectangular interior panorama of "):
                raise ValueError(f"Prompt format mismatch for {room['id']}")
            if room.get("panorama", {}).get("image") != "":
                raise ValueError(f"Panorama image should remain empty for {room['id']}")
            if room.get("panorama", {}).get("status") != "pending":
                raise ValueError(f"Panorama status should remain pending for {room['id']}")

    SceneBundle.model_validate(bundle)
    return bundle


def main() -> None:
    with ARTIFACT.open("r", encoding="utf-8") as fh:
        bundle = json.load(fh)

    enriched = enrich(bundle)

    with ARTIFACT.open("w", encoding="utf-8") as fh:
        json.dump(enriched, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    room_count = len(collect_room_ids(enriched))
    print(f"Enriched {ARTIFACT.relative_to(ROOT)} with {room_count} rooms.")


if __name__ == "__main__":
    main()
