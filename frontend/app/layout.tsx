import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeApplicator } from "./components/ThemeApplicator";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "RAVEN AI — AI Business Development Agent",
  description:
    "AI-powered outbound business development & narrative platform for Rayven Strategic Communications",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <ThemeApplicator>{children}</ThemeApplicator>
      </body>
    </html>
  );
}
