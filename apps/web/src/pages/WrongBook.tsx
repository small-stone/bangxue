import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWrongBook, type WrongBookItem } from '../api'
import { DemoBadge, PageNav } from '../chrome'
import {
  isDemoId,
  pickWrongShowcase,
  type DemoWrongItem,
} from '../demoShowcase'
import {
  BookIcon,
  CalcIcon,
  ClockIcon,
  EditIcon,
  MessageIcon,
  SparkIcon,
} from '../icons'
import { isLoggedIn } from '../session'

const FILTERS = ['全部', '数学', '语文', '英语'] as const

function wrongIcon(item: DemoWrongItem) {
  if (item.icon === 'clock') return <ClockIcon size={16} />
  if (item.icon === 'edit') return <EditIcon size={16} />
  if (item.subject === '英语') return <EditIcon size={16} />
  return <CalcIcon size={16} />
}

export default function WrongBook() {
  const navigate = useNavigate()
  const loggedIn = isLoggedIn()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('全部')
  const [apiItems, setApiItems] = useState<WrongBookItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(loggedIn)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    if (!loggedIn) {
      setApiItems([])
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      try {
        const data = await fetchWrongBook()
        if (cancelled) return
        setApiItems(data.items)
        setError(null)
      } catch (err) {
        if (!cancelled) {
          setApiItems([])
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

  const showcase = useMemo(
    () => pickWrongShowcase(loggedIn, apiItems),
    [loggedIn, apiItems],
  )

  const list = useMemo(
    () =>
      filter === '全部'
        ? showcase.items
        : showcase.items.filter((item) => item.subject === filter),
    [filter, showcase.items],
  )

  function openItem(item: DemoWrongItem) {
    if (showcase.demo || isDemoId(item.attempt_id)) {
      setNotice('演示样例，登录并确认成绩后可查看真实错题')
      return
    }
    navigate(`/grade/wrong/${item.attempt_id}`)
  }

  function onDemoCta() {
    setNotice('演示功能，敬请期待')
  }

  return (
    <div className="app-shell">
      <div className="page page-wrong-book">
        <PageNav title="错题本" badge={showcase.demo ? '演示' : undefined} hideGuest />
        <p className="sub">来自已确认成绩的错题</p>

        {showcase.demo && loggedIn ? (
          <p className="sub demo-hint">暂无真实错题，以下为演示样例；判分确认后会出现在这里</p>
        ) : null}
        {notice ? <p className="notice">{notice}</p> : null}
        {error && !showcase.demo ? <p className="notice error">{error}</p> : null}

        <div className="stats-row" style={{ marginTop: 14 }}>
          <div className="stat-card">
            <div className="stat-label">待复习</div>
            <div className="stat-value">
              {loading && loggedIn && !showcase.demo ? '—' : showcase.pendingReview}
            </div>
          </div>
          <div className="stat-card accent">
            <div className="stat-label">本周新增</div>
            <div className="stat-value">
              {loading && loggedIn && !showcase.demo ? '—' : showcase.weekNew}
            </div>
          </div>
        </div>

        <div className="chips" style={{ marginTop: 14 }}>
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
            <BookIcon size={14} />
            错题列表
          </div>
          {loading && loggedIn && !showcase.demo ? (
            <p className="sub">加载中…</p>
          ) : list.length === 0 ? (
            <div className="empty-card">
              <p>还没有这个科目的错题</p>
              <p className="sub">判分确认后，错题会出现在这里</p>
            </div>
          ) : (
            <div className="wrong-list" style={{ marginTop: 0 }}>
              {list.map((item, i) => (
                <button
                  className="wrong-card showcase practice-btn"
                  type="button"
                  key={`${item.attempt_id}-${item.index}-${i}`}
                  onClick={() => openItem(item)}
                >
                  <div className="wrong-card-top">
                    <span className="menu-ico">{wrongIcon(item)}</span>
                    <div className="meta">
                      <div className="kicker">
                        {item.subject || '练习'} · 第 {item.index ?? '—'} 题
                        <span className="date">{item.date || ''}</span>
                      </div>
                    </div>
                  </div>
                  <p className="wrong-stem">{item.stem}</p>
                  <div className="wrong-meta-row">
                    <span className="tag">
                      {item.source === 'chat' ? <MessageIcon size={12} /> : <BookIcon size={12} />}
                      {item.source === 'chat' ? '对话' : '教材'}
                    </span>
                    <span>{item.title}</span>
                  </div>
                  {item.student_answer || item.answer ? (
                    <div className="wrong-answers">
                      <div className="ans-box bad">
                        <div className="lab">你的答案</div>
                        <div className="val">{item.student_answer || '—'}</div>
                      </div>
                      <div className="ans-box ok">
                        <div className="lab">正确答案</div>
                        <div className="val">{item.answer || '—'}</div>
                      </div>
                    </div>
                  ) : null}
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
      <div className="sticky-cta">
        <button className="btn btn-amber btn-block" type="button" onClick={onDemoCta}>
          <SparkIcon size={16} />
          用错题出一卷
        </button>
      </div>
    </div>
  )
}
