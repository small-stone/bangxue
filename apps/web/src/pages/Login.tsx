import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { BookIcon } from '../icons'
import { DEMO_LOGIN_CODE, setSession } from '../session'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function sendCode() {
    const trimmed = email.trim()
    if (!EMAIL_RE.test(trimmed)) {
      setError('请输入有效邮箱')
      return
    }
    setError(null)
    setSent(true)
    // Demo only: no SMTP; user must type DEMO_LOGIN_CODE
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = email.trim()
    if (!EMAIL_RE.test(trimmed)) {
      setError('请输入有效邮箱')
      return
    }
    if (code.trim() !== DEMO_LOGIN_CODE) {
      setError(`验证码错误，演示环境请输入 ${DEMO_LOGIN_CODE}`)
      return
    }
    setSession({ email: trimmed, name: '家长' })
    navigate('/me', { replace: true })
  }

  return (
    <div className="app-shell">
      <div className="page login-page">
        <PageNav title="登录" hideGuest />

        <div className="login-hero">
          <div className="brand-lockup">
            <div className="brand-mark">
              <BookIcon size={22} />
            </div>
            <div className="brand-word">
              <div className="name">
                <em>帮</em>学
              </div>
              <div className="hint">BANG XUE</div>
            </div>
          </div>
          <h1 className="greet" style={{ fontSize: 24, marginTop: 20 }}>
            欢迎回来
          </h1>
          <p className="sub">登录后可同步成绩与错题；也可先游客使用</p>
        </div>

        <form className="login-form" onSubmit={onSubmit}>
          <label className="field">
            <span className="field-label">邮箱</span>
            <input
              type="email"
              autoComplete="email"
              placeholder="请输入邮箱"
              value={email}
              onChange={(event) => setEmail(event.target.value.trimStart())}
            />
          </label>

          <label className="field">
            <span className="field-label">验证码</span>
            <div className="field-row">
              <input
                inputMode="numeric"
                maxLength={4}
                placeholder="请输入邮箱验证码"
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 4))}
              />
              <button className="btn btn-outline btn-sm code-btn" type="button" onClick={sendCode}>
                {sent ? '已发送' : '发送验证码'}
              </button>
            </div>
          </label>

          {error ? <p className="notice">{error}</p> : null}
          {sent && !error ? (
            <p className="hint-line">演示环境未发信，请输入验证码 {DEMO_LOGIN_CODE}</p>
          ) : null}

          <button className="btn btn-amber btn-block" type="submit">
            登录
          </button>
          <button className="btn btn-outline btn-block" type="button" onClick={() => navigate('/')}>
            游客继续使用
          </button>
        </form>
      </div>
    </div>
  )
}
