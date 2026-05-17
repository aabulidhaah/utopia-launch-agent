# Loom script · 5 minutes max

The brief asks for two questions answered in the first 60 seconds. Hit them in the first 30. Keep total run under 5:00. Quiet room, screen recording mode, no over-editing — they explicitly score Feynman clarity over polish.

---

## 0:00–0:30 — The two questions, out loud

> "I'm Ahmed Abulidhaah. I built a LAUNCH agent for the M7 Go-to-Market track.
>
> The operator is the Marketing Lead at Utopia Studio. Today, after every studio meeting, they read the Granola transcript manually and write content from scratch — a LinkedIn post, a follow-up email to the external attendee, a press angle. With six to ten fellows running at once, that's hours a week of transcript-reading before any writing starts.
>
> In plain language: the agent reads the transcript, picks out the actual quotes and the sharpest observation, and produces three drafts in the studio's voice. The Marketing Lead reviews them and ships. Nothing auto-publishes."

## 0:30–1:30 — Show it running

- Terminal split with the transcript on the left, command on the right.
- Run: `python launch_agent.py --input ../fixtures/transcript_001.txt`
- Talk over it: _"One Claude API call. The system prompt encodes the studio voice — declarative, no hedging, opinions not summaries — and the LAUNCH framework. The model returns JSON, I validate and wrap it in an envelope a second agent can read."_
- Show the agent finish, point at the two output files written.

## 1:30–3:00 — Walk through the output

Open `output/output.md`. Read it in this order:

1. **LinkedIn post.** _"This is in the Studio voice. It publishes an opinion — 'the bottleneck is paperwork, not cranes' — not a summary. It uses a real quote-worthy line from the call: 'workflow ownership, not chrome.'"_
2. **Follow-up email to Karim, the Fellow.** _"Interesting call by the agent here. The system prompt said 'key external attendee, not Utopia staff.' The model treated the Fellow as the external party — which is actually defensible, since Fellows are co-builders, not employees. The email opens with Karim's own words from the transcript and proposes two concrete action items with deadlines. If the studio wanted email-to-Radical-Asia instead, that's one prompt tweak — the constraint is in plain English."_
3. **Press angle.** _"One sentence. Declarative. Specific to dwell-time numbers. A journalist can quote it back without rewriting."_

## 3:00–4:00 — Show the envelope and the handoff

Open `output/output.json`.

- Point at `launch.*` blocks. _"Three artefacts."_
- Point at `trace.quotes_used_verbatim`. _"Every quote in the output is here, verbatim from the transcript. If anything in the drafts isn't traceable to a quote, it's flagged."_
- Point at `trace.operator_review_required: true`. _"Hard interlock. Nothing auto-publishes. That's the cut I made."_
- Point at `next_actions`. _"This is the Utopia OS pattern. Each next agent has a `payload_path`. Slack-poster knows where to find its payload. So does linear-issue-creator. So does pr-pitcher. The agent is a node, not an endpoint."_

## 4:00–4:30 — What I cut and what surprised me

> "Two cuts worth naming. One, I did not wire Slack or Linear in this version — the envelope is the handoff. Auto-publishing the studio's voice is exactly the failure mode I think the brief is testing for.
>
> Two, I did not few-shot on real Studio posts. Cut for time, and because the voice constraints in the system prompt did most of the work.
>
> What surprised me: the model wants to summarise the meeting. The fix was one line — 'the studio publishes opinions, not summaries' — but I had to write it explicitly. That's the difference between a competent agent and a useful one. Also flagged in the writeup: my first live test crashed on an Anthropic 401 with a stack trace, before I wrapped the call in exception handling. A tool an operator runs Monday morning should never crash with a Python traceback in front of them."

## 4:30–5:00 — Close

> "If I had two more days, I'd wire the Granola webhook so the agent fires on transcript-ready, add a Slack approve/edit/discard interface, and build a small eval harness against ten real published Studio posts.
>
> Thanks for reading. Code is in the README, writeup is one page. Looking forward to walking through it live."

---

## Recording checklist

- [ ] Quiet room, headphones plugged in
- [ ] Terminal font size ≥ 16pt — they need to see the output
- [ ] `output/` cleared before recording so they see it being written
- [ ] `ANTHROPIC_API_KEY` already exported in the shell (don't show the key on camera)
- [ ] Run takes ~15s — don't cut the wait; it shows it's a real call
- [ ] Don't read every line of the LinkedIn post out loud. Read the opening line, point at the rest, move on.
- [ ] Stay under 5:00. They will count.
