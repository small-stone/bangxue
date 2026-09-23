# Tasks

## 1. Shared runtime foundations

- [x] 1.1 Add or reuse Bailian chat model factory in `agents/shared` (`bailian_api_key`, `QUIZ_MODEL` default `qwen3.7-plus`) and verify a one-shot invoke returns non-empty content when key is present (or raises a clear config error when missing)
- [x] 1.2 Add Jev client stub/module in `agents/shared` for completeness judgment (env key only) and verify missing key raises a clear error without inventing a “enough” result
- [x] 1.3 Wire Postgres LangGraph checkpointer for chat threads (no MemorySaver in the default path) and verify creating a session persists under a `thread_id` across two API process calls or an equivalent smoke check

## 2. DeepAgents chat harness

- [x] 2.1 Implement `agents/chat.build_agent()` with `create_deep_agent`, draft-quiz tool only, and verify the tool list has no host `execute` / shell backend
- [x] 2.2 Gate draft generation behind Jev completeness (ask follow-up when insufficient) and verify incomplete prompts do not return a question list
- [x] 2.3 On sufficient intent, call Bailian to produce validated JSON questions and verify count/stems are present before surfacing `draft_ready`

## 3. Chat HTTP API

- [x] 3.1 Add create-session and post-message endpoints (SSE or chunked stream) under `/api/chat/...` and verify a clarifying turn streams assistant text with status `clarifying`
- [x] 3.2 Add confirm endpoint that writes `save_quiz` with `source=chat` plus summary metadata and verify it returns a quiz id usable by existing PDF routes
- [x] 3.3 Verify missing `bailian_api_key` on a draft-ready path returns an explicit error body (no fabricated questions)

## 4. Mobile chat UI

- [x] 4.1 Open Home「对话出题」to a new chat page and verify the “尚未开放” notice is gone
- [x] 4.2 Implement multi-turn message UI with progress for long generation and verify a full clarifying → draft → confirm path reaches Result with matching stems
- [x] 4.3 Show draft preview + confirm CTA when status is `draft_ready` and verify confirm navigates to the shared result/PDF flow

## 5. End-to-end slice

- [x] 5.1 Run one happy-path E2E (enough detail → draft → confirm → paper PDF) and verify PDF stems match the confirmed list and quiz meta marks chat source
- [x] 5.2 Run one incomplete-path check (“出点数学题”) and verify follow-up only—no quiz id / no question list until the parent supplies missing fields
