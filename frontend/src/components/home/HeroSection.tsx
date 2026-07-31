function Badge({ children }: { children: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
      {children}
    </span>
  )
}

export function HeroSection() {
  return (
    <section className="mx-auto max-w-3xl px-4 pt-12 text-center sm:px-6 lg:pt-14">
      <div className="flex justify-center">
        <Badge>Powered by PaddleOCR</Badge>
      </div>
      <h1 className="mt-5 text-balance text-4xl font-semibold tracking-[-0.05em] text-slate-950 sm:text-5xl lg:text-6xl">
        Extract AI prompts from screenshots
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-pretty text-base leading-7 text-slate-600 sm:text-lg">
        Upload screenshots from Instagram, Midjourney, ChatGPT, X, Reddit or anywhere else.
        PromptLens automatically extracts and cleans AI prompts.
      </p>
    </section>
  )
}
