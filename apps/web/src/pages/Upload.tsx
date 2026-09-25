import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitGrading } from '../api'
import { PageNav } from '../chrome'
import { loadDraft, loadQuiz } from '../draft'
import { BookIcon, CameraIcon, CheckIcon, ImageIcon, InfoIcon, SearchIcon } from '../icons'

type PageSlot = { id: string; file: File; preview: string }

export default function Upload() {
  const navigate = useNavigate()
  const cameraRef = useRef<HTMLInputElement>(null)
  const albumRef = useRef<HTMLInputElement>(null)
  const [pages, setPages] = useState<PageSlot[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const quiz = loadQuiz()
  const draft = loadDraft()
  const subject =
    quiz?.source === 'chat' ? '综合' : draft.subject || '数学'
  const contextLabel = quiz
    ? quiz.source === 'chat'
      ? quiz.summary || quiz.title
      : quiz.title
    : null

  function addFiles(fileList: FileList | null) {
    if (!fileList?.length) return
    const next: PageSlot[] = []
    Array.from(fileList).forEach((file) => {
      if (!file.type.startsWith('image/')) return
      next.push({
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        preview: URL.createObjectURL(file),
      })
    })
    if (next.length) {
      setPages((prev) => [...prev, ...next])
      setError(null)
    }
  }

  async function startGrading() {
    if (!pages.length) {
      setError('请先拍摄或选择答卷照片')
      return
    }
    if (!quiz) {
      setError('练习已失效，请重新出题后再上传')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const form = new FormData()
      pages.forEach((page) => form.append('photos', page.file))
      if (quiz.id) form.append('quiz_id', quiz.id)
      form.append(
        'questions_json',
        JSON.stringify({
          title: quiz.title,
          subject,
          source: quiz.source || 'textbook',
          questions: quiz.questions,
        }),
      )
      form.append('source', quiz.source || 'textbook')
      form.append('title', quiz.title)
      form.append('subject', subject)
      const attempt = await submitGrading(form)
      navigate(`/grade/result/${attempt.id}`, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '判分失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <div className="page">
        <PageNav title="拍照上传答卷" />
        {quiz ? (
          <div className="chips" style={{ marginTop: 8 }}>
            <span className="tag">
              <BookIcon size={12} />
              {contextLabel}
            </span>
            <span className="tag">{quiz.count} 题</span>
          </div>
        ) : (
          <p className="notice error" style={{ marginTop: 12 }}>
            练习已失效，请重新出题后再上传
          </p>
        )}

        <button
          className="upload-drop"
          type="button"
          disabled={!quiz || busy}
          onClick={() => cameraRef.current?.click()}
        >
          <span className="upload-cam">
            <CameraIcon size={26} />
          </span>
          <span className="upload-title">拍摄答卷</span>
          <span className="upload-sub">或从相册选择</span>
        </button>
        <button
          className="link-action"
          type="button"
          disabled={!quiz || busy}
          onClick={() => albumRef.current?.click()}
        >
          <ImageIcon size={16} /> 从相册选择
        </button>

        <input
          ref={cameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          hidden
          onChange={(e) => {
            addFiles(e.target.files)
            e.target.value = ''
          }}
        />
        <input
          ref={albumRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => {
            addFiles(e.target.files)
            e.target.value = ''
          }}
        />

        <div className="page-thumbs">
          {pages.map((page, index) => (
            <div className="page-thumb on" key={page.id}>
              <img src={page.preview} alt={`第${index + 1}页`} />
              <span className="page-thumb-check">
                <CheckIcon size={12} />
              </span>
              <span className="page-thumb-label">第{index + 1}页</span>
            </div>
          ))}
          {quiz ? (
            <button
              className="page-thumb add"
              type="button"
              disabled={busy}
              onClick={() => albumRef.current?.click()}
            >
              <span className="plus">+</span>
              <span className="page-thumb-label">第{pages.length + 1}页</span>
            </button>
          ) : null}
        </div>

        <div className="info-banner">
          <InfoIcon />
          照片清晰、整页入镜，识别更准
        </div>

        {error ? <p className="notice error">{error}</p> : null}

        <button
          className="btn btn-amber btn-block"
          type="button"
          disabled={!quiz || !pages.length || busy}
          onClick={() => void startGrading()}
        >
          <SearchIcon size={18} /> {busy ? '判分中…' : '开始判分'}
        </button>
      </div>
    </div>
  )
}
