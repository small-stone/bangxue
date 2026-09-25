import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BottomNav, GuestBadge } from '../chrome'
import { BookIcon, MessageIcon, UserIcon } from '../icons'

export default function Home() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<'textbook' | 'chat' | null>(null)

  return (
    <div className="app-shell">
      <div className="page home">
        <div className="row">
          <div className="brand-lockup">
            <div className="brand-mark">
              <BookIcon size={20} />
            </div>
            <div className="brand-word">
              <div className="name">
                <em>帮</em>学
              </div>
              <div className="hint">BANG XUE</div>
            </div>
          </div>
          <div className="home-actions">
            <GuestBadge />
            <button className="avatar" type="button" aria-label="我的" onClick={() => navigate('/me')}>
              <UserIcon />
            </button>
          </div>
        </div>
        <h1 className="greet">你好，家长</h1>
        <p className="sub">为孩子智能出题与判分 · 教材 / 对话双入口</p>
        <div className="stack-gap">
          <button
            className={selected === 'textbook' ? 'card amber' : 'card'}
            type="button"
            onClick={() => {
              setSelected('textbook')
              navigate('/textbook')
            }}
          >
            <div className="icon-well">
              <BookIcon size={22} />
            </div>
            <div className="card-title">按教材出题</div>
            <div className="card-desc">选单元与学期，紧扣课本组卷</div>
          </button>
          <button
            className={selected === 'chat' ? 'card amber' : 'card'}
            type="button"
            onClick={() => {
              setSelected('chat')
              navigate('/chat')
            }}
          >
            <div className="icon-well">
              <MessageIcon size={22} />
            </div>
            <div className="card-title">对话出题</div>
            <div className="card-desc">用一句话说出练习需求</div>
          </button>
        </div>
        <section className="section">
          <div className="section-label">待办</div>
          <div className="todo">
            <div className="icon-well" style={{ margin: 0 }}>
              <BookIcon size={18} />
            </div>
            <div className="meta">
              待拍照判分
              <br />
              三年级数学第二单元
            </div>
            <button className="btn btn-amber btn-sm" type="button" onClick={() => navigate('/grade/upload')}>
              去上传
            </button>
          </div>
        </section>
        <section className="section">
          <div className="section-label">最近练习</div>
          <div className="practice">
            <div className="top">
              <span className="subj-dot">数</span>
              <span>10-24</span>
              <b>数学</b>
              <span className="tag">教材</span>
              <span className="score">18/20 · 90%</span>
            </div>
            <div className="bar">
              <i style={{ width: '90%' }} />
            </div>
          </div>
          <div className="practice">
            <div className="top">
              <span className="subj-dot">英</span>
              <span>10-23</span>
              <b>英语</b>
              <span className="tag">对话</span>
              <span className="score">16/20 · 80%</span>
            </div>
            <div className="bar">
              <i style={{ width: '80%' }} />
            </div>
          </div>
        </section>
      </div>
      <BottomNav active="home" />
    </div>
  )
}
