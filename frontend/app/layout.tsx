import type { Metadata } from "next";
import { sans, serif } from "./fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 3D Scene Describer",
  description:
    "Dựng khối tòa nhà 3D từ thông số cơ bản và để AI viết tiêu đề, mô tả, điểm nổi bật cho nội dung số hóa.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${sans.variable} ${serif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
