export function StepCard({
  number,
  title,
  description,
}: {
  number: string
  title: string
  description: string
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="text-xs font-medium tracking-[0.24em] text-slate-400">{number}</div>
      <h3 className="mt-8 text-base font-medium text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </article>
  )
}
