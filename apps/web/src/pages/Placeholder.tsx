import { BottomNav } from '../chrome'

export default function Placeholder({ title, active }: { title: string; active: 'scores' | 'me' }) {
  return (
    <div className="app-shell">
      <div className="page">
        <h1 className="greet">{title}</h1>
        <p className="notice">尚未开放</p>
      </div>
      <BottomNav active={active} />
    </div>
  )
}
