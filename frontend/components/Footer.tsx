export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-2 px-5 py-10 text-sm text-[var(--text-muted)] sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="serif font-semibold text-[var(--text)]">AI Tour Guide Generator</span>
          {"  "}công cụ tạo tour 3D có thuyết minh AI.
        </p>
        <p className="text-[var(--text-faint)]">Bản demo nội bộ, 2026.</p>
      </div>
    </footer>
  );
}
