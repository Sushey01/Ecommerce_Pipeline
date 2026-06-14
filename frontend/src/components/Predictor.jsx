import { useState } from 'react'
import { Send, Loader2, Zap, AlertCircle } from 'lucide-react'

const DEFAULTS = {
  age: 34, gender: 'Female', device_type: 'Mobile',
  time_on_site: 14.2, pages_viewed: 5, previous_purchases: 3,
  cart_items: 2, discount_seen: 1, returning_user: 1,
  avg_session_time: 12, bounce_rate: 0.04, purchase: 1,
}

/* Animated SVG Arc Gauge */
function Gauge({ probability }) {
  const pct    = Math.round(probability * 100)
  const R      = 60
  const cx     = 80
  const cy     = 80
  const stroke = 12
  const circumference = Math.PI * R          // half-circle arc length
  const offset = circumference * (1 - probability)
  const isClick = probability >= 0.5
  const arcColor = isClick ? '#10b981' : '#f43f5e'

  return (
    <div className="flex flex-col items-center gap-4">
      <svg width="160" height="100" viewBox="0 0 160 100" className="overflow-visible">
        <defs>
          <linearGradient id="gClick" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
          <linearGradient id="gNoClick" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f43f5e" />
            <stop offset="100%" stopColor="#fb7185" />
          </linearGradient>
        </defs>
        {/* Background arc */}
        <path
          d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`}
          fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Foreground arc */}
        <path
          d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`}
          fill="none"
          stroke={isClick ? 'url(#gClick)' : 'url(#gNoClick)'}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="gauge-arc"
        />
        {/* Center text */}
        <text x={cx} y={cy - 10} textAnchor="middle"
              className="fill-slate-100 font-bold" style={{ fontSize: 22, fontFamily: 'Inter,sans-serif', fontWeight: 800 }}>
          {pct}%
        </text>
        <text x={cx} y={cy + 7} textAnchor="middle"
              className="fill-slate-500" style={{ fontSize: 9, fontFamily: 'Inter,sans-serif', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Probability
        </text>
      </svg>

      <div className="text-center">
        <p className={`text-xl font-extrabold ${isClick ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isClick ? '🖱️ Will Click Ad' : '🚫 Will NOT Click'}
        </p>
        <p className="text-sm text-slate-500 mt-1">
          Confidence: <span className="font-semibold text-slate-300">{(probability * 100).toFixed(1)}%</span>
        </p>
      </div>
    </div>
  )
}

/* Slider input */
function SliderField({ label, name, value, min, max, step = 0.1, onChange }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[0.75rem] font-semibold text-slate-400">
        {label} <span className="text-slate-600 font-normal">({min}–{max})</span>
      </label>
      <div className="flex items-center gap-3">
        <input type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(name, parseFloat(e.target.value))}
          className="flex-1 bg-white/[0.08] accent-cyan-400 rounded-full" />
        <span className="text-sm font-bold text-cyan-400 min-w-[40px] text-right">{value}</span>
      </div>
    </div>
  )
}

/* Select input */
function SelectField({ label, name, value, options, onChange }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[0.75rem] font-semibold text-slate-400">{label}</label>
      <select value={value} onChange={e => onChange(name, e.target.value)}
        className="w-full px-3 py-2.5 rounded-lg border border-white/[0.08]
                   bg-white/[0.04] text-slate-200 text-sm outline-none
                   focus:border-cyan-500/40 focus:bg-cyan-500/[0.04]
                   transition-all duration-150">
        {options.map(o => <option key={o} value={o} className="bg-slate-900">{o}</option>)}
      </select>
    </div>
  )
}

/* Toggle input */
function ToggleField({ label, name, value, onChange }) {
  const on = value === 1
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[0.75rem] font-semibold text-slate-400">{label}</label>
      <button onClick={() => onChange(name, on ? 0 : 1)}
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-white/[0.08]
                   bg-white/[0.04] hover:bg-white/[0.07] transition-all text-sm text-slate-300">
        <div className={`w-9 h-5 rounded-full relative transition-colors duration-200 flex-shrink-0
                         ${on ? 'bg-cyan-500' : 'bg-slate-700'}`}>
          <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white
                           transition-transform duration-200 ${on ? 'translate-x-4' : ''}`} />
        </div>
        <span>{on ? 'Yes' : 'No'}</span>
      </button>
    </div>
  )
}

export default function Predictor() {
  const [form, setForm]     = useState(DEFAULTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  const set = (name, val) => setForm(f => ({ ...f, [name]: val }))

  const handleSubmit = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const res  = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setResult(await res.json())
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 pt-8 pb-0">
        <h1 className="text-2xl font-extrabold text-slate-100">Ad Click Predictor</h1>
        <p className="text-sm text-slate-500 mt-1">
          Fill in the user session details below to predict ad-click probability
        </p>
      </div>

      <div className="px-8 py-6 flex-1 overflow-y-auto">
        <div className="grid grid-cols-2 gap-6 items-start">

          {/* ── Form ─────────────────────────────────────────── */}
          <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-6 flex flex-col gap-5">
            <h2 className="text-[0.65rem] font-semibold text-slate-500 uppercase tracking-widest">
              User Session Features
            </h2>

            <div className="grid grid-cols-2 gap-x-6 gap-y-5">
              <SliderField label="Age"                name="age"                value={form.age}                min={18}  max={75}  step={1}    onChange={set} />
              <SliderField label="Time on Site (min)" name="time_on_site"       value={form.time_on_site}       min={0}   max={60}  step={0.1}  onChange={set} />
              <SliderField label="Pages Viewed"       name="pages_viewed"       value={form.pages_viewed}       min={1}   max={30}  step={1}    onChange={set} />
              <SliderField label="Prev. Purchases"    name="previous_purchases" value={form.previous_purchases} min={0}   max={20}  step={1}    onChange={set} />
              <SliderField label="Cart Items"         name="cart_items"         value={form.cart_items}         min={0}   max={15}  step={1}    onChange={set} />
              <SliderField label="Avg Session (min)"  name="avg_session_time"   value={form.avg_session_time}   min={0}   max={60}  step={0.1}  onChange={set} />
              <SliderField label="Bounce Rate"        name="bounce_rate"        value={form.bounce_rate}        min={0}   max={1}   step={0.01} onChange={set} />

              <SelectField label="Gender"      name="gender"      value={form.gender}      options={['Female','Male','Unknown']}                     onChange={set} />
              <SelectField label="Device Type" name="device_type" value={form.device_type} options={['Mobile','Desktop','Tablet','Unknown']}          onChange={set} />

              <ToggleField label="Discount Seen"   name="discount_seen"   value={form.discount_seen}   onChange={set} />
              <ToggleField label="Returning User"  name="returning_user"  value={form.returning_user}  onChange={set} />
              <ToggleField label="Made a Purchase" name="purchase"        value={form.purchase}        onChange={set} />
            </div>

            <button onClick={handleSubmit} disabled={loading}
              className="mt-2 flex items-center justify-center gap-2.5 w-full py-3 rounded-xl
                         text-sm font-bold bg-gradient-to-r from-cyan-500 to-cyan-600 text-white
                         shadow-[0_4px_20px_rgba(6,182,212,0.3)]
                         hover:shadow-[0_6px_24px_rgba(6,182,212,0.45)]
                         hover:-translate-y-0.5 transition-all duration-150
                         disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {loading ? 'Predicting…' : 'Run Prediction'}
            </button>
          </div>

          {/* ── Result Panel ─────────────────────────────────── */}
          <div className="flex flex-col gap-4">
            {!result && !error && !loading && (
              <div className="bg-white/[0.03] border border-white/[0.07] border-dashed rounded-2xl p-10
                              flex flex-col items-center justify-center gap-3 text-center">
                <span className="text-4xl">🎯</span>
                <p className="text-slate-400 font-semibold">No prediction yet</p>
                <p className="text-sm text-slate-600">Fill in the form and click <strong className="text-slate-400">Run Prediction</strong></p>
              </div>
            )}

            {loading && (
              <div className="bg-white/[0.03] border border-white/[0.07] rounded-2xl p-10
                              flex flex-col items-center justify-center gap-3">
                <Loader2 size={32} className="text-cyan-400 animate-spin" />
                <p className="text-slate-400 text-sm">Running inference…</p>
              </div>
            )}

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/25 rounded-2xl p-6
                              flex items-center gap-3 text-rose-400">
                <AlertCircle size={20} className="flex-shrink-0" />
                <div>
                  <p className="font-semibold text-sm">Prediction failed</p>
                  <p className="text-xs text-rose-400/70 mt-0.5">{error} — is the API running?</p>
                </div>
              </div>
            )}

            {result && (
              <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-6
                              flex flex-col gap-6 animate-result">
                {/* Cached badge */}
                {result.cached && (
                  <div className="flex justify-center">
                    <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full
                                     bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      <Zap size={12} /> Retrieved from Redis Cache
                    </span>
                  </div>
                )}

                {/* Gauge */}
                <Gauge probability={result.ad_clicked_probability} />

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'Probability', value: `${(result.ad_clicked_probability * 100).toFixed(1)}%` },
                    { label: 'Prediction',  value: result.ad_clicked === 1 ? 'Click' : 'No Click' },
                    { label: 'Source',      value: result.cached ? 'Cache' : 'Model' },
                  ].map(({ label, value }) => (
                    <div key={label} className="text-center p-3 rounded-xl bg-white/[0.03] border border-white/[0.07]">
                      <p className="text-[0.65rem] text-slate-600 uppercase tracking-wider mb-1">{label}</p>
                      <p className="text-sm font-bold text-slate-100">{value}</p>
                    </div>
                  ))}
                </div>

                {/* Session echo */}
                <div className="border-t border-white/[0.06] pt-4">
                  <p className="text-[0.65rem] text-slate-600 uppercase tracking-wider mb-2">Input Summary</p>
                  <div className="grid grid-cols-3 gap-1.5">
                    {[
                      { k: 'Age', v: form.age },
                      { k: 'Gender', v: form.gender },
                      { k: 'Device', v: form.device_type },
                      { k: 'Pages', v: form.pages_viewed },
                      { k: 'Cart', v: form.cart_items },
                      { k: 'Bounce', v: form.bounce_rate },
                    ].map(({ k, v }) => (
                      <div key={k} className="flex flex-col px-2 py-1.5 rounded-lg bg-white/[0.03]">
                        <span className="text-[0.6rem] text-slate-600">{k}</span>
                        <span className="text-xs text-slate-300 font-medium">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
