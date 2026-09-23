import { useNavigate } from 'react-router-dom'
import { PageNav } from '../chrome'
import { loadQuiz, loadQuizError } from '../draft'

export default function Result() {
  const navigate = useNavigate()
  const quiz = loadQuiz()
  const error = loadQuizError()

  if (error || !quiz) {
    return (
      <div className="app-shell">
        <div className="page">
          <PageNav title="暂时无法出题" />
          <p className="notice error">{error || '暂时无法出题'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell result-screen">
      <header className="result-head">
        <PageNav title="练习卷已生成" />
        <div className="celebrate">
          <span className="check">✓</span>
          可以打印啦
        </div>
      </header>
      <div className="result-frame">
        <article className="paper-sheet">
          <div className="paper-scroll">
            <h2>{quiz.title}</h2>
            {quiz.questions.map((question, index) => (
              <div className="q" key={`${index}-${question.stem}`}>
                <p>
                  {index + 1}. {question.stem}
                  {quiz.includeAnswers && question.answer ? (
                    <span className="answer"> 答案：{question.answer}</span>
                  ) : null}
                </p>
                {question.options && question.options.length > 0 ? (
                  <ul className="q-options">
                    {question.options.map((option) => (
                      <li key={option}>{option}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
            <div className="chips" style={{ marginTop: 14 }}>
              <span className="tag">{quiz.source === 'chat' ? '对话' : '教材'}</span>
              <span className="tag">{quiz.count} 题</span>
              <span className="tag">{quiz.difficulty}</span>
              {quiz.includeAnswers ? <span className="tag">含答案卷</span> : null}
            </div>
          </div>
        </article>
      </div>
      <footer className="result-foot">
        <a className="btn btn-amber btn-block" href={`/api/quizzes/${quiz.id}/paper.pdf`}>
          下载 PDF
        </a>
        {quiz.includeAnswers ? (
          <a className="btn btn-outline amber btn-block" href={`/api/quizzes/${quiz.id}/answers.pdf`}>
            下载答案卷
          </a>
        ) : null}
        <button className="link-action" type="button" onClick={() => navigate(quiz.source === 'chat' ? '/chat' : '/textbook/config')}>
          再调整题目
        </button>
      </footer>
    </div>
  )
}
