import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner"; // 👈 1. 引入组件

export const metadata: Metadata = {
  title: "PUBG Weapon System",
  description: "Tactical Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark"> 
      <body>
        {children}
        <Toaster /> {/* 👈 2. 放在这里 */}
      </body>
    </html>
  );
}