import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { confirmAttempt, fetchAttempt, type GradeAttempt } from '../api'
import { PageNav } from '../chrome'
import { BookIcon, ChartIcon, CheckIcon, CrossIcon, MessageIcon, SearchIcon } from '../icons'
import { isLoggedIn } from '../session'

export default function GradeResult() {
  const { attemptId = '' } = useParams()
  const navigate = useNavigate()
  const [attempt, setAttempt] = useState<GradeAttempt | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const data = await fetchAttempt(attemptId)
        if (!cancelled) setAttempt(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载失败')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [attemptId])

  async function onConfirm() {
    if (!attempt) return
    if (!isLoggedIn()) {
      setNotice('请先登录后再保存成绩')
      navigate('/login')
      return
    }
    setConfirming(true)
    setNotice(null)
    try {
      const data = await confirmAttempt(attempt.id)
      setAttempt(data)
      setNotice('成绩已保存')
    } catch (err) {
      setNotice(err instanceof Error ? err.message : '保存失败')
    } finally {
      setConfirming(false)
    }
  }

  if (error) {
    return (
      <div className="app-shell">
        <div className="page">
          <PageNav title="判分结果" />
          <p className="notice error">{error}</p>
        </div>
      </div>
    )
  }

  if (!attempt) {
    return (
      <div className="app-shell">
        <div className="page">
          <PageNav title="判分结果" />
          <p className="sub">加载中…</p>
        </div>
      </div>
    )
  }

  const pct = attempt.total ? Math.round((attempt.correct / attempt.total) * 100) : 0
  const sourceLabel = attempt.source === 'chat' ? '对话' : '教材'
  const ringStyle = {
    background: `conic-gradient(var(--amber) ${pct * 3.6}deg, rgba(22,22,22,0.08) 0)`,
  }

  return (
    <div className="app-shell">
      <div className="page page-tab grade-result">
        <PageNav title="判分结果" />

        <div className="score-ring-wrap">
          <div className="score-ring" style={ringStyle}>
            <div className="score-ring-inner">
              <div className="score-ring-num">
                {attempt.correct}/{attempt.total}
              </div>
              <div className="score-ring-pct">{pct}%</div>
            </div>
          </div>
          <p className="score-cheer">很棒！错题已整理好</p>
          <div className="chips" style={{ justifyContent: 'center' }}>
            <span className="tag">
              {attempt.source === 'chat' ? <MessageIcon size={12} /> : <BookIcon size={12} />}
              {sourceLabel} · {attempt.title}
            </span>
            {attempt.demo ? <span className="tag">演示判分</span> : null}
          </div>
        </div>

        <div className="grade-list">
          {attempt.items.map((item) => (
            <div className="grade-row" key={item.index}>
              <span className="grade-stem">
                {item.index}. {item.stem}
              </span>
              {item.correct ? (
                <span className="grade-ok">
                  <CheckIcon size={14} /> 正确
                </span>
              ) : (
                <span className="grade-bad">
                  <CrossIcon size={14} /> 错误
                </span>
              )}
            </div>
          ))}
        </div>

        {notice ? <p className="notice">{notice}</p> : null}

        {!attempt.confirmed ? (
          <button
            className="btn btn-amber btn-block"
            type="button"
            disabled={confirming}
            onClick={() => void onConfirm()}
          >
            {confirming ? '保存中…' : isLoggedIn() ? '确认并保存成绩' : '登录后保存成绩'}
          </button>
        ) : (
          <p className="sub" style={{ textAlign: 'center', marginTop: 8 }}>
            已写入成绩记录
          </p>
        )}

        <button
          className="btn btn-amber btn-block"
          type="button"
          onClick={() => navigate(`/grade/wrong/${attempt.id}`)}
        >
          <SearchIcon size={16} /> 查看错题
        </button>
        <button className="btn btn-outline amber btn-block" type="button" onClick={() => navigate('/scores')}>
          <ChartIcon /> 成绩记录
        </button>
      </div>
    </div>
  )
}
