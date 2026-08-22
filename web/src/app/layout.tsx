import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Survivor",
  description: "One NFL team a week. Never twice. Last one standing wins.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Survivor",
    // Transparent bar so our own header paints under the status bar.
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: "/icon.svg",
    apple: "/apple-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#08090c",
  width: "device-width",
  initialScale: 1,
  // Installed-app feel: no pinch-zoom bounce, and the layout extends
  // under the notch and home indicator (we pad with safe-area insets).
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-bg text-body">{children}</body>
    </html>
  );
}
