import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/auth-context";

export const metadata: Metadata = {
  title: "AFFECTORYX — Engineering Intelligence Platform",
  description: "Deterministic change consequence analysis, dependency graph topology, and blast radius simulation for software engineering teams.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-[#0b0f17] text-gray-100">
      <body className="min-h-screen bg-[#0b0f17] text-gray-100 flex flex-col font-sans">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
