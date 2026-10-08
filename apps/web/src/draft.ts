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

export type QuestionIllustration = {
  scene?: {
    kind: string
    item: string
    groups: { count: number }[]
  }
  svg?: string
}

export type Question = {
  qtype: string
  stem: string
  options?: string[]
  answer?: string
  illustration?: QuestionIllustration
}

export type QuizPayload = {
  id: string
  title: string
  questions: Question[]
  includeAnswers: boolean
  count: number
  difficulty: string
  source?: 'textbook' | 'chat'
  summary?: string
}

const DRAFT_KEY = 'bangxue-draft'
const QUIZ_KEY = 'bangxue-quiz'
const ERROR_KEY = 'bangxue-quiz-error'

const PRIMARY_GRADES_ALL = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'] as const
const PRIMARY_GRADES_EN = ['三年级', '四年级', '五年级', '六年级'] as const
const PRIMARY_TERMS = new Set(['上册', '下册'])

/** Keep in sync with apps/api/agents/textbook/generate.py allowlist. */
const SUBJECT_EDITIONS: Record<string, string[]> = {
  数学: ['人教版'],
  语文: ['统编版'],
  英语: ['人教版'],
}

const SUBJECT_GRADES: Record<string, readonly string[]> = {
  数学: PRIMARY_GRADES_ALL,
  语文: PRIMARY_GRADES_ALL,
  英语: PRIMARY_GRADES_EN,
}

export const OPEN_BOOK_NOTICE =
  '目前开放：小学数学人教版（一至六上下）、语文统编版（一至六上下）、英语人教版（三至六上下）'

export function defaultEdition(subject: string): string {
  return SUBJECT_EDITIONS[subject]?.[0] ?? '人教版'
}

export function editionsFor(subject: string): string[] {
  return SUBJECT_EDITIONS[subject] ?? ['人教版', '苏教版', '北师大版', '沪教版']
}

export function gradesFor(subject: string): readonly string[] {
  return SUBJECT_GRADES[subject] ?? PRIMARY_GRADES_ALL
}

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
  if (draft.stage !== '小学') return false
  if (draft.subject === '更多') return false
  if (!PRIMARY_TERMS.has(draft.term)) return false
  const editions = SUBJECT_EDITIONS[draft.subject]
  const grades = SUBJECT_GRADES[draft.subject]
  if (!editions || !grades) return false
  return editions.includes(draft.edition) && grades.includes(draft.grade)
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
