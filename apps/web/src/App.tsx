import { Route, Routes } from 'react-router-dom'
import Chat from './pages/Chat'
import Config from './pages/Config'
import Home from './pages/Home'
import Placeholder from './pages/Placeholder'
import Range from './pages/Range'
import Result from './pages/Result'
import Select from './pages/Select'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/chat/result" element={<Result />} />
      <Route path="/textbook" element={<Select />} />
      <Route path="/textbook/range" element={<Range />} />
      <Route path="/textbook/config" element={<Config />} />
      <Route path="/textbook/result" element={<Result />} />
      <Route path="/scores" element={<Placeholder title="成绩" active="scores" />} />
      <Route path="/me" element={<Placeholder title="我的" active="me" />} />
    </Routes>
  )
}
