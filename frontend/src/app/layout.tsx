import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import Template from "@/components/Template";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BL Genius - Football Analysis AI",
  description: "Analyse intelligente de matchs de football par IA. Détection automatique des joueurs, tracking du ballon et statistiques avancées.",
  keywords: ["football", "analysis", "AI", "YOLO", "computer vision", "tracking"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body
        className={`${geistSans.variable} ${geistSans.variable} antialiased min-h-screen relative`}
      >
        <AuthProvider>
          <Template>
            <div className="relative z-10">{children}</div>
          </Template>
        </AuthProvider>
      </body>
    </html>
  );
}
