"""
LAUNCH Agent — Utopia Studio · Marketing & Events / M7

Takes a Granola transcript and emits a single structured JSON envelope plus a
human-readable rendering, containing:
  - one LinkedIn post in the studio voice (LAUNCH stage: Lead or Amplify)
  - one personalised follow-up email to the key attendee (LAUNCH stage: Nurture)
  - one press-angle sentence for a journalist (LAUNCH stage: Lead)

The envelope is shaped so a second agent (Slack-poster, Linear-issue-creator,
PR-email-drafter) could pick it up without a human in the middle. That is the
Utopia OS pattern: every node emits something the next node can read.

Run live (requires ANTHROPIC_API_KEY env var):
    python launch_agent.py --input ../fixtures/transcript_001.txt

Run dry (no API call — uses a canned response to verify wiring):
    python launch_agent.py --input ../fixtures/transcript_001.txt --dry-run

Outputs are written to ../output/output.json and ../output/output.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Model + prompt
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-6"  # Pinned. If unavailable, swap to claude-sonnet-4-6.

SYSTEM_PROMPT = """You are an in-house content agent for The Utopia Studio in Doha.

THE STUDIO'S VOICE — non-negotiable:
- Declarative, specific, no hedging.
- The studio publishes opinions, not summaries.
- Short sentences. Em-dashes for breaks. No corporate verbs ("leverage", "unlock", "transform").
- Never reference the meeting itself in published copy — that is internal.
- Quote attendees only with words they actually said in the transcript. Verbatim.
- One idea per post. Cut the second-best line.

THE LAUNCH FRAMEWORK — every output maps to one stage:
- Lead: generates inbound interest (LinkedIn posts, press lines)
- Amplify: extends reach (cross-channel echo)
- Unify: aligns voice across surfaces
- Nurture: moves a specific prospect forward (personal follow-ups)
- Convert: closes a commitment
- Harvest: recycles what worked

YOUR TASK: read the transcript and produce three artefacts:

1. linkedin_post — the studio's voice on LinkedIn.
   - 80–140 words. One opinion. No hashtags. No "Excited to share".
   - Names a sharp observation drawn from the transcript.
   - Maps to Lead or Amplify.

2. follow_up_email — to the key external attendee (not Utopia staff).
   - Subject + body. 80–120 words in the body.
   - References one specific thing that person actually said.
   - Proposes one concrete next step.
   - Maps to Nurture.

3. press_angle — one sentence a journalist could quote or pitch back.
   - Declarative. Specific. No throat-clearing.
   - Maps to Lead.

HARD CONSTRAINTS:
- All quotes verbatim from the transcript. Anything else, paraphrase or omit.
- Identify the key external attendee yourself from the transcript. If none, set
  follow_up_email.to_role to "internal" and address the closest external party
  mentioned by name in the discussion (a customer, a partner, a press contact).
- Output JSON only. No prose before or after. Schema below.

RESPOND WITH THIS EXACT JSON SHAPE:
{
  "linkedin_post": {
    "stage": "Lead" | "Amplify",
    "text": "...",
    "char_count": <int>
  },
  "follow_up_email": {
    "stage": "Nurture",
    "to_name": "...",
    "to_role": "...",
    "subject": "...",
    "body": "..."
  },
  "press_angle": {
    "stage": "Lead",
    "text": "..."
  },
  "quotes_used_verbatim": [
    "...exact substring from transcript...",
    "..."
  ],
  "key_attendee_reasoning": "one sentence on why you picked them"
}
"""


# ---------------------------------------------------------------------------
# Transcript parsing
# ---------------------------------------------------------------------------


@dataclass
class TranscriptMeta:
    meeting_id: str = ""
    title: str = ""
    date: str = ""
    attendees: list[dict[str, str]] = field(default_factory=list)
    body: str = ""


ATTENDEE_LINE = re.compile(r"^\s*#?\s*-\s*(?P<name>[^()]+?)\s*\((?P<role>[^)]+)\)")


def parse_transcript(text: str) -> TranscriptMeta:
    """Pull a minimal header out of a Granola-style transcript.

    The header is whatever appears before the first '[HH:MM]' timestamp. We
    extract meeting metadata; everything from the first timestamp onward is
    the body the model needs to read.
    """
    meta = TranscriptMeta()
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if re.match(r"^\[\d{2}:\d{2}\]", line):
            body_start = i
            break
        stripped = line.lstrip("#").strip()
        if stripped.lower().startswith("meeting:"):
            meta.title = stripped.split(":", 1)[1].strip()
        elif stripped.lower().startswith("date:"):
            meta.date = stripped.split(":", 1)[1].strip()
        elif "meeting_id" in stripped.lower():
            m = re.search(r"meeting_id\s+(\S+)", stripped)
            if m:
                meta.meeting_id = m.group(1)
        else:
            m = ATTENDEE_LINE.match(line)
            if m:
                meta.attendees.append({"name": m.group("name").strip(), "role": m.group("role").strip()})
    meta.body = "\n".join(lines[body_start:])
    return meta


# ---------------------------------------------------------------------------
# Model call (live + dry-run)
# ---------------------------------------------------------------------------


def call_claude(system: str, user: str) -> str:
    """Call the real Anthropic API. Raises if anthropic SDK or key is missing."""
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "anthropic SDK not installed. Run: pip install anthropic\n"
            f"Underlying error: {e}"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Either:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "or run with --dry-run to verify wiring without a model call."
        )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Concatenate any text blocks.
    parts = [b.text for b in msg.content if getattr(b, "type", "") == "text"]
    return "".join(parts).strip()


def dry_run_response() -> str:
    """Canned response shaped like the real one. For wiring tests only.

    The text is hand-written against the sample transcript so you can see the
    pipeline produce a complete envelope without spending an API call.
    """
    return json.dumps(
        {
            "linkedin_post": {
                "stage": "Lead",
                "text": (
                    "Container dwell time at Hamad Port sits at 4.1 days. "
                    "The published target is 2.5. The reason it is stuck is "
                    "not the cranes — it is the paperwork. Three customs "
                    "systems, three vendors, no one owning the translation "
                    "layer between them. The infrastructure story has been "
                    "the wrong story for three years. We are co-building "
                    "the agent that reads the declaration, decides which "
                    "fields go where, and writes back. Insider truth from "
                    "nine years inside the operator. The wedge is workflow "
                    "ownership, not a dashboard."
                ),
                "char_count": 632,
            },
            "follow_up_email": {
                "stage": "Nurture",
                "to_name": "Priya Anand",
                "to_role": "Principal, Radical Asia",
                "subject": "On head start vs. moat — moat ledger v2 incoming",
                "body": (
                    "Priya — your line in the pipeline call has been sitting "
                    "with me: \"Number one is a head start, not a moat.\" "
                    "Karim is rewriting the moat ledger this week with that "
                    "split made explicit. The customs sandbox is the head "
                    "start; the labelled corpus from nine years inside "
                    "Milaha is the durable piece. We will share v2 before "
                    "Wednesday. Separately, the PSA Singapore intro you "
                    "offered — happy to take it whenever it is ready. "
                    "Useful for the regional thesis even if it does not "
                    "land as a G1 call."
                ),
            },
            "press_angle": {
                "stage": "Lead",
                "text": (
                    "The Gulf's container-dwell problem is not a crane "
                    "problem — it is a paperwork problem, and the agent "
                    "that fixes it is being co-built inside Qatar."
                ),
            },
            "quotes_used_verbatim": [
                "Number one is a head start, not a moat.",
                "Container dwell times at Hamad Port. Average dwell is sitting at 4.1 days.",
                "The wedge here is workflow ownership, not a dashboard.",
            ],
            "key_attendee_reasoning": (
                "Priya Anand (Radical Asia) gave the sharpest critique in "
                "the meeting — that the customs API access is a head start, "
                "not a moat — and she also offered an unsolicited intro. "
                "Following up directly nurtures both threads."
            ),
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Envelope + rendering
# ---------------------------------------------------------------------------


def build_envelope(meta: TranscriptMeta, agent_output: dict[str, Any], model: str, dry: bool) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "agent": "utopia.launch_agent",
        "source": {
            "transcript_id": meta.meeting_id or "unknown",
            "meeting_title": meta.title,
            "meeting_date": meta.date,
            "attendees": meta.attendees,
        },
        "launch": {
            "linkedin_post": agent_output.get("linkedin_post", {}),
            "follow_up_email": agent_output.get("follow_up_email", {}),
            "press_angle": agent_output.get("press_angle", {}),
        },
        "trace": {
            "model": model if not dry else f"{model} (DRY-RUN — canned response, not a real model call)",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "quotes_used_verbatim": agent_output.get("quotes_used_verbatim", []),
            "key_attendee_reasoning": agent_output.get("key_attendee_reasoning", ""),
            "operator_review_required": True,
        },
        "next_actions": [
            {
                "agent": "slack-poster",
                "channel": "#studio-marketing",
                "payload_path": "$.launch.linkedin_post",
                "description": "Post the LinkedIn draft to studio-marketing for sign-off.",
            },
            {
                "agent": "linear-issue-creator",
                "team": "Marketing",
                "payload_path": "$.launch.follow_up_email",
                "description": "Open a Linear issue with the personalised follow-up as the description, owner = Marketing Lead.",
            },
            {
                "agent": "pr-pitcher",
                "payload_path": "$.launch.press_angle",
                "description": "Hold for the next press cycle; pair with a named journalist before sending.",
            },
        ],
    }


def render_markdown(env: dict[str, Any]) -> str:
    src = env["source"]
    li = env["launch"]["linkedin_post"]
    em = env["launch"]["follow_up_email"]
    pr = env["launch"]["press_angle"]
    trace = env["trace"]

    out = []
    out.append("# LAUNCH Agent · output")
    out.append("")
    out.append(f"**Source:** {src['meeting_title']} · {src['meeting_date']}")
    out.append(f"**Transcript:** `{src['transcript_id']}`")
    out.append(f"**Model:** {trace['model']}")
    out.append(f"**Generated:** {trace['generated_at']}")
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"## 1 · LinkedIn post · {li.get('stage', '?')}")
    out.append("")
    out.append(li.get("text", ""))
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"## 2 · Follow-up email · {em.get('stage', '?')}")
    out.append("")
    out.append(f"**To:** {em.get('to_name', '')} ({em.get('to_role', '')})")
    out.append(f"**Subject:** {em.get('subject', '')}")
    out.append("")
    out.append(em.get("body", ""))
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"## 3 · Press angle · {pr.get('stage', '?')}")
    out.append("")
    out.append(pr.get("text", ""))
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Trace")
    out.append("")
    out.append(f"_Reasoning:_ {trace.get('key_attendee_reasoning', '')}")
    out.append("")
    out.append("_Quotes lifted verbatim from transcript:_")
    for q in trace.get("quotes_used_verbatim", []):
        out.append(f"- \"{q}\"")
    out.append("")
    out.append("_Next agents in the chain:_")
    for na in env.get("next_actions", []):
        out.append(f"- **{na['agent']}** — {na['description']}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def extract_json_blob(text: str) -> dict[str, Any]:
    """Pull the first {...} JSON object out of a text response. Tolerant of
    minor preamble/postamble the model may include despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1:
        raise ValueError(f"No JSON object found in model output. Raw output:\n{text}")
    blob = text[first : last + 1]
    return json.loads(blob)


def main() -> int:
    p = argparse.ArgumentParser(description="LAUNCH agent for Utopia Studio")
    p.add_argument("--input", required=True, help="Path to the Granola transcript .txt")
    p.add_argument("--out-dir", default="../output", help="Where to write output.json and output.md")
    p.add_argument("--dry-run", action="store_true", help="Skip the API call; use a canned response")
    args = p.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript = input_path.read_text(encoding="utf-8")
    meta = parse_transcript(transcript)

    print(f"[launch_agent] parsed transcript: {meta.title!r}")
    print(f"[launch_agent] attendees: {len(meta.attendees)}")
    print(f"[launch_agent] mode: {'DRY-RUN' if args.dry_run else 'LIVE (Anthropic API)'}")

    if args.dry_run:
        raw = dry_run_response()
    else:
        try:
            raw = call_claude(SYSTEM_PROMPT, transcript)
        except SystemExit:
            raise  # already a clean message; let it surface
        except Exception as e:
            # Anthropic API errors (401, 429, 5xx, network) surface here.
            # We refuse to write a half-baked envelope — the operator should
            # see exactly what went wrong and re-run.
            kind = type(e).__name__
            print(f"[launch_agent] {kind}: {e}", file=sys.stderr)
            print("[launch_agent] aborting — no envelope written. Re-run with --dry-run to test wiring.", file=sys.stderr)
            return 1

    try:
        agent_output = extract_json_blob(raw)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[launch_agent] failed to parse model JSON: {e}", file=sys.stderr)
        # Write the raw model output so the operator can see what happened.
        (out_dir / "raw_model_output.txt").write_text(raw, encoding="utf-8")
        return 1

    envelope = build_envelope(meta, agent_output, MODEL, dry=args.dry_run)

    json_path = out_dir / "output.json"
    md_path = out_dir / "output.md"
    json_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(envelope), encoding="utf-8")

    print(f"[launch_agent] wrote: {json_path}")
    print(f"[launch_agent] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
