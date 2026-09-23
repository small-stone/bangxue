import { Route, Routes } from 'react-router-dom'

export default function App() {
  return (
    <div className="min-h-dvh bg-stone-50 text-stone-900">
      <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-3 px-6">
        <h1 className="text-2xl font-semibold tracking-tight">帮学</h1>
        <p className="text-sm text-stone-600">家长端移动 Web 脚手架已就绪。</p>
        <Routes>
          <Route path="/" element={<p className="text-sm text-stone-500">首页占位</p>} />
        </Routes>
      </main>
    </div>
  )
}
