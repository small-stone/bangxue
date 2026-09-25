import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchScores, type GradeAttempt } from '../api'
import { BottomNav, GuestBadge } from '../chrome'
import { BookIcon, ChartIcon, MessageIcon } from '../icons'
import { isLoggedIn } from '../session'

const FILTERS = ['全部', '数学', '语文', '英语', '综合'] as const

function formatDate(iso?: string | null): string {
  if (!iso) return '--'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(5, 10)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${mm}-${dd}`
}

function subjectShort(subject?: string): string {
  if (!subject) return '练'
  return subject.slice(0, 1)
}

export default function Scores() {
  const navigate = useNavigate()
  const loggedIn = isLoggedIn()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('全部')
  const [scores, setScores] = useState<GradeAttempt[]>([])
  const [guest, setGuest] = useState(!loggedIn)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setLoading(true)
      try {
        const data = await fetchScores()
        if (cancelled) return
        setScores(data.scores)
        setGuest(data.guest)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [loggedIn])

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

  return (
    <div className="app-shell">
      <div className="page page-tab">
        <div className="page-head row page-head-row">
          <div>
            <h1 className="page-title">成绩记录</h1>
            <p className="sub">查看历史练习得分与错题</p>
          </div>
          <GuestBadge />
        </div>

        {guest || !loggedIn ? (
          <div className="empty-card" style={{ marginTop: 16 }}>
            <p>登录后同步成绩</p>
            <p className="sub">游客可判分预览，确认成绩需登录</p>
            <button className="btn btn-amber btn-sm" type="button" style={{ marginTop: 12 }} onClick={() => navigate('/login')}>
              去登录
            </button>
          </div>
        ) : null}

        {!guest && loggedIn ? (
          <>
            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-label">练习次数</div>
                <div className="stat-value">{loading ? '—' : list.length}</div>
              </div>
              <div className="stat-card accent">
                <div className="stat-label">平均得分</div>
                <div className="stat-value">
                  {loading ? '—' : avg}
                  <span className="stat-unit">%</span>
                </div>
              </div>
            </div>

            <div className="chips" style={{ marginTop: 16 }}>
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

            {error ? <p className="notice error" style={{ marginTop: 12 }}>{error}</p> : null}

            <section className="section">
              <div className="section-label">
                <ChartIcon />
                最近练习
              </div>
              {loading ? (
                <p className="sub">加载中…</p>
              ) : list.length === 0 ? (
                <div className="empty-card">
                  <p>还没有这个科目的成绩</p>
                  <p className="sub">去首页出一套题，判分后会出现在这里</p>
                </div>
              ) : (
                list.map((item) => {
                  const pct = item.total ? Math.round((item.correct / item.total) * 100) : 0
                  const source = item.source === 'chat' ? '对话' : '教材'
                  return (
                    <button
                      key={item.id}
                      className="practice practice-btn"
                      type="button"
                      onClick={() => navigate(`/grade/result/${item.id}`)}
                    >
                      <div className="top">
                        <span className="subj-dot">{subjectShort(item.subject)}</span>
                        <span>{formatDate(item.confirmed_at || item.created_at)}</span>
                        <b>{item.subject || '练习'}</b>
                        <span className="tag">
                          {item.source === 'chat' ? <MessageIcon size={12} /> : <BookIcon size={12} />}
                          {source}
                        </span>
                        <span className="score">
                          {item.correct}/{item.total} · {pct}%
                        </span>
                      </div>
                      <div className="practice-title">{item.title}</div>
                      <div className="bar">
                        <i style={{ width: `${pct}%` }} />
                      </div>
                    </button>
                  )
                })
              )}
            </section>
          </>
        ) : null}
      </div>
      <BottomNav active="scores" />
    </div>
  )
}
