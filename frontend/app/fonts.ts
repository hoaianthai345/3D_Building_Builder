import { Lora, Be_Vietnam_Pro } from "next/font/google";

// Serif display (editorial, warm) — Vietnamese diacritics supported.
export const serif = Lora({
  subsets: ["vietnamese", "latin"],
  weight: ["500", "600"],
  variable: "--font-serif",
  display: "swap",
});

// Body / UI — purpose-built for Vietnamese, clean grotesque.
export const sans = Be_Vietnam_Pro({
  subsets: ["vietnamese", "latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});
