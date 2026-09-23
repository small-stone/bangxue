# Tasks

## 1. Flexible count (Mode B)

- [x] 1.1 Remove chat count snapping to `{10,15,20,30}` and accept `1..100` in `generate_chat_questions` / harness; verify requesting 12 yields exactly 12 stems
- [x] 1.2 When parsed count is `>100`, return `clarifying` with an upper-bound message and no question list; verify with a 101 request
- [x] 1.3 Update Jev/local completeness follow-up copy and count extraction so prompts mention 1–100 (not the four tiers); verify incomplete prompts no longer say only 10/15/20/30

## 2. Typewriter SSE + UI

- [x] 2.1 Chunk `assistant_text` into sequential SSE `token` events after `handle_parent_message` returns (then send `done`); verify multiple `token` frames appear before `done` in a clarifying turn
- [x] 2.2 Update `Chat.tsx` to create/append an assistant bubble from `token` events and only attach the draft panel on `done` when `draft_ready`; verify text appears incrementally instead of one shot after progress
- [x] 2.3 Keep a progress notice during the long compute phase and clear it when the first `token` arrives; verify「正在理解你的需求…」does not remain after typing starts

## 3. Regression checks

- [x] 3.1 Confirm Mode A quiz count chips / API still only allow 10/15/20/30 (unchanged)
- [x] 3.2 Happy path: enough intent with count 12 → typewriter reply → preview length 12 → confirm → PDF still works
