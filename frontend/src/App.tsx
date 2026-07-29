import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'

const linkCard =
  'flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-slate-950 transition-shadow hover:shadow-[0_10px_15px_-3px_rgba(15,23,42,0.1),0_4px_6px_-2px_rgba(15,23,42,0.05)]'

function App() {
  const [count, setCount] = useState(0)

  return (
    <main className="flex min-h-screen flex-col bg-white text-slate-700">
      <section className="flex flex-1 flex-col items-center justify-center gap-6 px-5 py-8 text-center lg:gap-8">
        <div className="relative isolate">
          <img
            src={heroImg}
            className="relative z-0 mx-auto w-[170px]"
            width="170"
            height="179"
            alt=""
          />
          <img
            src={reactLogo}
            className="absolute left-1/2 top-[34px] z-10 h-7 -translate-x-1/2 [transform:perspective(2000px)_rotateZ(300deg)_rotateX(44deg)_rotateY(39deg)_scale(1.4)]"
            alt="React logo"
          />
          <img
            src={viteLogo}
            className="absolute left-1/2 top-[107px] z-0 h-[26px] w-auto -translate-x-1/2 [transform:perspective(2000px)_rotateZ(300deg)_rotateX(40deg)_rotateY(39deg)_scale(0.8)]"
            alt="Vite logo"
          />
        </div>

        <div className="space-y-2">
          <h1 className="text-4xl font-medium tracking-[-0.04em] text-slate-950 lg:text-6xl">
            Get started
          </h1>
          <p className="text-base lg:text-lg">
            Edit <code className="rounded bg-amber-50 px-2 py-1">src/App.tsx</code> and save to test{' '}
            <code className="rounded bg-amber-50 px-2 py-1">HMR</code>
          </p>
        </div>

        <button
          type="button"
          className="rounded-md border-2 border-transparent bg-violet-50 px-3 py-1.5 text-base text-violet-600 transition hover:border-violet-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500"
          onClick={() => setCount((value) => value + 1)}
        >
          Count is {count}
        </button>
      </section>

      <div className="relative w-full before:absolute before:left-0 before:top-[-4.5px] before:border-[5px] before:border-transparent before:border-l-slate-200 after:absolute after:right-0 after:top-[-4.5px] after:border-[5px] after:border-transparent after:border-r-slate-200" />

      <section className="grid border-t border-slate-200 text-left lg:grid-cols-2">
        <div className="border-b border-slate-200 p-5 lg:border-b-0 lg:border-r lg:p-8">
          <svg className="mb-4 h-[22px] w-[22px]" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg>
          <h2 className="mb-2 text-xl font-medium tracking-[-0.01em] text-slate-950 lg:text-2xl">
            Documentation
          </h2>
          <p>Your questions, answered</p>
          <ul className="mt-8 flex flex-wrap gap-2 p-0">
            <li>
              <a href="https://vite.dev/" target="_blank" rel="noreferrer" className={linkCard}>
                <img className="h-[18px]" src={viteLogo} alt="" />
                Explore Vite
              </a>
            </li>
            <li>
              <a href="https://react.dev/" target="_blank" rel="noreferrer" className={linkCard}>
                <img className="h-[18px] w-[18px]" src={reactLogo} alt="" />
                Learn more
              </a>
            </li>
          </ul>
        </div>

        <div className="p-5 lg:p-8">
          <svg className="mb-4 h-[22px] w-[22px]" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2 className="mb-2 text-xl font-medium tracking-[-0.01em] text-slate-950 lg:text-2xl">
            Connect with us
          </h2>
          <p>Join the Vite community</p>
          <ul className="mt-8 flex flex-wrap gap-2 p-0">
            <li>
              <a href="https://github.com/vitejs/vite" target="_blank" rel="noreferrer" className={linkCard}>
                <svg className="h-[18px] w-[18px]" role="presentation" aria-hidden="true">
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            <li>
              <a href="https://chat.vite.dev/" target="_blank" rel="noreferrer" className={linkCard}>
                <svg className="h-[18px] w-[18px]" role="presentation" aria-hidden="true">
                  <use href="/icons.svg#discord-icon"></use>
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank" rel="noreferrer" className={linkCard}>
                <svg className="h-[18px] w-[18px]" role="presentation" aria-hidden="true">
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank" rel="noreferrer" className={linkCard}>
                <svg className="h-[18px] w-[18px]" role="presentation" aria-hidden="true">
                  <use href="/icons.svg#bluesky-icon"></use>
                </svg>
                Bluesky
              </a>
            </li>
          </ul>
        </div>
      </section>

      <div className="h-[88px] border-t border-slate-200 lg:h-12" />
    </main>
  )
}

export default App
