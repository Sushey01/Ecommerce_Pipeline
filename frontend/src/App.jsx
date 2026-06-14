import { useState, useEffect } from 'react'
import {
  LayoutDashboard, MousePointerClick, BarChart2,
  TrendingUp, ExternalLink, Activity
} from 'lucide-react'
import Overview from './components/Overview.jsx'
import Predictor from './components/Predictor.jsx'
import MonitoringFrame from './components/MonitoringFrame.jsx'
import DriftFrame from './components/DriftFrame.jsx'

const NAV = [
  { id: 'overview',   label: 'Overview',           icon: LayoutDashboard },
  { id: 'predictor',  label: 'Ad Click Predictor',  icon: MousePointerClick },
  { id: 'monitoring', label: 'Monitoring',           icon: BarChart2 },
  { id: 'drift',      label: 'Drift Report',          icon: TrendingUp },
]

const EXTERNAL = [
  { label: 'Airflow UI',  href: 'http://localhost:8081', emoji: '🌀' },
  { label: 'MLflow UI',   href: 'http://localhost:5002', emoji: '🧪' },
  { label: 'API Docs',    href: '/docs',                 emoji: '📄' },
]

export default function App() {
  const [page, setPage]       = useState('overview')
  const [apiStatus, setStatus] = useState('checking')   // 'online' | 'offline' | 'checking'

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/health', { signal: AbortSignal.timeout(4000) })
        setStatus(res.ok ? 'online' : 'offline')
      } catch { setStatus('offline') }
    }
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [])

  const dotColor =
    apiStatus === 'online'   ? 'bg-emerald-400 animate-pulse-dot' :
    apiStatus === 'offline'  ? 'bg-rose-500' : 'bg-amber-400'

  const statusText =
    apiStatus === 'online'   ? 'API Online' :
    apiStatus === 'offline'  ? 'API Offline' : 'Checking…'

  return (
    <div className="flex min-h-screen bg-[#07090f] font-sans">

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="fixed top-0 left-0 bottom-0 w-60 flex flex-col
                        bg-slate-900 border-r border-white/[0.07] z-50">

        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/[0.07]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg
                            bg-gradient-to-br from-cyan-400 to-violet-600 flex-shrink-0">
              🛒
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-700 text-slate-100 font-bold">MLOps Pipeline</span>
              <span className="text-[0.65rem] text-slate-500">E-Commerce · Ad Click</span>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2.5 py-4 flex flex-col gap-0.5 overflow-y-auto">
          <span className="text-[0.6rem] font-semibold text-slate-600 uppercase tracking-widest px-2.5 pb-1">
            Navigation
          </span>

          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setPage(id)}
              className={`
                relative flex items-center gap-2.5 w-full px-3 py-2.5 rounded-lg
                text-sm font-medium transition-all duration-150 text-left cursor-pointer
                ${page === id
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200 border border-transparent'}
              `}
            >
              {page === id && (
                <span className="absolute left-0 top-1/4 bottom-1/4 w-[3px]
                                 bg-cyan-400 rounded-r-full" />
              )}
              <Icon size={15} />
              {label}
            </button>
          ))}

          <span className="text-[0.6rem] font-semibold text-slate-600 uppercase tracking-widest px-2.5 pb-1 mt-4">
            External
          </span>

          {EXTERNAL.map(({ label, href, emoji }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm
                         text-slate-400 hover:bg-white/[0.05] hover:text-slate-200
                         transition-all duration-150 border border-transparent"
            >
              <span className="text-base leading-none">{emoji}</span>
              {label}
              <ExternalLink size={10} className="ml-auto opacity-40" />
            </a>
          ))}
        </nav>

        {/* Footer status */}
        <div className="px-3 py-3 border-t border-white/[0.07]">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg
                          bg-white/[0.03] border border-white/[0.06]">
            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
            <span className="text-xs text-slate-400">{statusText}</span>
            <Activity size={11} className="ml-auto text-slate-600" />
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────── */}
      <main className="ml-60 flex-1 flex flex-col min-h-screen">
        {page === 'overview'   && <Overview   apiStatus={apiStatus} onNavigate={setPage} />}
        {page === 'predictor'  && <Predictor />}
        {page === 'monitoring' && <MonitoringFrame />}
        {page === 'drift'      && <DriftFrame />}
      </main>
    </div>
  )
}
