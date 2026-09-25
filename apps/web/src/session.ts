const KEY = 'bangxue-session'

/** Demo-only verification code; no SMTP in this phase. */
export const DEMO_LOGIN_CODE = '0000'

export type Session = {
  email: string
  name: string
}

export function getSession(): Session | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Session> & { phone?: string }
    if (typeof parsed.email === 'string' && parsed.email.includes('@')) {
      return {
        email: parsed.email.trim(),
        name: typeof parsed.name === 'string' && parsed.name ? parsed.name : '家长',
      }
    }
    // Drop legacy phone-only or invalid payloads
    localStorage.removeItem(KEY)
    return null
  } catch {
    localStorage.removeItem(KEY)
    return null
  }
}

export function isLoggedIn(): boolean {
  return getSession() !== null
}

export function setSession(session: Session): void {
  localStorage.setItem(
    KEY,
    JSON.stringify({ email: session.email.trim(), name: session.name || '家长' }),
  )
}

export function clearSession(): void {
  localStorage.removeItem(KEY)
}

export function maskEmail(email: string): string {
  const at = email.indexOf('@')
  if (at <= 1) return email
  const name = email.slice(0, at)
  const domain = email.slice(at)
  if (name.length <= 2) return `${name[0]}*${domain}`
  return `${name.slice(0, 2)}***${domain}`
}
