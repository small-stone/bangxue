import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { fetchAttempt, type GradeAttempt } from '../api'
import { PageNav } from '../chrome'
import { CrossIcon } from '../icons'

export default function WrongQuestions() {
  const { attemptId = '' } = useParams()
  const navigate = useNavigate()
  const [attempt, setAttempt] = useState<GradeAttempt | null>(null)
  const [error, setError] = useState<string | null>(null)

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

  const wrong = useMemo(
    () => (attempt?.items || []).filter((item) => !item.correct),
    [attempt],
  )

  if (error) {
    return (
      <div className="app-shell">
        <div className="page">
          <PageNav title="错题详情" />
          <p className="notice error">{error}</p>
        </div>
      </div>
    )
  }

  if (!attempt) {
    return (
      <div className="app-shell">
        <div className="page">
          <PageNav title="错题详情" />
          <p className="sub">加载中…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="错题详情" />
        <p className="sub">{attempt.title}</p>

        {wrong.length === 0 ? (
          <div className="empty-card" style={{ marginTop: 16 }}>
            <p>本次没有错题</p>
            <p className="sub">全部答对，继续保持</p>
          </div>
        ) : (
          <div className="wrong-list">
            {wrong.map((item) => (
              <div className="wrong-card" key={item.index}>
                <div className="wrong-head">
                  <CrossIcon size={16} />
                  <span>
                    第 {item.index} 题
                  </span>
                </div>
                <p className="wrong-stem">{item.stem}</p>
                {item.answer ? <p className="wrong-meta">参考答案：{item.answer}</p> : null}
                {item.student_answer ? (
                  <p className="wrong-meta">识别作答：{item.student_answer}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}

        <button className="btn btn-outline amber btn-block" type="button" onClick={() => navigate(`/grade/result/${attempt.id}`)}>
          返回判分结果
        </button>
      </div>
    </div>
  )
}
