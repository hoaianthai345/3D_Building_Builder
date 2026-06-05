import Link from "next/link";
import type { ReactNode } from "react";

// Shared primitives. One radius system: cards 16px, buttons/inputs 10px, badges pill.

export function ButtonLink({
  href,
  children,
  variant = "primary",
  className = "",
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
  className?: string;
}) {
  const base =
    "inline-flex h-11 items-center justify-center rounded-[10px] px-5 text-sm font-medium transition active:translate-y-[1px]";
  const styles =
    variant === "primary"
      ? "bg-[var(--accent-strong)] text-white hover:bg-[var(--accent-hover)] shadow-[var(--shadow-sm)]"
      : "border border-[var(--border-strong)] text-[var(--text)] hover:bg-[var(--bg-subtle)]";
  return (
    <Link href={href} className={`${base} ${styles} ${className}`}>
      {children}
    </Link>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-[var(--border)] bg-[var(--surface)] ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-medium text-[var(--accent-hover)]">
      {children}
    </span>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent-hover)]">
      {children}
    </p>
  );
}
