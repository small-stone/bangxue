import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { canContinue, loadDraft, saveDraft, type Draft, type ScopeMode } from '../draft'
import { ChevronRight } from '../icons'

const SCOPES: { id: ScopeMode; title: string; hint: string }[] = [
  { id: 'unit', title: '按单元', hint: '选择某一单元或若干单元' },
  { id: 'half', title: '半学期', hint: '覆盖半学期所学内容' },
  { id: 'term', title: '整学期', hint: '覆盖整学期所学内容' },
]

function unitsFor(scope: ScopeMode, all: string[], picked: string[]) {
  if (scope === 'term') return all
  if (scope === 'half') return all.slice(0, Math.ceil(all.length / 2))
  return picked.filter((name) => all.includes(name))
}

export default function Range() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const [allUnits, setAllUnits] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!canContinue(draft)) {
      navigate('/textbook', { replace: true })
      return
    }
    const params = new URLSearchParams({
      stage: draft.stage,
      grade: draft.grade,
      subject: draft.subject,
      edition: draft.edition,
      term: draft.term,
    })
    fetch(`/api/textbooks/units?${params}`)
      .then(async (response) => {
        const body = await response.json()
        if (!response.ok) throw new Error(body.detail || '无法读取单元')
        setAllUnits(body.units)
      })
      .catch((err: Error) => setError(err.message))
  }, [draft.stage, draft.grade, draft.subject, draft.edition, draft.term, navigate])

  const selected = unitsFor(draft.scope, allUnits, draft.units)

  function chooseScope(scope: ScopeMode) {
    const next = { ...draft, scope, units: unitsFor(scope, allUnits, draft.units) }
    setDraft(next)
    saveDraft(next)
  }

  function toggleUnit(name: string) {
    if (draft.scope !== 'unit') return
    const units = draft.units.includes(name) ? draft.units.filter((item) => item !== name) : [...draft.units, name]
    const next = { ...draft, units }
    setDraft(next)
    saveDraft(next)
  }

  function next() {
    const units = unitsFor(draft.scope, allUnits, draft.units)
    if (units.length === 0) return
    const saved = { ...draft, units }
    saveDraft(saved)
    navigate('/textbook/config')
  }

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="选择出题范围" />
        <div className="ctx">
          <span className="tag">{draft.grade}</span>
          <span className="tag">{draft.term}</span>
          <span className="tag">{draft.subject}</span>
          <span className="tag">{draft.edition}</span>
        </div>
        {error ? <p className="notice error">{error}</p> : null}
        {SCOPES.map((scope) => (
          <button
            key={scope.id}
            type="button"
            className={draft.scope === scope.id ? 'option on' : 'option'}
            onClick={() => chooseScope(scope.id)}
          >
            <div className="ic">{scope.title.slice(0, 1)}</div>
            <div>
              <b>{scope.title}</b>
              <div className="hint">{scope.hint}</div>
            </div>
          </button>
        ))}
        <div className="label">选择单元</div>
        <div className="chips">
          {allUnits.map((name) => (
            <button
              key={name}
              type="button"
              className={selected.includes(name) ? 'chip on' : 'chip'}
              onClick={() => toggleUnit(name)}
            >
              {name}
            </button>
          ))}
        </div>
        <div className="bottom-cta">
          <button className="btn btn-amber btn-block" type="button" disabled={selected.length === 0} onClick={next}>
            下一步
            <ChevronRight />
          </button>
        </div>
      </div>
    </div>
  )
}
