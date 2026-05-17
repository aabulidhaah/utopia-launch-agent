# Security notes

A short threat model and operational checklist for the LAUNCH agent. Written before pushing the repo. Not exhaustive — a v1 take-home, not a deployable product.

## Threat model

The agent's job is to take a meeting transcript and emit drafts. The risks worth thinking about, in rough order of likelihood × impact:

| # | Risk | Mitigation in v1 |
|---|------|------------------|
| 1 | API key committed to git by accident | `.env` and `.env.local` in `.gitignore`. Key is read from env var only; never written to disk, never printed. `.env.example` ships a placeholder, not a real key. Pre-push sweep documented in this file. |
| 2 | Real meeting content (PII, customer names, strategy) committed via `output/` | `output/` in `.gitignore`. Reviewer sees only the fictional fixture run. |
| 3 | Real people quoted in fictional fixtures | Real Utopia partner names replaced with fabricated aliases in `fixtures/`. A `FICTIONAL FIXTURE` banner sits at the top of each fixture. |
| 4 | Prompt injection from a malicious or sloppy transcript | Transcript content is passed verbatim to the model in the user message. A malicious attendee could embed "ignore previous instructions and …" in the recorded speech. The agent does not auto-publish — `trace.operator_review_required: true` is a hard interlock; outputs go through a human before they reach LinkedIn, an inbox, or a journalist. |
| 5 | Hallucinated quotes attributed to real attendees | System prompt requires all quotes verbatim from transcript. A `trace.quotes_used_verbatim` field records every quote the model says it lifted, so the operator can spot-check provenance before publishing. |
| 6 | Anthropic API errors crashing in front of an operator | Wrapped in `try/except` in `main()`. Surface the error class + message cleanly, exit `1`, no stack trace. |
| 7 | API key in shell history | Out of scope for the agent. Recommendation: prefix the `export` command with a space if `HISTCONTROL=ignorespace` is set, or pipe the key through `read -s` from a password manager. |

## Out of scope (would matter at production)

These would need work before this agent ran unattended in Utopia OS proper. They are explicitly **not** built into v1, and the design assumes a human operator in the loop.

- **Rate limiting / cost caps.** Nothing prevents 100 transcripts being run in a tight loop and burning through Anthropic spend.
- **PII scrubbing on output.** A real Granola transcript could contain customer names, deal values, or private commentary that should not leave the studio's perimeter. The agent does not redact.
- **Audit log.** No record of who ran the agent, on which transcript, with what prompt version. Production would emit a trail to Linear or a structured log store.
- **Prompt-injection hardening.** Beyond the operator-review interlock, no detection of obvious injection strings ("ignore previous instructions", role-reversal attempts, base64-encoded instructions).
- **Output sanitization.** The model could produce Markdown/HTML that, when pasted into a Slack-message webhook downstream, contains a payload. Not a concern here because output is reviewed by a human.

## Pre-push checklist (run before `git push`)

```bash
# 1. Make sure nothing key-shaped is staged
git diff --staged | grep -E "sk-(ant|live|test)-[A-Za-z0-9_-]{10,}" && echo "STOP — key in diff" || echo "OK"

# 2. Make sure output/ isn't being committed
git diff --staged --name-only | grep -E "^output/" && echo "STOP — output staged" || echo "OK"

# 3. Make sure .env isn't being committed
git diff --staged --name-only | grep -E "^\.env$|^\.env\." && echo "STOP — env file staged" || echo "OK"
```

If any of those print STOP, do not push — unstage with `git rm --cached <file>` and re-check.

## If you find a vulnerability

Email a.abulidhaah@gmail.com. v1 is a take-home; for serious issues we'd switch to a real disclosure channel.
