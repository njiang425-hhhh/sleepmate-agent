import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SleepMate Agent",
  description: "AI 助眠助手",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
