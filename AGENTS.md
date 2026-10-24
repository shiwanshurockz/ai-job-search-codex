---
framework_version: 1.0.0
---

# Agent Guidelines: AI Job Search

This workspace is structured to manage job search activities, scraper tools, CVs, cover letters, and interview preparation.

## Thin-Pointer Design (Single Source of Truth)

To prevent duplication and configuration drift across different AI agent frameworks (Claude Code, Google Antigravity, Codex, Cursor, Gemini CLI, etc.), this workspace uses a unified thin-pointer design. All agent runtimes should load the canonical specifications and candidate profiles from the files and directories below:

1. **Personal Candidate Profile:**
   - The candidate profile, contact details, education, and target preferences are defined in [CLAUDE.md](CLAUDE.md) and the individual profile methodology files under [.claude/skills/job-application-assistant/](.claude/skills/job-application-assistant/) (specifically `01-*.md` etc.).
2. **Canonical Workflow Specifications:**
   - The step-by-step instructions and triggers for tasks (setup, scrape, rank, apply, upskill, interview) are defined in the [.claude/](.claude/) directory (specifically under `.claude/skills/` and `.claude/commands/`).
   - Do not duplicate these rules or specifications. Treat `.claude/` files as the single source of truth.
3. **Portal Search Skills:**
   - Job-portal search CLIs live under [.agents/skills/](.agents/skills/) in the portable Agent Skills format (with a `SKILL.md` per portal). Codex and Antigravity discover these automatically; the `/scrape` workflow in [.claude/skills/job-scraper/](.claude/skills/job-scraper/) orchestrates them.

## Codex workflow adapter

When running in Codex, load `CLAUDE.md` as candidate data and shared workflow guidance; its filename does not require the Claude runtime. Keep the canonical files in `.claude/` rather than copying their contents.

Route natural-language requests as follows (Claude slash commands are labels, not assumed Codex commands):

| Request | Canonical specification |
|---|---|
| Set up or update my profile | `.claude/commands/setup.md` |
| Search for jobs | `.claude/skills/job-scraper/SKILL.md` |
| Rank found jobs | `.claude/commands/rank.md` |
| Prepare an application for a URL or pasted posting | `.claude/commands/apply.md` |
| Fill or submit a selected application through a portal | `.claude/commands/submit.md` |
| Prepare for an interview | `.claude/commands/interview.md` |
| Record an outcome or prepare a follow-up | `.claude/commands/outcome.md` |
| Generate a dashboard | `.claude/commands/html-report.md` |
| Plan learning to address skill gaps | `.claude/skills/upskill/SKILL.md` |

For other workflows, read the matching file in `.claude/commands/` when present. Treat `$ARGUMENTS` as the user's actual request arguments; never execute that placeholder literally.

### Runtime translation

- Map Read/Glob/Grep to available file readers and `rg`, Edit/Write to available file editing tools, WebFetch/WebSearch to available web tools, and AskUserQuestion to the runtime's question mechanism. Do not assume Claude tool names exist.
- `.claude/settings.json` permissions and hooks do not configure Codex. Follow the active Codex sandbox and approval policy; never weaken permissions to imitate a Claude allowlist.
- For specified fetcher/reviewer agents, read the matching `.claude/agents/` specification and use available subagent tools when supported, preserving their read-only role. If unavailable, disclose that limitation and perform separate fetch/review passes; do not claim an independent review occurred.
- Create a writable temporary directory before using a workflow scratchpad. Adapt Bash examples to the active shell; in PowerShell use explicit paths rather than Bash `${SCRATCHPAD:?}` syntax.
- On Windows, verify a working Python interpreter instead of assuming `python3` works. Verify Bun, `lualatex`, and `xelatex` before dependent steps. Report missing dependencies rather than claiming successful searches or compiled PDFs.
- Inspect generated PDF pages using the available PDF renderer and image viewer; reading TeX alone does not satisfy visual verification.
- Preserve the posting integrity checks, factual grounding, fit evaluation, and draft status tracking in the canonical workflows. Preparing documents does not mean an application was submitted. Submit or send only when the user explicitly requests that action.
- Mention AI tools in application materials only when supported by the candidate's actual experience. Neither using Codex here nor the legacy Claude filenames establish a candidate skill.

## Application submission mode
The user selected fill-and-review mode. Follow .claude/commands/submit.md to fill forms and upload selected documents, then pause for explicit final review before every submission. Asking to apply is not permission to skip that review. Use the job_application_browser MCP server; no real submission is authorized merely by installing or testing this integration.
