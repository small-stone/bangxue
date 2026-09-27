import type { GradeAttempt, GradeItem, WrongBookItem } from './api'

type WrongSpec = {
  index: number
  stem: string
  answer: string
  student_answer: string
  icon?: 'clock' | 'calc' | 'edit'
}

function buildItems(total: number, wrongs: WrongSpec[], okStem: string): GradeItem[] {
  const wrongByIndex = new Map(wrongs.map((w) => [w.index, w]))
  const items: GradeItem[] = []
  for (let i = 1; i <= total; i += 1) {
    const wrong = wrongByIndex.get(i)
    if (wrong) {
      items.push({
        index: i,
        stem: wrong.stem,
        correct: false,
        answer: wrong.answer,
        student_answer: wrong.student_answer,
      })
    } else {
      items.push({
        index: i,
        stem: `${okStem}（第 ${i} 题）`,
        correct: true,
        answer: '略',
        student_answer: '略',
      })
    }
  }
  return items
}

function assertScore(attempt: GradeAttempt): GradeAttempt {
  const correct = attempt.items.filter((item) => item.correct).length
  if (attempt.items.length !== attempt.total || correct !== attempt.correct) {
    throw new Error(`Demo fixture mismatch for ${attempt.id}`)
  }
  return attempt
}

const SCORE1_WRONGS: WrongSpec[] = [
  {
    index: 3,
    stem: '时针指向 2，分针指向 12，现在是几点？',
    student_answer: '3:00',
    answer: '2:00',
    icon: 'clock',
  },
  {
    index: 7,
    stem: '计算：38 + 27 = ?',
    student_answer: '55',
    answer: '65',
    icon: 'calc',
  },
]

const SCORE2_WRONGS: WrongSpec[] = [
  {
    index: 2,
    stem: '选出 “苹果” 的正确拼写',
    student_answer: 'appel',
    answer: 'apple',
    icon: 'edit',
  },
  {
    index: 5,
    stem: '选出 “学校” 的正确拼写',
    student_answer: 'scholl',
    answer: 'school',
    icon: 'edit',
  },
  {
    index: 9,
    stem: '选出 “朋友” 的正确拼写',
    student_answer: 'freind',
    answer: 'friend',
    icon: 'edit',
  },
  {
    index: 14,
    stem: '选出 “黄色” 的正确拼写',
    student_answer: 'yello',
    answer: 'yellow',
    icon: 'edit',
  },
]

const SCORE3_WRONGS: WrongSpec[] = [
  {
    index: 4,
    stem: '计算：15 − 8 = ?',
    student_answer: '6',
    answer: '7',
    icon: 'calc',
  },
]

/** Demo score rows aligned with mockup-07-scores (with per-question items). */
export const DEMO_SCORES: GradeAttempt[] = [
  assertScore({
    id: 'demo-score-1',
    confirmed: true,
    demo: true,
    source: 'textbook',
    subject: '数学',
    title: '三年级 · 第二单元',
    correct: 18,
    total: 20,
    items: buildItems(20, SCORE1_WRONGS, '认识钟表与加减练习'),
    confirmed_at: '2025-10-24T10:00:00Z',
    created_at: '2025-10-24T10:00:00Z',
  }),
  assertScore({
    id: 'demo-score-2',
    confirmed: true,
    demo: true,
    source: 'chat',
    subject: '英语',
    title: 'Unit 2 单词练习',
    correct: 16,
    total: 20,
    items: buildItems(20, SCORE2_WRONGS, '单词选择'),
    confirmed_at: '2025-10-23T10:00:00Z',
    created_at: '2025-10-23T10:00:00Z',
  }),
  assertScore({
    id: 'demo-score-3',
    confirmed: true,
    demo: true,
    source: 'chat',
    subject: '数学',
    title: '20 以内加减法',
    correct: 9,
    total: 10,
    items: buildItems(10, SCORE3_WRONGS, '口算练习'),
    confirmed_at: '2025-10-21T10:00:00Z',
    created_at: '2025-10-21T10:00:00Z',
  }),
  assertScore({
    id: 'demo-score-4',
    confirmed: true,
    demo: true,
    source: 'textbook',
    subject: '语文',
    title: '第三单元 · 课文朗读',
    correct: 10,
    total: 10,
    items: buildItems(10, [], '课文朗读跟读'),
    confirmed_at: '2025-10-20T10:00:00Z',
    created_at: '2025-10-20T10:00:00Z',
  }),
]

/** Relative heights (%) for the 7-day spark chart (Mon–Sun). */
export const DEMO_SPARK_HEIGHTS = [42, 58, 36, 78, 64, 88, 72] as const

export const DEMO_SPARK_PEAK_LABEL = '最高 95%'

export type DemoWrongItem = WrongBookItem & {
  icon?: 'clock' | 'calc' | 'edit'
}

const WRONG_ICON_BY_KEY = new Map<string, DemoWrongItem['icon']>(
  [...SCORE1_WRONGS, ...SCORE2_WRONGS, ...SCORE3_WRONGS].map((w) => [
    `${w.stem}|${w.index}`,
    w.icon,
  ]),
)

function formatDemoDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(5, 10)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${mm}-${dd}`
}

/** Derived from DEMO_SCORES so attempt ids stay in sync. */
export const DEMO_WRONG_ITEMS: DemoWrongItem[] = DEMO_SCORES.flatMap((attempt) =>
  attempt.items
    .filter((item) => !item.correct)
    .map((item) => ({
      attempt_id: attempt.id,
      subject: attempt.subject,
      title: attempt.title,
      source: attempt.source,
      date: formatDemoDate(attempt.confirmed_at || attempt.created_at),
      index: item.index,
      stem: item.stem,
      student_answer: item.student_answer,
      answer: item.answer,
      icon: WRONG_ICON_BY_KEY.get(`${item.stem}|${item.index}`),
    })),
)

export const DEMO_WRONG_STATS = {
  pendingReview: DEMO_WRONG_ITEMS.length,
  weekNew: Math.min(DEMO_WRONG_ITEMS.length, 2),
} as const

export function isDemoId(id: string | undefined | null): boolean {
  return Boolean(id && id.startsWith('demo-'))
}

export function getDemoAttempt(id: string): GradeAttempt | null {
  return DEMO_SCORES.find((item) => item.id === id) ?? null
}

/** Prefer real logged-in data; otherwise fall back to showcase samples. */
export function pickScoreShowcase(
  loggedIn: boolean,
  apiScores: GradeAttempt[],
): { scores: GradeAttempt[]; demo: boolean } {
  if (loggedIn && apiScores.length > 0) {
    return { scores: apiScores, demo: false }
  }
  return { scores: DEMO_SCORES, demo: true }
}

export function pickWrongShowcase(
  loggedIn: boolean,
  apiItems: WrongBookItem[],
): {
  items: DemoWrongItem[]
  demo: boolean
  pendingReview: number
  weekNew: number
} {
  if (loggedIn && apiItems.length > 0) {
    return {
      items: apiItems,
      demo: false,
      pendingReview: apiItems.length,
      weekNew: Math.min(apiItems.length, 2),
    }
  }
  return {
    items: DEMO_WRONG_ITEMS,
    demo: true,
    pendingReview: DEMO_WRONG_STATS.pendingReview,
    weekNew: DEMO_WRONG_STATS.weekNew,
  }
}
