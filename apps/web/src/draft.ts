export type ScopeMode = 'unit' | 'half' | 'term'

export type Draft = {
  stage: '小学' | '初中'
  grade: string
  subject: string
  edition: string
  term: '上册' | '下册'
  scope: ScopeMode
  units: string[]
  count: number
  difficulty: string
  includeAnswers: boolean
}

export type Question = {
  qtype: string
  stem: string
  answer?: string
}

export type QuizPayload = {
  id: string
  title: string
  questions: Question[]
  includeAnswers: boolean
  count: number
  difficulty: string
}

const DRAFT_KEY = 'bangxue-draft'
const QUIZ_KEY = 'bangxue-quiz'
const ERROR_KEY = 'bangxue-quiz-error'

const PRIMARY_GRADES = new Set(['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'])

export const emptyDraft = (): Draft => ({
  stage: '小学',
  grade: '一年级',
  subject: '数学',
  edition: '人教版',
  term: '上册',
  scope: 'unit',
  units: [],
  count: 15,
  difficulty: '适中',
  includeAnswers: true,
})

export function loadDraft(): Draft {
  const raw = sessionStorage.getItem(DRAFT_KEY)
  if (!raw) return emptyDraft()
  return { ...emptyDraft(), ...JSON.parse(raw) }
}

export function saveDraft(draft: Draft) {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
}

export function canContinue(draft: Draft) {
  return (
    draft.stage === '小学' &&
    draft.subject === '数学' &&
    draft.edition === '人教版' &&
    PRIMARY_GRADES.has(draft.grade) &&
    (draft.term === '上册' || draft.term === '下册')
  )
}

export function saveQuiz(quiz: QuizPayload) {
  sessionStorage.setItem(QUIZ_KEY, JSON.stringify(quiz))
  sessionStorage.removeItem(ERROR_KEY)
}

export function saveQuizError(message: string) {
  sessionStorage.setItem(ERROR_KEY, message)
  sessionStorage.removeItem(QUIZ_KEY)
}

export function loadQuiz(): QuizPayload | null {
  const raw = sessionStorage.getItem(QUIZ_KEY)
  return raw ? JSON.parse(raw) : null
}

export function loadQuizError(): string | null {
  return sessionStorage.getItem(ERROR_KEY)
}
