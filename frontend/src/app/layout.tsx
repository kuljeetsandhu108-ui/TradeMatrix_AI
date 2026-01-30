import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css"; // This connects your beautiful dark theme

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TradeMatrix AI",
  description: "High-Frequency Algo Trading Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}