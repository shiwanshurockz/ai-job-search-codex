# Using this workspace with Codex

This repository is an instruction-driven job search workspace, with Python helpers and Bun-based portal search tools. Codex follows AGENTS.md, which routes requests to the existing canonical workflows under .claude/. No Anthropic API replacement is required for those helpers.

## Start in the repository

In your UCRT64 terminal:

```bash
cd ~/Videos/Code/ai-job-search-codex
codex
```

Or open this folder as the project in the Codex desktop app. Use natural-language requests below; the original Claude slash commands are not assumed to be installed in Codex.

## Set up prerequisites

Verify a real Python 3.10+ installation, Bun, and the LaTeX executables lualatex and xelatex. See SETUP.md for the existing dependency instructions and TeX packages. Skip its Claude Code installation section when using Codex. Dependencies available in UCRT64 may differ from the desktop app's PATH.

Preview portal dependency installation, then install when ready:

```bash
python tools/install_portal_clis.py --dry-run
python tools/install_portal_clis.py
```

Do not use example profile values as facts. Before committing or pushing a populated profile, remember that profile files are tracked; use a private destination for personal information.

## First application

1. Put source resume files into documents/cv/ (see documents/README.md for other supported sources).
2. Ask: "Follow the setup workflow and build my profile from documents/. Ask me for missing facts and my target roles, locations, and work preferences."
3. Ask: "Evaluate this job against my profile: <URL or pasted description>."
4. After reviewing the fit assessment, ask: "Prepare the tailored CV and cover letter, perform the review, compile the PDFs, and verify the output."
5. Ask Codex to prepare the employer form with the browser submission workflow, review it, and approve the final submission. Record an outcome only after confirmed receipt.

The apply workflow generates and tracks drafts. To fill an employer form and submit after final review, continue with the browser submission workflow described below.

## Search and follow-up

Ask "Search for jobs matching my profile", "Rank the saved jobs", "Prepare me for this interview", or "Generate my application dashboard". Four bundled portals target Denmark; LinkedIn and FreeHire support broader searches. Set your actual geography and preferences during setup. Direct job URLs and pasted descriptions also work without portal search installation.

## Compatibility limits

The Codex adapter is in AGENTS.md. Claude permissions, hooks, slash command registration, and tool names are not imported into Codex. Available Codex tools and permissions still determine which steps can execute. Independent reviewer agents, web access, PDF rendering, and optional Gmail/Notion integrations require their respective capabilities. Missing capabilities must be reported rather than treated as successful checks.

## Windows launcher (configured for this checkout)

From PowerShell in the repository, run:

```powershell
.\Start-JobSearch.cmd
```

Check dependencies without opening an interactive session:

```powershell
.\Start-JobSearch.cmd -Check
```

The launcher finds an installed Codex executable, including the desktop app's bundled executable when Codex is absent from PATH. It adds this repository's local Bun and the desktop app's bundled Python/Git/PDF tools to the child session PATH when present. It does not change the global PATH or the system execution policy. These desktop runtime paths are machine-specific and may change after app updates; the dependency check reports missing tools.

LaTeX must be installed separately for the stock CV and cover letter PDF compilation. The launcher does not treat missing LaTeX as a successful PDF setup.

## Dependency setup

Install Python 3.10+, Bun, Node.js 18+, and Chrome if they are not already available.
The Windows launcher can also reuse supported desktop-bundled runtimes.
LinkedIn and FreeHire need Bun but have no runtime package dependencies.

Install the browser integration and register it for this checkout:

```powershell
bun install --cwd tools/browser --ignore-scripts
powershell -NoProfile -ExecutionPolicy Bypass -File tools/configure-application-browser.ps1
```

For generated PDFs, install MiKTeX with `winget install --id MiKTeX.MiKTeX -e`
or its official installer. Follow SETUP.md's Windows Basic MiKTeX section for
required template packages. Restart the terminal and run `Start-JobSearch.cmd -Check`.
Never treat missing LaTeX as successful PDF verification.

### Desktop-bundled CLI startup

The launcher automatically supplies `--no-daemon` when using the desktop app's bundled executable. That executable lacks the complete standalone package needed to launch its shared background server. This flag runs the interactive CLI in-process and also supports resume/fork. Explicit remote connections and the `agents` command are left unchanged because they require server mode. A separately installed CLI retains its default behavior.

## Fill forms and submit after your review

Restart Codex using `Start-JobSearch.cmd`, trust this repository, and run `/mcp`.
The `job_application_browser` server should be listed. It uses the installed Chrome
browser and a separate local login profile. You handle login/MFA/CAPTCHA in its window.

Ask: "Prepare the application for <job URL>, fill the form, and pause for my review
before submitting." Select the resume PDF to use (your original resume can be used
without LaTeX if you explicitly choose it). Codex asks for missing screening answers,
uploads only selected documents, presents the final form, and waits for your approval.
Uploads/autosave may send entered information before the final submission.

Browser implementation: Microsoft Playwright MCP 0.0.83, installed under tools/browser.
Configuration: .codex/config.toml (generated locally and ignored by Git; rerun the
configuration script after moving the repository, following its existing-file guidance). Browser sessions and output are kept in ignored .local-tools/.
Review packets are in ignored documents/applications/<archive>/submission_review.json.

The review helper validates file hashes and records approval; final-click discipline
is enforced by the agent workflow, not a browser security boundary. Portal support is
best-effort and may need manual steps. A click alone never marks an application applied.
