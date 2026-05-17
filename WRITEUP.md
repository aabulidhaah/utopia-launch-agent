# LAUNCH Agent · Writeup

**Track:** Marketing & Events / M7 Go-to-Market
**Submitter:** Ahmed Abulidhaah · a.abulidhaah@gmail.com

---

### Operator & problem

The operator is the Marketing Lead at Utopia Studio. After every studio meeting — co-build pipeline calls, fellow product reviews, QDB weekly, partner check-ins — Granola produces a transcript. Today the Marketing Lead reads each one manually and writes content from scratch: a LinkedIn post, a follow-up to whoever was in the room from outside the studio, and a one-line press angle for the next pitch cycle. With six to ten fellows running simultaneously, that is hours a week of transcript-reading before any actual writing starts.

### The agent

`launch_agent.py` takes a Granola transcript as input and calls the Anthropic Messages API (Claude Opus 4.6) once. The model is given the studio's voice rules and the LAUNCH framework as a system prompt, and is constrained to return JSON in a fixed schema. The agent parses the response into an envelope containing three drafts — LinkedIn post (Lead), personalised follow-up email (Nurture), and press-angle sentence (Lead) — plus a trace block (model, verbatim quotes lifted from transcript, key-attendee reasoning) and a `next_actions` list shaped for downstream agents. Output lands as `output.json` (for the next agent) and `output.md` (for the operator's eye).

### Sample input (verbatim)

```
# Granola transcript · Co-Build Pipeline Call · 2026-05-14
# Meeting: Pipeline Review — Fellow Karim (Hadhar Logistics AI)
# Date: 2026-05-14, 14:00–14:42 Doha (UTC+3)
# Attendees:
#   - Layla Mahmoud (Utopia, Managing Partner) — host
#   - Daniel Sterling (Utopia, CPO)
#   - Karim Hassan (Fellow, Hadhar)
#   - Priya Anand (Radical Asia, Principal)
#   - Marcus Lee (A-Typical Ventures, Director)

[14:02] Karim Hassan: So Hadhar is solving the same problem I lived for nine years at Milaha. Container dwell times at Hamad Port. Average dwell is sitting at 4.1 days. The published target is 2.5. The reason it's stuck isn't the cranes, it's the paperwork…
[14:09] Priya Anand: Number two is the durable one. Number one is a head start, not a moat. Be honest with yourself about the difference.
[14:19] Karim Hassan: I want to be clear — I'm not chasing a SaaS sticker. The wedge here is workflow ownership, not a dashboard.
```

_Full fixture: `fixtures/transcript_001.txt`._

### Sample output (verbatim — replace with live run before submission)

> ⚠️ Below is the dry-run canned output for reference. Run the agent live with your `ANTHROPIC_API_KEY` set, then paste the real model output here before submitting.

```json
{
  "linkedin_post": {
      "stage": "Lead",
      "text": "Container dwell time at Gulf ports averages 4.1 days. The published target is 2.5. Every newspaper blames cranes and infrastructure. They're writing the wrong article.\n\nThe bottleneck is paperwork. Customs declarations bounce between three systems maintained by three vendors — and a human still copies fields between them. Nobody owns it end to end.\n\nThe fix isn't a dashboard. It's an agent that reads the declaration, decides which fields go where, and writes back. Workflow ownership, not chrome.\n\nThe Gulf's port problem is a translation-layer problem. The sooner the industry says that out loud, the sooner dwell times move.",
      "char_count": 529
    },
    "follow_up_email": {
      "stage": "Nurture",
      "to_name": "Karim Hassan",
      "to_role": "Fellow, Hadhar Logistics AI",
      "subject": "Moat ledger + the DP World slot",
      "body": "Karim,\n\nStrong session. One thing that stuck: your line — \"I'm not chasing a SaaS sticker. The wedge here is workflow ownership, not a dashboard.\" That conviction is the venture. Don't soften it in the deck.\n\nTwo items before Wednesday:\n\n1. Rewrite the moat ledger with the head-start vs. durable-advantage split Priya flagged. The customs API access is real — but frame it honestly as a timing edge, not a wall.\n\n2. Convert the DP World Sokhna verbal yes into a booked call by Friday — or swap in GWC through Faisal.\n\nSend me the revised ledger by Wednesday EOD and I'll pre-read before Daniel's gate review.\n\n— Layla"
    },
    "press_angle": {
      "stage": "Lead",
      "text": "Gulf container dwell times are stuck at 4.1 days — not because of cranes or infrastructure, but because customs declarations still bounce between three incompatible systems stitched together by manual copy-paste, and a Doha-based AI venture is building the agent layer to close that gap."
    }
}

```

### What I cut

- **Direct Slack/Linear posting.** The agent emits a `next_actions` envelope and stops. Auto-publishing studio voice without a human review is the kind of failure mode the brief is testing for — and the studio rubric flags "operator review required" as a hard interlock.
- **Multi-meeting summarisation.** Considered chaining several transcripts a week into one digest. Cut it. The brief is "every meeting produces publishable content within an hour" — batching breaks that loop.
- **Voice-fine-tuning on real studio posts.** Considered scraping the Studio LinkedIn page for 30 examples and few-shotting the model. Cut it for time and because the studio voice is encoded sharply enough in prose constraints alone for a v1.

### What broke or surprised me

- The model wants to summarise the meeting instead of publishing an opinion. The fix was a single line in the system prompt — _"the studio publishes opinions, not summaries"_ — but I had to add it explicitly. Pre-2026 instinct says "summarise the call". The studio voice does the opposite.
- "Key external attendee" is fuzzier than I expected. In some transcripts there is no clear external party (internal-only reviews). The agent now handles this by addressing the closest customer or partner named in discussion, with a `to_role: "internal"` fallback flag.
- Quote attribution drifts if you do not pin it. Without the "all quotes verbatim from transcript" constraint and a `quotes_used_verbatim` trace field, the model paraphrases attendees and the press angle starts inventing things. That is a publication risk, not a craft risk.
- Test mode hit a real 401 from Anthropic before I added exception handling — the SDK raised a stack trace instead of failing cleanly. Easy fix; flagging it because a tool an operator runs at 9am Monday should never crash with a Python traceback in front of them.

### If I had two more days

1. **Granola webhook → auto-trigger.** Connect to Granola's post-meeting webhook so the agent fires on transcript-ready rather than on operator action. Same envelope, zero clicks.
2. **Slack bot interface.** `/launch <granola_id>` posts the rendered output to `#studio-marketing` with approve/edit/discard buttons. The bonus-challenge "second-agent handoff" becomes a real button click.
3. **Voice eval harness.** A small set of 10 studio-published posts as a reference set, plus a Claude-based eval that scores new drafts on three axes — declarativeness, specificity, length — and refuses to ship anything that scores below a threshold without operator override.
