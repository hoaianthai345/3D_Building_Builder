import Link from "next/link";
import { CubeIcon } from "@phosphor-icons/react/dist/ssr";
import { ButtonLink } from "./ui";

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg)]/85 backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-5">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent-strong)] text-white">
            <CubeIcon size={18} weight="bold" />
          </span>
          <span className="serif text-lg font-semibold">Scene Describer</span>
        </Link>

        <div className="hidden items-center gap-7 md:flex">
          <Link href="/#how" className="text-sm text-[var(--text-muted)] hover:text-[var(--text)]">
            Cách hoạt động
          </Link>
          <Link href="/#output" className="text-sm text-[var(--text-muted)] hover:text-[var(--text)]">
            AI tạo ra gì
          </Link>
          <Link href="/demo" className="text-sm text-[var(--text-muted)] hover:text-[var(--text)]">
            Demo
          </Link>
        </div>

        <ButtonLink href="/demo">Mở demo</ButtonLink>
      </nav>
    </header>
  );
}
