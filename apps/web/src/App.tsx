import { Route, Routes } from 'react-router-dom'
import Chat from './pages/Chat'
import Config from './pages/Config'
import GradeResult from './pages/GradeResult'
import Home from './pages/Home'
import Login from './pages/Login'
import Me from './pages/Me'
import Range from './pages/Range'
import Result from './pages/Result'
import Scores from './pages/Scores'
import Select from './pages/Select'
import Upload from './pages/Upload'
import WrongBook from './pages/WrongBook'
import WrongQuestions from './pages/WrongQuestions'

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
      <Route path="/grade/upload" element={<Upload />} />
      <Route path="/grade/result/:attemptId" element={<GradeResult />} />
      <Route path="/grade/wrong/:attemptId" element={<WrongQuestions />} />
      <Route path="/scores" element={<Scores />} />
      <Route path="/me" element={<Me />} />
      <Route path="/me/wrong-book" element={<WrongBook />} />
      <Route path="/login" element={<Login />} />
    </Routes>
  )
}
