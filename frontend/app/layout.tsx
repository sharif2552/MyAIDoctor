import "./globals.css";
import type { Metadata, Viewport } from "next";
import MedicalShaderBackground from "@/components/MedicalShaderBackground";

export const metadata: Metadata = {
  title: "MyAIDoctor",
  description: "AI diagnostic assistant",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <MedicalShaderBackground />
        <main className="app-shell">{children}</main>
      </body>
    </html>
  );
}
