import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  OPEN_BOOK_NOTICE,
  canContinue,
  defaultEdition,
  editionsFor,
  loadDraft,
  saveDraft,
  type Draft,
} from '../draft'
import { PageNav } from '../chrome'
import { ChevronRight } from '../icons'

const GRADES = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
const TERMS = ['上册', '下册'] as const
const SUBJECTS = [
  { name: '语文', hint: '阅读与表达' },
  { name: '数学', hint: '逻辑与计算' },
  { name: '英语', hint: '听说读写' },
  { name: '更多', hint: '后续开放' },
]

export default function Select() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const ready = canContinue(draft)
  const editionOptions = editionsFor(draft.subject)

  function update(patch: Partial<Draft>) {
    const next = { ...draft, ...patch, units: [] }
    if (patch.subject !== undefined) {
      const allowed = editionsFor(patch.subject)
      if (!allowed.includes(next.edition)) {
        next.edition = defaultEdition(patch.subject)
      }
    }
    setDraft(next)
    saveDraft(next)
  }

  function next() {
    if (!ready) return
    saveDraft(draft)
    navigate('/textbook/range')
  }

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="按教材出题" />
        <div className="banner">紧扣课本单元出题</div>
        {!ready ? <p className="notice">{OPEN_BOOK_NOTICE}</p> : null}
        <div className="seg">
          {(['小学', '初中'] as const).map((stage) => (
            <button key={stage} type="button" className={draft.stage === stage ? 'on' : ''} onClick={() => update({ stage })}>
              {stage}
            </button>
          ))}
        </div>
        <div className="label">选择年级</div>
        <div className="chips">
          {GRADES.map((grade) => (
            <button key={grade} type="button" className={draft.grade === grade ? 'chip on' : 'chip'} onClick={() => update({ grade })}>
              {grade}
            </button>
          ))}
        </div>
        <div className="label">选择学期</div>
        <div className="chips">
          {TERMS.map((term) => (
            <button key={term} type="button" className={draft.term === term ? 'chip on' : 'chip'} onClick={() => update({ term })}>
              {term}
            </button>
          ))}
        </div>
        <div className="label">选择科目</div>
        <div className="grid2">
          {SUBJECTS.map((subject) => (
            <button
              key={subject.name}
              type="button"
              className={draft.subject === subject.name ? 'subj on' : 'subj'}
              onClick={() => update({ subject: subject.name })}
            >
              <div className="ic">{subject.name.slice(0, 1)}</div>
              <b>{subject.name}</b>
              <span>{subject.hint}</span>
            </button>
          ))}
        </div>
        <div className="label">选择教材版本</div>
        <div className="chips">
          {editionOptions.map((edition) => (
            <button
              key={edition}
              type="button"
              className={draft.edition === edition ? 'chip on' : 'chip'}
              onClick={() => update({ edition })}
            >
              {edition}
            </button>
          ))}
        </div>
        <div className="bottom-cta">
          <button className="btn btn-amber btn-block" type="button" disabled={!ready} onClick={next}>
            下一步
            <ChevronRight />
          </button>
        </div>
      </div>
    </div>
  )
}
