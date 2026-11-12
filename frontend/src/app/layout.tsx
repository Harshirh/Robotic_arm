import type { Metadata } from "next";
import { RealtimeProvider } from "@/components/realtime/realtime-provider";
import "./globals.css";

export const metadata: Metadata = { title: "Circular Robotics | Control Center", description: "Industrial control center for a recycling robotic arm project." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><RealtimeProvider>{children}</RealtimeProvider></body></html>;
}
