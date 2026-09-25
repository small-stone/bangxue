import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWrongBook, type WrongBookItem } from '../api'
import { PageNav } from '../chrome'
import { isLoggedIn } from '../session'

export default function WrongBook() {
  const navigate = useNavigate()
  const loggedIn = isLoggedIn()
  const [items, setItems] = useState<WrongBookItem[]>([])
  const [guest, setGuest] = useState(!loggedIn)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(loggedIn)

  useEffect(() => {
    if (!loggedIn) {
      setGuest(true)
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      try {
        const data = await fetchWrongBook()
        if (cancelled) return
        setItems(data.items)
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

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="错题本" />
        <p className="sub">来自已确认成绩的错题</p>

        {guest || !loggedIn ? (
          <div className="empty-card" style={{ marginTop: 16 }}>
            <p>登录后同步错题本</p>
            <p className="sub">游客无法查看账号错题</p>
            <button className="btn btn-amber btn-sm" type="button" style={{ marginTop: 12 }} onClick={() => navigate('/login')}>
              去登录
            </button>
          </div>
        ) : loading ? (
          <p className="sub" style={{ marginTop: 16 }}>
            加载中…
          </p>
        ) : error ? (
          <p className="notice error">{error}</p>
        ) : items.length === 0 ? (
          <div className="empty-card" style={{ marginTop: 16 }}>
            <p>还没有错题</p>
            <p className="sub">判分确认后，错题会出现在这里</p>
          </div>
        ) : (
          <div className="wrong-list">
            {items.map((item, i) => (
              <button
                className="wrong-card practice-btn"
                type="button"
                key={`${item.attempt_id}-${item.index}-${i}`}
                onClick={() => navigate(`/grade/wrong/${item.attempt_id}`)}
              >
                <div className="wrong-head">
                  <span>
                    {item.subject || '练习'} · 第 {item.index} 题
                  </span>
                  <span className="wrong-date">{item.date}</span>
                </div>
                <p className="wrong-stem">{item.stem}</p>
                <p className="wrong-meta">{item.title}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
