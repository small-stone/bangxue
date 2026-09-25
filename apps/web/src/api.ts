import { getSession } from './session'

export type GradeItem = {
  index: number
  stem: string
  correct: boolean
  answer?: string | null
  student_answer?: string | null
}

export type GradeAttempt = {
  id: string
  confirmed: boolean
  demo: boolean
  quiz_id?: string | null
  source?: string
  subject?: string
  title?: string
  correct: number
  total: number
  items: GradeItem[]
  created_at?: string
  confirmed_at?: string | null
  email?: string | null
}

export type WrongBookItem = {
  attempt_id: string
  subject?: string
  title?: string
  source?: string
  date?: string
  index?: number
  stem?: string
  answer?: string | null
  student_answer?: string | null
}

export function parentHeaders(extra?: HeadersInit): HeadersInit {
  const session = getSession()
  const headers = new Headers(extra)
  if (session?.email) {
    headers.set('X-Parent-Email', session.email)
  }
  return headers
}

export async function parseError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: string }
    if (typeof data.detail === 'string') return data.detail
  } catch {
    /* ignore */
  }
  return `请求失败（${res.status}）`
}

export async function submitGrading(form: FormData): Promise<GradeAttempt> {
  const res = await fetch('/api/grading/attempts', {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchAttempt(id: string): Promise<GradeAttempt> {
  const res = await fetch(`/api/grading/attempts/${id}`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function confirmAttempt(id: string): Promise<GradeAttempt> {
  const res = await fetch(`/api/grading/attempts/${id}/confirm`, {
    method: 'POST',
    headers: parentHeaders(),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchScores(): Promise<{ scores: GradeAttempt[]; guest: boolean }> {
  const res = await fetch('/api/scores', { headers: parentHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchWrongBook(): Promise<{ items: WrongBookItem[]; guest: boolean }> {
  const res = await fetch('/api/wrong-questions', { headers: parentHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
