# Job search and applications with Codex

This fork adds a Codex entry point and a browser-assisted application workflow to
the original job-search framework. Claude Code is not required for the Codex path.
The `.claude/` directory remains the shared source of workflow instructions;
`AGENTS.md` tells Codex how to use those files.

## What was already here, and what we added

| Capability | Original framework | Added in this fork |
|---|---|---|
| Profile setup | Imports a resume and collects preferences | Codex follows the same setup instructions |
| Search and ranking | Portal CLIs, deduplication, fit evaluation | Codex routing and Windows runtime discovery |
| `/apply` | Evaluates a posting, drafts/reviews CV and cover letter, verifies PDFs, records a draft | Handoff to the new browser submission workflow |
| Form answers | Drafts text for the candidate to paste | Browser fills observed fields and uploads selected PDFs |
| Final submission | Candidate submits outside the drafting workflow | Codex pauses for final review, then submits only with explicit approval |
| Application tracking | `/outcome` records application progress | Browser receipt establishes when a draft can be marked `applied` |

**The new feature is `.claude/commands/submit.md`, not the original `/apply` command.**
Its default mode is **fill -> upload -> review -> approve -> submit -> verify receipt**.
In Codex, use natural-language prompts below. `/apply` and `/submit` are workflow
names; Claude-style slash commands are not automatically registered in Codex.
`/mcp` is a Codex command for checking the connected browser tools.

## Start an already configured checkout

1. Open PowerShell or Command Prompt in this repository.
2. Run the launcher:

   ```powershell
   .\Start-JobSearch.cmd
   ```

3. If prompted, review the folder-trust request and trust your own checkout.
4. In Codex, run `/mcp` and check that `job_application_browser` is available.
5. Use the search prompt below. You do not need to import the resume again if your
   local profile is already populated.

The launcher finds Codex on PATH or falls back to the installed desktop app binary.
For the desktop-bundled binary it adds `--no-daemon`, avoiding the "no complete local
package" startup error. It also adds available local Bun and desktop-bundled
Python/Git/PDF tools to that session's PATH. It does not change the global PATH.

Check tool availability without starting a chat:

```powershell
.\Start-JobSearch.cmd -Check
```

## Step 1: Find and rank jobs

Paste this into Codex:

```text
Read AGENTS.md and my saved candidate profile and search preferences. Follow the
repository's search and ranking workflows. Find jobs in my target roles, cities,
and work arrangement, preferably posted within the last 14 days.

Use the installed search tools and employer career pages. Remove duplicates and
check that shortlisted listings are still open. Rank the top 10 against my actual
experience. Show company, role, location, verified work arrangement, posting date,
fit score, matching skills, gaps, experience requirements, and a direct job link.
Flag unknown information instead of guessing. Distinguish overall software
experience from years of experience with a particular AI technology.

Only search and rank. Do not fill forms, upload documents, or submit applications.
Let me select the jobs to apply for.
```

Search results are candidates for review, not verified offers or automatically
approved applications. Review the shortlist and select a specific role/link.

## Step 2: Select the job and documents

Choose one of the following prompts.

**Use an existing resume PDF (does not require LaTeX):**

```text
Prepare my application for <JOB URL>. Evaluate the fit first. Use my existing
resume PDF at <REPO-RELATIVE PDF PATH>; do not change its claims. Follow the browser
submission workflow in .claude/commands/submit.md. Ask me for missing screening
answers, fill the form, and upload only the documents I selected. Pause at the
final review before submitting.
```

**Create tailored materials first (requires a working PDF toolchain):**

```text
Evaluate <JOB URL> against my profile, then follow the apply workflow to prepare
and review a tailored CV and cover letter. Compile and verify the PDFs before
using them. After the documents are ready, follow the browser submission workflow
to fill the application. Pause for my final review before submitting.
```

Replace `<JOB URL>` and `<REPO-RELATIVE PDF PATH>` with the real values. If several
resume files exist, select the exact one. The workflow must not upload an arbitrary
file or treat uncompiled TeX as a resume PDF.

## Step 3: Complete login and missing answers

The browser opens a separate Chrome profile for applications. Handle login, MFA,
CAPTCHA, account creation, or identity checks yourself in that window when needed.
The profile persists locally under `.local-tools/application-browser/`.

Codex fills only facts supported by your profile or answers. It asks when a form
needs information not yet confirmed: salary, work authorization, sponsorship,
joining date, technology-specific experience, or custom screening answers.
Optional sensitive fields and consent choices are not guessed.

Entering fields and uploading documents may transmit information through portal
autosave before the final Submit action. Review the employer/destination first.

## Step 4: Review, approve, and confirm receipt

Codex presents the company/role, application URL, attachments, completed answers,
remaining questions, and the final review page. It then waits for your response.

To revise, say what to change. To approve, explicitly identify the application:

```text
I reviewed the application for <ROLE> at <COMPANY>. Submit it as shown.
```

Approval applies to that reviewed application. Changed answers, attachments, or
URLs require another review. Codex clicks Submit once and checks for a receipt or
confirmed portal status. A click or timeout alone is not proof of submission.
If the result is ambiguous, it checks status before attempting anything again.
Only confirmed receipt allows the tracker to move from `drafted` to `applied`.

## First-time setup for a fresh clone

A fresh clone contains template profiles, not another person's private profile.

1. Install/sign in to Codex CLI, or install the Codex desktop app for the launcher
   fallback. Install Python 3.10+, Bun, Node.js 18+, and Chrome as needed. The Windows
   launcher can reuse supported desktop-bundled runtimes when present.
2. From the repository root, install browser dependencies and generate local MCP
   configuration:

   ```powershell
   bun install --cwd tools/browser --ignore-scripts
   powershell -NoProfile -ExecutionPolicy Bypass -File tools/configure-application-browser.ps1
   ```

   The script preserves an existing `.codex/config.toml`. If moving the checkout,
   follow its printed guidance to update the browser command path and working
   directory; it does not silently overwrite your configuration.
3. LinkedIn and FreeHire run with Bun without runtime package installation. For
   other portal/development dependencies, preview then run:

   ```powershell
   python tools/install_portal_clis.py --dry-run
   python tools/install_portal_clis.py
   ```

4. Put your resume in `documents/cv/`, start Codex, and ask:

   ```text
   Follow the setup workflow and build my profile from documents/cv/. Ask for
   missing facts, target roles, locations, work preferences, and working languages.
   Keep my personal data local; do not commit or push it.
   ```

5. For new tailored PDFs, install a LaTeX distribution with `lualatex` and `xelatex`.
   On Windows, use MiKTeX's installer or `winget install --id MiKTeX.MiKTeX -e`.
   Follow [SETUP.md](SETUP.md)'s Windows Basic MiKTeX section for template packages.
   Restart the terminal and check `Start-JobSearch.cmd -Check`. Existing selected
   resume PDFs do not need a LaTeX installation.

## Files added or adapted

| File | Purpose |
|---|---|
| `AGENTS.md` | Maps natural-language Codex requests to shared workflows |
| `Start-JobSearch.cmd` / `Start-JobSearch.ps1` | Windows launcher, runtime discovery, desktop `--no-daemon` fallback |
| `.claude/commands/submit.md` | Form preparation, final-review pause, submission, and receipt workflow |
| `.claude/commands/apply.md` | Handoff from verified documents to browser preparation |
| `tools/browser/package.json` and `bun.lock` | Pinned Microsoft Playwright MCP dependency |
| `tools/configure-application-browser.ps1` | Generates checkout-specific MCP configuration |
| `tools/start-application-browser.ps1` | Starts the browser tools with a separate local Chrome profile |
| `tools/application_review.py` | Builds/checks review packets and records approval tied to document and answer hashes |
| `tests/test_application_review.py` | Tests missing answers, stale approvals, changed files/destinations, and path validation |
| `tools/test_application_browser.py` | Local-only Chrome form-fill/upload smoke test, without submitting |
| `.gitignore` | Excludes browser sessions, local MCP paths, and downloaded runtime files |
| `CLAUDE.md` | Agent-neutral wording and factual AI-tool claims; populated profile stays local |

## Records and privacy

Per-application answers, review packets, attempts, and receipt evidence are saved in
`documents/applications/<archive>/`. Browser sessions/output stay in `.local-tools/`.
These locations are ignored by Git, as is `.codex/config.toml`.

**Profile and template files are still tracked by Git.** Populating them makes local
personal changes; an ignore rule does not hide changes to already tracked files.
Keep those changes out of code commits and public pushes. The reusable code commit
does not include your resume, populated profile, or private search preferences.

## Validation and practical limits

The implementation was checked with 40 passing Python tests (one additional test
skipped), plus a real Chrome test against a local form that filled fields, uploaded
a test PDF, read back values, and verified zero submissions. These checks do not
establish compatibility with every employer portal. No real application was sent
as part of development or testing.

The review helper checks recorded state and hashes; it does not intercept browser
clicks. The explicit final-review rule is part of the agent workflow. Portal changes,
unsupported widgets, login requirements, assessments, and anti-bot checks can require
manual work. Missing capabilities must be reported, not treated as successful steps.

To rerun the focused checks from a configured terminal:

```powershell
python -m unittest discover -s tests -p test_application_review.py
python tools/test_application_browser.py
```

If the browser is missing from `/mcp`, run the configuration script, trust the checkout,
and restart Codex. If dependencies are missing, reinstall `tools/browser` as above.
Never mark a PDF verified merely because the source file exists, and never mark an
application applied merely because its form was filled.
