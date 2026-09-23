import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { saveQuiz, saveQuizError } from '../draft'

type Role = 'user' | 'assistant'

type ChatMessage = {
  role: Role
  text: string
}

type Question = {
  qtype: string
  stem: string
  options?: string[]
  answer?: string
}

type StreamDone = {
  event: 'done'
  status: 'clarifying' | 'draft_ready' | 'error'
  assistant_text: string
  questions: Question[]
  summary?: string
}

export default function Chat() {
  const navigate = useNavigate()
  const [threadId, setThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState<string | null>(null)
  const [draft, setDraft] = useState<Question[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch('/api/chat/sessions', { method: 'POST' })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '无法创建对话')
        if (!cancelled) setThreadId(data.thread_id)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '无法创建对话')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, draft, progress])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!threadId || !input.trim() || busy) return
    const text = input.trim()
    setInput('')
    setBusy(true)
    setError(null)
    setDraft(null)
    setProgress('正在发送…')
    setMessages((prev) => [...prev, { role: 'user', text }])

    try {
      const res = await fetch(`/api/chat/sessions/${threadId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || '发送失败')
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let donePayload: StreamDone | null = null

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() || ''
        for (const chunk of chunks) {
          const line = chunk.trim()
          if (!line.startsWith('data:')) continue
          const payload = JSON.parse(line.slice(5).trim())
          if (payload.event === 'progress') {
            setProgress(payload.message)
          }
          if (payload.event === 'token') {
            const piece = String(payload.text || '')
            setProgress(null)
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last?.role === 'assistant') {
                return [...prev.slice(0, -1), { ...last, text: last.text + piece }]
              }
              return [...prev, { role: 'assistant', text: piece }]
            })
          }
          if (payload.event === 'done') donePayload = payload as StreamDone
        }
      }

      if (!donePayload) throw new Error('没有收到完整回复')

      setMessages((prev) => {
        const finalText = donePayload!.assistant_text || ''
        const last = prev[prev.length - 1]
        if (last?.role === 'assistant') {
          return [...prev.slice(0, -1), { ...last, text: finalText }]
        }
        return finalText ? [...prev, { role: 'assistant', text: finalText }] : prev
      })

      if (donePayload.status === 'error') {
        setError(donePayload.assistant_text)
      } else if (donePayload.status === 'draft_ready') {
        setDraft(donePayload.questions || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送失败')
    } finally {
      setBusy(false)
      setProgress(null)
    }
  }

  async function onConfirm() {
    if (!threadId || busy) return
    setBusy(true)
    setProgress('正在生成练习卷…')
    try {
      const res = await fetch(`/api/chat/sessions/${threadId}/confirm`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '确认失败')
      saveQuiz({
        id: data.id,
        title: data.title,
        questions: data.questions,
        includeAnswers: data.include_answers,
        count: data.count,
        difficulty: data.difficulty,
        source: 'chat',
        summary: data.summary,
      })
      navigate('/chat/result')
    } catch (err) {
      const message = err instanceof Error ? err.message : '确认失败'
      saveQuizError(message)
      setError(message)
    } finally {
      setBusy(false)
      setProgress(null)
    }
  }

  return (
    <div className="app-shell chat-screen">
      <header className="chat-head">
        <PageNav title="对话出题" />
      </header>
      <div className="chat-body">
        {messages.length === 0 ? (
          <p className="sub chat-hint">用一句话说明练习需求，例如「三年级口算 12 道」。</p>
        ) : null}
        {messages.map((message, index) => (
          <div key={`${index}-${message.role}`} className={message.role === 'user' ? 'bubble me' : 'bubble bot'}>
            {message.text}
          </div>
        ))}
        {progress ? <p className="notice">{progress}</p> : null}
        {error ? <p className="notice error">{error}</p> : null}
        {draft && draft.length > 0 ? (
          <div className="draft-panel">
            <div className="section-label">题目预览</div>
            {draft.map((question, index) => (
              <div className="q" key={`${index}-${question.stem}`}>
                <p>
                  {index + 1}. {question.stem}
                </p>
                {question.options && question.options.length > 0 ? (
                  <ul className="q-options">
                    {question.options.map((option) => (
                      <li key={option}>{option}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
            <button className="btn btn-amber btn-block" type="button" disabled={busy} onClick={onConfirm}>
              确认出题
            </button>
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>
      <form className="chat-composer" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={threadId ? '输入出题需求' : '正在准备对话…'}
          disabled={!threadId || busy}
        />
        <button className="btn btn-amber" type="submit" disabled={!threadId || busy || !input.trim()}>
          发送
        </button>
      </form>
    </div>
  )
}
