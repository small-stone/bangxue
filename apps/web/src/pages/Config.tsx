import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { loadDraft, saveDraft, saveQuiz, saveQuizError, type Draft } from '../draft'

const COUNTS = [10, 15, 20, 30]
const LEVELS = ['简单', '适中', '较难']
const LOADING_LINES = [
  '正在对照这一单元的课文',
  '大模型即将计算好题目',
  '正在按难度和题型整理',
  '练习卷马上就好',
]

export default function Config() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const [busy, setBusy] = useState(false)
  const [line, setLine] = useState(0)

  useEffect(() => {
    if (!busy) return
    const timer = window.setInterval(() => {
      setLine((current) => (current + 1) % LOADING_LINES.length)
    }, 1600)
    return () => window.clearInterval(timer)
  }, [busy])

  function update(patch: Partial<Draft>) {
    const next = { ...draft, ...patch }
    setDraft(next)
    saveDraft(next)
  }

  async function start() {
    if (busy || draft.units.length === 0) return
    setLine(0)
    setBusy(true)
    try {
      const response = await fetch('/api/quizzes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stage: draft.stage,
          grade: draft.grade,
          subject: draft.subject,
          edition: draft.edition,
          term: draft.term,
          units: draft.units,
          count: draft.count,
          difficulty: draft.difficulty,
          include_answers: draft.includeAnswers,
        }),
      })
      const body = await response.json()
      if (!response.ok) {
        saveQuizError(typeof body.detail === 'string' ? body.detail : '暂时无法出题')
      } else {
        saveQuiz({
          id: body.id,
          title: body.title,
          questions: body.questions,
          includeAnswers: draft.includeAnswers,
          count: draft.count,
          difficulty: draft.difficulty,
        })
      }
      navigate('/textbook/result')
    } catch {
      saveQuizError('暂时无法出题')
      navigate('/textbook/result')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="出题设置" />
        <div className="ctx">
          {draft.units.map((name) => (
            <span className="tag" key={name}>
              {name}
            </span>
          ))}
          <span className="tag">{draft.subject}</span>
        </div>
        <div className="label">题目数量</div>
        <div className="chips">
          {COUNTS.map((count) => (
            <button key={count} type="button" className={draft.count === count ? 'chip on' : 'chip'} onClick={() => update({ count })}>
              {count}
            </button>
          ))}
        </div>
        <div className="label">难度</div>
        <div className="grid3">
          {LEVELS.map((level) => (
            <button
              key={level}
              type="button"
              className={draft.difficulty === level ? 'diff-card on' : 'diff-card'}
              onClick={() => update({ difficulty: level })}
            >
              <div className="ic">{level.slice(0, 1)}</div>
              <b>{level}</b>
            </button>
          ))}
        </div>
        <div className="label">题型比例</div>
        <div className="card">
          {[
            ['选择题', '40%'],
            ['填空题', '30%'],
            ['计算题', '30%'],
          ].map(([name, ratio]) => (
            <div className="ratio" key={name}>
              <span>{name}</span>
              <div className="track">
                <i style={{ width: ratio }} />
              </div>
              <b>{ratio}</b>
            </div>
          ))}
        </div>
        <button className="toggle" type="button" onClick={() => update({ includeAnswers: !draft.includeAnswers })}>
          <span>同时生成答案卷</span>
          <span className={draft.includeAnswers ? 'switch on' : 'switch'} />
        </button>
        <div className="bottom-cta">
          <button className="btn btn-amber btn-block" type="button" disabled={busy} onClick={start}>
            开始出题
          </button>
        </div>
      </div>
      {busy ? (
        <div className="loading-mask" role="dialog" aria-modal="true" aria-labelledby="quiz-loading-title">
          <div className="loading-card">
            <div className="loading-spin" aria-hidden="true" />
            <p id="quiz-loading-title" className="loading-kicker">
              大模型正在出题
            </p>
            <p className="loading-line" key={line} aria-live="polite">
              {LOADING_LINES[line]}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  )
}
