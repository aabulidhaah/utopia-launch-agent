# LAUNCH Agent · Utopia Studio · M7 Go-to-Market

**One-line description:** A single-file Python agent that turns a Granola transcript into three publishable LAUNCH artefacts (LinkedIn post, personalised follow-up email, press-angle sentence), shaped as a JSON envelope another agent can consume.

---

## How to run

```bash
# 1. Install dependency
pip install -r requirements.txt

# 2. Set your key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run live against the sample transcript
cd src
python launch_agent.py --input ../fixtures/transcript_001.txt

# Or dry-run (no API call — verifies wiring with a canned response)
python launch_agent.py --input ../fixtures/transcript_001.txt --dry-run
```

Outputs land in `output/output.json` and `output/output.md`.

---

## What it calls

- **Anthropic Messages API** (`anthropic` SDK), model `claude-opus-4-6`. One call per transcript. Fallback string in source if Opus is unavailable: `claude-sonnet-4-6`.

The agent does not call Slack, Linear, or Drive in this version — by design. It emits the envelope those downstream agents would consume. See **What I cut** in the writeup.

---

## Prompt design

The system prompt encodes three things, in this order:

1. **Studio voice** — declarative, specific, no hedging; publishes opinions, not summaries; no corporate verbs; one idea per post.
2. **LAUNCH framework** — every output must map to a stage (Lead / Amplify / Unify / Nurture / Convert / Harvest). LinkedIn = Lead or Amplify. Follow-up email = Nurture. Press angle = Lead.
3. **Hard constraints** — all quotes verbatim from transcript; key external attendee identified by the model itself; JSON-only response in a fixed schema.

The full prompt is in `src/launch_agent.py` as `SYSTEM_PROMPT`. It is the most opinionated part of the build — the voice work is in there, not in the code.

---

## What the envelope looks like (the handoff)

```json
{
  "schema_version": "1.0",
  "agent": "utopia.launch_agent",
  "source": { "transcript_id": "...", "meeting_title": "...", "attendees": [...] },
  "launch": {
    "linkedin_post": { "stage": "Lead", "text": "...", "char_count": 632 },
    "follow_up_email": { "stage": "Nurture", "to_name": "...", "subject": "...", "body": "..." },
    "press_angle": { "stage": "Lead", "text": "..." }
  },
  "trace": {
    "model": "claude-opus-4-6",
    "generated_at": "2026-05-17T07:34:59+00:00",
    "quotes_used_verbatim": [ "..." ],
    "key_attendee_reasoning": "...",
    "operator_review_required": true
  },
  "next_actions": [
    { "agent": "slack-poster", "channel": "#studio-marketing", "payload_path": "$.launch.linkedin_post" },
    { "agent": "linear-issue-creator", "team": "Marketing", "payload_path": "$.launch.follow_up_email" },
    { "agent": "pr-pitcher", "payload_path": "$.launch.press_angle" }
  ]
}
```

Any second agent reading the envelope can find its payload via the `payload_path` field. `operator_review_required: true` is a hard interlock for now — nothing auto-publishes.

---

## File tree

```
utopia-agent-submission/
├── README.md                ← you are here
├── WRITEUP.md               ← one-page submission writeup
├── LOOM.md                  ← script for the 5-min Loom
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   └── launch_agent.py      ← the agent (single file)
├── fixtures/
│   └── transcript_001.txt   ← sample Granola transcript (fictional)
└── output/
    ├── output.json          ← generated envelope (after run)
    └── output.md            ← generated human-readable rendering
```
