import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchScores, type GradeAttempt } from '../api'
import { BottomNav, DemoBadge, GuestBadge } from '../chrome'
import {
  DEMO_SPARK_HEIGHTS,
  DEMO_SPARK_PEAK_LABEL,
  isDemoId,
  pickScoreShowcase,
} from '../demoShowcase'
import {
  BookIcon,
  CalcIcon,
  ChartIcon,
  ChevronRight,
  ClipboardIcon,
  GlobeIcon,
  MessageIcon,
} from '../icons'
import { isLoggedIn } from '../session'

const FILTERS = ['全部', '数学', '语文', '英语'] as const
const SPARK_DAYS = ['一', '二', '三', '四', '五', '六', '日'] as const

function formatDate(iso?: string | null): string {
  if (!iso) return '--'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(5, 10)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${mm}-${dd}`
}

function subjectIcon(subject?: string) {
  if (subject === '英语') return <GlobeIcon size={16} />
  return <CalcIcon size={16} />
}

export default function Scores() {
  const navigate = useNavigate()
  const loggedIn = isLoggedIn()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('全部')
  const [apiScores, setApiScores] = useState<GradeAttempt[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setLoading(true)
      try {
        if (!loggedIn) {
          if (!cancelled) {
            setApiScores([])
            setError(null)
          }
          return
        }
        const data = await fetchScores()
        if (cancelled) return
        setApiScores(data.scores)
        setError(null)
      } catch (err) {
        if (!cancelled) {
          setApiScores([])
          setError(err instanceof Error ? err.message : '加载失败')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [loggedIn])

  const { scores, demo } = useMemo(
    () => pickScoreShowcase(loggedIn, apiScores),
    [loggedIn, apiScores],
  )

  const list = useMemo(
    () => (filter === '全部' ? scores : scores.filter((item) => item.subject === filter)),
    [filter, scores],
  )

  const avg =
    list.length === 0
      ? 0
      : Math.round(
          (list.reduce((sum, item) => sum + (item.total ? item.correct / item.total : 0), 0) /
            list.length) *
            100,
        )

  function openScore(item: GradeAttempt) {
    if (isDemoId(item.id) || demo) {
      setNotice('演示样例，登录并确认成绩后可查看真实详情')
      return
    }
    navigate(`/grade/result/${item.id}`)
  }

  return (
    <div className="app-shell">
      <div className="page page-tab">
        <div className="page-head row page-head-row">
          <div>
            <h1 className="page-title">成绩记录</h1>
            <p className="sub">查看历史练习得分与错题</p>
          </div>
          {demo ? <DemoBadge /> : <GuestBadge />}
        </div>

        {demo && loggedIn ? (
          <p className="sub demo-hint">暂无真实成绩，以下为演示样例；判分确认后会出现在这里</p>
        ) : null}
        {notice ? <p className="notice">{notice}</p> : null}
        {error && !demo ? <p className="notice error">{error}</p> : null}

        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-label">练习次数</div>
            <div className="stat-value">{loading && loggedIn && !demo ? '—' : list.length}</div>
          </div>
          <div className="stat-card accent">
            <div className="stat-label">平均得分</div>
            <div className="stat-value">
              {loading && loggedIn && !demo ? '—' : avg}
              <span className="stat-unit">%</span>
            </div>
          </div>
        </div>

        <div className="spark-card">
          <div className="spark-head">
            <div className="label">
              <ChartIcon />
              近 7 日得分
            </div>
            <div className="hint">{DEMO_SPARK_PEAK_LABEL}</div>
          </div>
          <div className="sparkline" aria-hidden="true">
            {DEMO_SPARK_HEIGHTS.map((h, i) => (
              <span key={SPARK_DAYS[i]} style={{ height: `${h}%` }}>
                <i style={{ height: '100%' }} />
              </span>
            ))}
          </div>
          <div className="spark-days">
            {SPARK_DAYS.map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>
        </div>

        <div className="chips" style={{ marginTop: 4 }}>
          {FILTERS.map((item) => (
            <button
              key={item}
              className={filter === item ? 'chip on' : 'chip'}
              type="button"
              onClick={() => setFilter(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <section className="section">
          <div className="section-label">
            <ClipboardIcon size={14} />
            最近练习
          </div>
          {loading && loggedIn && !demo ? (
            <p className="sub">加载中…</p>
          ) : list.length === 0 ? (
            <div className="empty-card">
              <p>还没有这个科目的成绩</p>
              <p className="sub">去首页出一套题，判分后会出现在这里</p>
            </div>
          ) : (
            list.map((item) => {
              const pct = item.total ? Math.round((item.correct / item.total) * 100) : 0
              const wrong = Math.max(0, item.total - item.correct)
              const source = item.source === 'chat' ? '对话' : '教材'
              return (
                <button
                  key={item.id}
                  className="score-card practice-btn"
                  type="button"
                  onClick={() => openScore(item)}
                >
                  <div className="top">
                    <span className="menu-ico">{subjectIcon(item.subject)}</span>
                    <div className="meta">
                      <div className="title-row">
                        <span className="date">{formatDate(item.confirmed_at || item.created_at)}</span>
                        {item.subject || '练习'}{' '}
                        <span className="tag">
                          {item.source === 'chat' ? <MessageIcon size={12} /> : <BookIcon size={12} />}
                          {source}
                        </span>
                      </div>
                      <div className="desc">{item.title}</div>
                    </div>
                    <span className="score">{pct}%</span>
                    <span className="chev">
                      <ChevronRight />
                    </span>
                  </div>
                  <div className="foot">
                    <div className="bar">
                      <i style={{ width: `${pct}%` }} />
                    </div>
                    {wrong > 0 ? <span className="wrong-count">错 {wrong}</span> : null}
                  </div>
                </button>
              )
            })
          )}
        </section>
      </div>
      <BottomNav active="scores" />
    </div>
  )
}
