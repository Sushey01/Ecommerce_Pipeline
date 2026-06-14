import { useState, useEffect } from 'react'
import { RefreshCw, Server, Database, Cpu, ArrowRight, ExternalLink, MousePointerClick, BarChart2, TrendingUp } from 'lucide-react'

const PIPELINE_STEPS = [
  { icon: '📥', label: 'Extract',   desc: 'Kaggle API' },
  { icon: '🗄️', label: 'Load',      desc: 'MariaDB OBT' },
  { icon: '🔧', label: 'Transform', desc: 'OHE + Scaler' },
  { icon: '🎯', label: 'Tune',      desc: 'RandomizedCV' },
  { icon: '🤖', label: 'Train',     desc: 'Best Model' },
  { icon: '📊', label: 'Evaluate',  desc: 'Metrics + Plots' },
]

const SERVICE_LINKS = [
  { name: 'Airflow UI',     url: 'http://localhost:8081', desc: 'Orchestration & DAGs',      emoji: '🌀', color: 'from-sky-500/10 to-sky-600/5' },
  { name: 'MLflow UI',      url: 'http://localhost:5002', desc: 'Experiment tracking',        emoji: '🧪', color: 'from-violet-500/10 to-violet-600/5' },
  { name: 'API Docs',       url: '/docs',                 desc: 'Interactive Swagger UI',     emoji: '📄', color: 'from-emerald-500/10 to-emerald-600/5' },
  { name: 'MariaDB · 3310', url: null,                    desc: 'mlops_user / mlops_password', emoji: '🗄️', color: 'from-amber-500/10 to-amber-600/5' },
  { name: 'Redis · 6380',   url: null,                    desc: 'Cache + data bus',            emoji: '⚡', color: 'from-red-500/10 to-red-600/5' },
]

export default function Overview({ apiStatus, onNavigate }) {
  const [health, setHealth]   = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchHealth = async () => {
    setLoading(true)
    try {
      const res  = await fetch('/health', { signal: AbortSignal.timeout(5000) })
      const data = await res.json()
      setHealth(data)
    } catch { setHealth({ status: 'unreachable', redis: 'unknown' }) }
    finally   { setLoading(false) }
  }

  useEffect(() => { fetchHealth() }, [])

  const apiOk   = health?.status === 'healthy'
  const redisOk = health?.redis  === 'connected'

  const badge = (ok) =>
    ok === true  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' :
    ok === false ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' :
                   'text-amber-400 bg-amber-500/10 border-amber-500/20'

  const badgeLabel = (ok) => ok === true ? '● Online' : ok === false ? '● Offline' : '● N/A'

  const StatCard = ({ title, value, sub, ok, Icon }) => (
    <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-5
                    hover:bg-white/[0.06] hover:border-white/[0.13] transition-all duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-xl bg-white/[0.06] flex items-center justify-center">
          <Icon size={18} className="text-slate-400" />
        </div>
        <span className={`text-[0.7rem] font-semibold px-2.5 py-1 rounded-full border ${badge(ok)}`}>
          {badgeLabel(ok)}
        </span>
      </div>
      <p className="text-[0.65rem] text-slate-600 uppercase tracking-widest font-semibold mb-1">{title}</p>
      <p className="text-2xl font-bold text-slate-100">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      <div className="px-8 pt-8 pb-0">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-100">Overview</h1>
            <p className="text-sm text-slate-500 mt-1">System health, pipeline & service links</p>
          </div>
          <button onClick={fetchHealth} disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold
                       bg-white/[0.05] border border-white/[0.08] text-slate-400
                       hover:bg-white/[0.09] hover:text-slate-200 transition-all disabled:opacity-50">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="px-8 py-6 flex flex-col gap-7 overflow-y-auto">
        {/* Stat Cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard title="FastAPI"  value=":8005" sub="Inference + API"         ok={apiOk}     Icon={Server}   />
          <StatCard title="Redis"    value="Cache"  sub="Prediction + data bus"  ok={redisOk}   Icon={Cpu}      />
          <StatCard title="MLflow"   value=":5002"  sub="Experiment tracking"    ok={undefined} Icon={Database} />
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { id: 'predictor',  label: 'Ad Click Predictor', desc: 'Real-time inference with Redis caching', Icon: MousePointerClick, colors: 'from-cyan-500/10 border-cyan-500/20 hover:border-cyan-500/40', icolor: 'bg-cyan-500/15 text-cyan-400' },
            { id: 'monitoring', label: 'System Monitoring',  desc: 'Live metrics & Evidently drift reports',  Icon: BarChart2,         colors: 'from-violet-500/10 border-violet-500/20 hover:border-violet-500/40', icolor: 'bg-violet-500/15 text-violet-400' },
          ].map(({ id, label, desc, Icon, colors, icolor }) => (
            <button key={id} onClick={() => onNavigate(id)}
              className={`group flex items-center gap-4 p-5 rounded-2xl text-left
                          bg-gradient-to-br ${colors} to-transparent border
                          transition-all duration-200`}>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${icolor}`}>
                <Icon size={22} />
              </div>
              <div>
                <p className="font-bold text-slate-100 text-sm">{label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </div>
              <ArrowRight size={16} className="ml-auto text-slate-600 group-hover:translate-x-1 transition-transform" />
            </button>
          ))}
        </div>

        {/* Pipeline flow */}
        <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-6">
          <h2 className="text-[0.65rem] font-semibold text-slate-500 uppercase tracking-widest mb-5 flex items-center gap-2">
            <TrendingUp size={12} /> Airflow Pipeline · ecommerce_pipeline DAG
          </h2>
          <div className="flex items-center overflow-x-auto pb-1">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.label} className="flex items-center">
                <div className="flex flex-col items-center gap-2 min-w-[80px]">
                  <div className="w-12 h-12 rounded-2xl bg-white/[0.05] border border-white/[0.08]
                                  flex items-center justify-center text-xl
                                  hover:bg-cyan-500/10 hover:border-cyan-500/25 transition-all duration-200">
                    {step.icon}
                  </div>
                  <div className="text-center">
                    <p className="text-[0.7rem] font-semibold text-slate-300">{step.label}</p>
                    <p className="text-[0.6rem] text-slate-600">{step.desc}</p>
                  </div>
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <ArrowRight size={13} className="text-slate-700 mx-1 mb-5 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Service links */}
        <div>
          <h2 className="text-[0.65rem] font-semibold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <Server size={12} /> Services & Ports
          </h2>
          <div className="flex flex-col gap-2">
            {SERVICE_LINKS.map(({ name, url, desc, emoji, color }) =>
              url ? (
                <a key={name} href={url} target="_blank" rel="noreferrer"
                  className={`flex items-center justify-between p-4 rounded-xl
                              bg-gradient-to-r ${color} to-transparent
                              border border-white/[0.07] hover:border-white/[0.15]
                              transition-all duration-200 group`}>
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{emoji}</span>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">{name}</p>
                      <p className="text-xs text-slate-500">{desc}</p>
                    </div>
                  </div>
                  <ExternalLink size={13} className="text-slate-600 group-hover:text-slate-300 transition-colors" />
                </a>
              ) : (
                <div key={name}
                  className={`flex items-center gap-3 p-4 rounded-xl
                              bg-gradient-to-r ${color} to-transparent border border-white/[0.07]`}>
                  <span className="text-xl">{emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">{name}</p>
                    <p className="text-xs text-slate-500">{desc}</p>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
