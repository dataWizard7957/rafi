import "./globals.css";
import type { Metadata } from "next";
import Nav from "@/components/Nav";
import { DEMO } from "@/lib/demo";

export const metadata: Metadata = { title: "Rafi · Cedar & Date Market", description: "Your shop's AI crew" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="mx-auto max-w-7xl px-6 py-6">
          {DEMO && (
            <p className="mb-4 text-sm text-stone-500">
              Live demo with sample data.{" "}
              <a href="https://github.com/dataWizard7957/rafi" target="_blank" rel="noreferrer" className="font-medium text-cedar-700 hover:underline">
                Run it locally.
              </a>
            </p>
          )}
          {children}
        </main>
      </body>
    </html>
  );
}
