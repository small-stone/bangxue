import { useNavigate } from 'react-router-dom'
import { ChartIcon, ChevronLeft, HomeIcon, UserIcon } from './icons'

export function PageNav({ title, badge }: { title: string; badge?: string }) {
  const navigate = useNavigate()
  return (
    <div className="nav">
      <button className="back" type="button" aria-label="返回" onClick={() => navigate(-1)}>
        <ChevronLeft />
      </button>
      <h1>{title}</h1>
      {badge ? <span className="badge">{badge}</span> : <span style={{ width: 32 }} />}
    </div>
  )
}

export function BottomNav({ active }: { active: 'home' | 'scores' | 'me' }) {
  const navigate = useNavigate()
  return (
    <div className="tab-dock">
      <div className="tabs">
        <button className={active === 'home' ? 'tab active' : 'tab'} type="button" onClick={() => navigate('/')}>
          <HomeIcon />
          首页
        </button>
        <button className={active === 'scores' ? 'tab active' : 'tab'} type="button" onClick={() => navigate('/scores')}>
          <ChartIcon />
          成绩
        </button>
        <button className={active === 'me' ? 'tab active' : 'tab'} type="button" onClick={() => navigate('/me')}>
          <UserIcon />
          我的
        </button>
      </div>
    </div>
  )
}
