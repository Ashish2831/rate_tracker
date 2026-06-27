/** Root layout — global styles, metadata, and HTML shell. */

import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rate Tracker",
  description: "Live interest rate comparison dashboard — latest rates and 30-day history by provider.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
