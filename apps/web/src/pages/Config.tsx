import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { loadDraft, saveDraft, saveQuiz, saveQuizError, type Draft, type Question } from '../draft'

const COUNTS = [10, 15, 20, 30]
const LEVELS = ['简单', '适中', '较难']

type StreamEvent = {
  type?: string
  phase?: string
  message?: string
  done?: number
  total?: number
  index?: number
  id?: string
  title?: string
  questions?: Question[]
  detail?: string
}

async function* readSse(response: Response): AsyncGenerator<StreamEvent> {
  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('no body')
  }
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const dataLine = chunk
        .split('\n')
        .map((line) => line.trimEnd())
        .find((line) => line.startsWith('data:'))
      if (!dataLine) continue
      const raw = dataLine.slice(5).trim()
      if (!raw) continue
      try {
        yield JSON.parse(raw) as StreamEvent
      } catch {
        // ignore malformed frames
      }
    }
  }
}

export default function Config() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const [busy, setBusy] = useState(false)
  const [statusText, setStatusText] = useState('正在准备出题…')
  const [progress, setProgress] = useState<{ done?: number; total?: number }>({})
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  function update(patch: Partial<Draft>) {
    const next = { ...draft, ...patch }
    setDraft(next)
    saveDraft(next)
  }

  async function start() {
    if (busy || draft.units.length === 0) return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setStatusText('正在连接出题服务…')
    setProgress({ total: draft.count })
    setBusy(true)
    try {
      const response = await fetch('/api/quizzes/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        signal: controller.signal,
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
      if (!response.ok || !response.body) {
        let detail = '暂时无法出题'
        try {
          const body = await response.json()
          if (typeof body.detail === 'string') detail = body.detail
        } catch {
          // keep default
        }
        saveQuizError(detail)
        navigate('/textbook/result')
        return
      }

      let finished = false
      for await (const event of readSse(response)) {
        if (controller.signal.aborted) return
        if (event.type === 'status') {
          if (typeof event.message === 'string' && event.message) {
            setStatusText(event.message)
          }
          setProgress((prev) => ({
            done: typeof event.done === 'number' ? event.done : prev.done,
            total: typeof event.total === 'number' ? event.total : prev.total ?? draft.count,
          }))
        } else if (event.type === 'question') {
          const done = typeof event.done === 'number' ? event.done : (event.index ?? 0) + 1
          const total = typeof event.total === 'number' ? event.total : draft.count
          setProgress({ done, total })
          setStatusText(`已整理 ${done}/${total} 题`)
        } else if (event.type === 'done') {
          finished = true
          saveQuiz({
            id: String(event.id ?? ''),
            title: String(event.title ?? ''),
            questions: Array.isArray(event.questions) ? (event.questions as Question[]) : [],
            includeAnswers: draft.includeAnswers,
            count: draft.count,
            difficulty: draft.difficulty,
          })
          navigate('/textbook/result')
          return
        } else if (event.type === 'error') {
          finished = true
          saveQuizError(typeof event.detail === 'string' ? event.detail : '暂时无法出题')
          navigate('/textbook/result')
          return
        }
      }
      if (!finished) {
        saveQuizError('出题中断，请重试')
        navigate('/textbook/result')
      }
    } catch (err) {
      if (controller.signal.aborted) return
      saveQuizError('暂时无法出题')
      navigate('/textbook/result')
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null
      }
      setBusy(false)
    }
  }

  const progressLabel =
    typeof progress.done === 'number' && typeof progress.total === 'number'
      ? `${progress.done}/${progress.total}`
      : typeof progress.total === 'number'
        ? `共 ${progress.total} 题`
        : ''

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
            <p className="loading-line" aria-live="polite">
              {statusText}
            </p>
            {progressLabel ? (
              <p className="loading-line" style={{ opacity: 0.75, marginTop: 8 }}>
                {progressLabel}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
