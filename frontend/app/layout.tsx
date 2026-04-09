import "./globals.css";
import type { Metadata } from "next";
import MedicalShaderBackground from "@/components/MedicalShaderBackground";

export const metadata: Metadata = {
  title: "MyAIDoctor",
  description: "AI diagnostic assistant"
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
