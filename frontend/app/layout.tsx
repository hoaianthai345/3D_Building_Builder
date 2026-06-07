import type { Metadata } from "next";
import { BackgroundMusic } from "@/components/BackgroundMusic";
import { sans, serif } from "./fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Tour Guide Generator",
  description:
    "Tạo tour tham quan 3D có lời dẫn AI, chỉnh sửa script và render giọng đọc hướng dẫn viên bằng VieNeu-TTS.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${sans.variable} ${serif.variable}`} suppressHydrationWarning>
      <body suppressHydrationWarning>
        {children}
        <BackgroundMusic />
      </body>
    </html>
  );
}
