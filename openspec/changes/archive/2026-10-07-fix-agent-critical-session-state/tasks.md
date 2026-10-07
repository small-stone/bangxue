# Tasks

## 1. Schema and session store

- [x] 1.1 Add `chat_sessions` table + ensure_schema (fail-closed on missing `DATABASE_URL`), mirroring `score_store` patterns. Verify: unit/integration test creates table and upserts one row when DB available; missing URL raises clear error.
- [x] 1.2 Implement load/save/exists for chat sessions and wire `create_session` / `get_session` / `session_exists` to use DB as authority (optional process cache). Verify: restart simulation (clear cache, reload from DB) restores messages/draft; pytest covers happy path + missing session 404.
- [x] 1.3 Call session schema ensure from API lifespan alongside scores. Verify: starting API with valid `DATABASE_URL` creates table without manual SQL.

## 2. Quiz paper store

- [x] 2.1 Add `quiz_papers` table with TTL (`expires_at`, default 7 days, optional env override) and replace `quiz_store` authority with Postgres. Verify: `save_quiz` then clear cache then `get_quiz` returns same payload; expired row returns None.
- [x] 2.2 Ensure confirm-chat and textbook `POST /api/quizzes` both persist via the new store; PDF/grade paths still resolve by id. Verify: pytest or manual curl create quiz → get quiz after process-local cache clear.

## 3. Checkpoint namespace isolation

- [x] 3.1 Set chat harness checkpointer config to `checkpoint_ns="chat-agent"` (create/exists/invoke paths). Verify: harness unit test asserts ns string in config; no remaining production `checkpoint_ns=""` for chat.
- [x] 3.2 Set Supervisor invoke config to `checkpoint_ns="supervisor"`. Verify: supervisor test asserts distinct ns; shared `thread_id` does not read chat-agent checkpoint as supervisor state.
- [x] 3.3 Update supervisor/chat tests that seed `_SESSIONS` to use the session store API. Verify: `pytest` for supervisor + chat-related tests pass.

## 4. Spec alignment and docs

- [x] 4.1 Remove any remaining UI/API “对话出题尚未开放” behavior if present; confirm homepage chat entry works. Verify: chat entry navigates/creates session (manual or existing e2e notes).
- [x] 4.2 Document `chat_sessions` / `quiz_papers`, TTL, and checkpoint ns in README (or ops note). Verify: README mentions DB tables + fail-closed + ns names.
- [x] 4.3 Run focused pytest suite for store/supervisor/harness changes. Verify: suite green under project `.venv`.
