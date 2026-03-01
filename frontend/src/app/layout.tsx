import type { Metadata } from "next";

import Navbar from "@/components/Navbar";

import "./globals.css";

export const metadata: Metadata = {
  title: "LearnStral",
  description: "Generate lesson videos from PDFs across all subjects",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="page-bg">
          <div className="app-frame">
            <Navbar />
            <main className="inner-page">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
