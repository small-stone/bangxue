import type { GradeAttempt, WrongBookItem } from './api'

/** Demo score rows aligned with mockup-07-scores. */
export const DEMO_SCORES: GradeAttempt[] = [
  {
    id: 'demo-score-1',
    confirmed: true,
    demo: true,
    source: 'textbook',
    subject: '数学',
    title: '三年级 · 第二单元',
    correct: 18,
    total: 20,
    items: [],
    confirmed_at: '2025-10-24T10:00:00Z',
    created_at: '2025-10-24T10:00:00Z',
  },
  {
    id: 'demo-score-2',
    confirmed: true,
    demo: true,
    source: 'chat',
    subject: '英语',
    title: 'Unit 2 单词练习',
    correct: 16,
    total: 20,
    items: [],
    confirmed_at: '2025-10-23T10:00:00Z',
    created_at: '2025-10-23T10:00:00Z',
  },
  {
    id: 'demo-score-3',
    confirmed: true,
    demo: true,
    source: 'chat',
    subject: '数学',
    title: '20 以内加减法',
    correct: 9,
    total: 10,
    items: [],
    confirmed_at: '2025-10-21T10:00:00Z',
    created_at: '2025-10-21T10:00:00Z',
  },
  {
    id: 'demo-score-4',
    confirmed: true,
    demo: true,
    source: 'textbook',
    subject: '语文',
    title: '第三单元 · 课文朗读',
    correct: 10,
    total: 10,
    items: [],
    confirmed_at: '2025-10-20T10:00:00Z',
    created_at: '2025-10-20T10:00:00Z',
  },
]

/** Relative heights (%) for the 7-day spark chart (Mon–Sun). */
export const DEMO_SPARK_HEIGHTS = [42, 58, 36, 78, 64, 88, 72] as const

export const DEMO_SPARK_PEAK_LABEL = '最高 95%'

export type DemoWrongItem = WrongBookItem & {
  icon?: 'clock' | 'calc' | 'edit'
}

export const DEMO_WRONG_ITEMS: DemoWrongItem[] = [
  {
    attempt_id: 'demo-wrong-1',
    subject: '数学',
    title: '三年级 · 第二单元',
    source: 'textbook',
    date: '10-24',
    index: 3,
    stem: '时针指向 2，分针指向 12，现在是几点？',
    student_answer: '3:00',
    answer: '2:00',
    icon: 'clock',
  },
  {
    attempt_id: 'demo-wrong-2',
    subject: '数学',
    title: '三年级 · 第二单元',
    source: 'textbook',
    date: '10-24',
    index: 7,
    stem: '计算：38 + 27 = ?',
    student_answer: '55',
    answer: '65',
    icon: 'calc',
  },
  {
    attempt_id: 'demo-wrong-3',
    subject: '英语',
    title: 'Unit 2 单词练习',
    source: 'chat',
    date: '10-23',
    index: 2,
    stem: '选出 “苹果” 的正确拼写',
    student_answer: 'appel',
    answer: 'apple',
    icon: 'edit',
  },
]

export const DEMO_WRONG_STATS = { pendingReview: 6, weekNew: 2 } as const

export function isDemoId(id: string | undefined | null): boolean {
  return Boolean(id && id.startsWith('demo-'))
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
