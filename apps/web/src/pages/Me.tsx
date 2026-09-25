import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BottomNav, GuestBadge } from '../chrome'
import { BookIcon, ChartIcon, ChevronRight, ProfileUserMark, UserIcon } from '../icons'
import { clearSession, getSession, maskEmail } from '../session'

export default function Me() {
  const navigate = useNavigate()
  const [session, setLocal] = useState(() => getSession())
  const [notice, setNotice] = useState<string | null>(null)

  const loggedIn = Boolean(session)

  return (
    <div className="app-shell">
      <div className="page page-tab">
        <div className="page-head row page-head-row">
          <div>
            <h1 className="page-title">我的</h1>
            <p className="sub">账号、孩子与学习设置</p>
          </div>
          {!loggedIn ? <GuestBadge /> : null}
        </div>

        <button
          className="profile-card"
          type="button"
          onClick={() => {
            if (!loggedIn) navigate('/login')
          }}
        >
          <div className="avatar lg profile-avatar" aria-hidden="true">
            <ProfileUserMark size={24} />
          </div>
          <div className="profile-meta">
            {loggedIn ? (
              <>
                <div className="profile-name">{session!.name}</div>
                <div className="profile-sub">{maskEmail(session!.email)}</div>
              </>
            ) : (
              <>
                <div className="profile-name">点击登录</div>
                <div className="profile-sub">登录后同步成绩与错题本</div>
              </>
            )}
          </div>
          <span className="profile-chevron" aria-hidden="true">
            <ChevronRight />
          </span>
        </button>

        {notice ? <p className="notice" style={{ marginTop: 12 }}>{notice}</p> : null}

        <section className="section">
          <div className="menu-card">
            <button className="menu-row" type="button" onClick={() => navigate('/me/wrong-book')}>
              <span className="menu-ico">
                <BookIcon size={18} />
              </span>
              <span className="menu-label">错题本</span>
              <ChevronRight />
            </button>
            <button className="menu-row" type="button" onClick={() => setNotice('孩子档案尚未开放')}>
              <span className="menu-ico">
                <UserIcon size={18} />
              </span>
              <span className="menu-label">孩子档案</span>
              <ChevronRight />
            </button>
            <button className="menu-row" type="button" onClick={() => navigate('/scores')}>
              <span className="menu-ico">
                <ChartIcon />
              </span>
              <span className="menu-label">成绩记录</span>
              <ChevronRight />
            </button>
          </div>
        </section>

        <section className="section">
          <div className="menu-card">
            <button className="menu-row" type="button" onClick={() => setNotice('设置尚未开放')}>
              <span className="menu-label alone">设置</span>
              <ChevronRight />
            </button>
            <button className="menu-row" type="button" onClick={() => setNotice('帮学 · 家长端一期')}>
              <span className="menu-label alone">关于帮学</span>
              <ChevronRight />
            </button>
          </div>
        </section>

        {loggedIn ? (
          <button
            className="btn btn-outline btn-block"
            style={{ marginTop: 20 }}
            type="button"
            onClick={() => {
              clearSession()
              setLocal(null)
              setNotice('已退出登录')
            }}
          >
            退出登录
          </button>
        ) : (
          <button
            className="btn btn-amber btn-block"
            style={{ marginTop: 20 }}
            type="button"
            onClick={() => navigate('/login')}
          >
            登录 / 注册
          </button>
        )}
      </div>
      <BottomNav active="me" />
    </div>
  )
}
