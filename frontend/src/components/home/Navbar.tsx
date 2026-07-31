function NavIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
      <path
        d="M7 7.5C7 6.12 8.12 5 9.5 5h5C15.88 5 17 6.12 17 7.5v5c0 1.38-1.12 2.5-2.5 2.5h-5C8.12 15 7 13.88 7 12.5v-5Z"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path d="M9 18h6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

export function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <NavIcon className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="text-[15px] font-semibold text-slate-950">PromptLens</div>
            <div className="text-xs text-slate-500">Screenshot prompt extraction</div>
          </div>
        </div>

        <nav className="flex items-center gap-2 text-sm">
          <a
            href="#extract"
            className="rounded-full bg-blue-50 px-4 py-2 font-medium text-blue-700 transition hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            Extract
          </a>
          <span aria-disabled="true" className="rounded-full px-4 py-2 font-medium text-slate-400">
            History
          </span>
        </nav>
      </div>
    </header>
  )
}
