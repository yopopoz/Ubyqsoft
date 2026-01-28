import type { Metadata } from "next";
import { Gruppo } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const gruppo = Gruppo({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-gruppo",
});

export const metadata: Metadata = {
  title: "PURE TRADE | Logistique",
  description: "Tableau de bord logistique mondiale",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={gruppo.variable}>
      <body className={`${gruppo.className} antialiased`} suppressHydrationWarning>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
