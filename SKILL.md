---
name: emba-case-study
description: Use whenever the user shares or mentions a business case, teaching case, company memo, board deck, strategy document, or executive decision paper — even if they just say "help me understand this PDF", "prepare me for class tomorrow", or "what should the CEO do here". Covers EMBA homework and case writeups, classroom discussion prep, CEO decision framing, trade-off analysis, exhibit checking, and Traditional Chinese decision briefs. Accepts PDF, PPTX, DOCX, Markdown, or TXT. Invoke even when the file type or task phrasing is vague — if the material looks like a business decision situation, this skill applies.
---

# EMBA Case Study

Analyze case documents as decision situations, not as passive summaries.

Default output language: Traditional Chinese unless the user asks otherwise.

## Core Goal

Turn raw case materials into a decision-ready analysis that:

- identifies the protagonist, decision point, and urgency
- separates facts, inference, and unresolved gaps
- diagnoses the core dilemma beneath the surface symptoms
- checks exhibits and numeric claims before trusting them
- ends with executable options, rationale, and trade-offs

## Workflow

### 0. Detect capabilities and ask before committing

Before doing substantial work, detect what this session can actually use:

- source-reading tools for `pdf`, `pptx`, `docx`, `md`, `txt`
- browsing or external research capability
- output-generation skills for `docx`, `pptx`, or `md`

Start with a short capability brief to the user:

- what you found
- the safest recommended path
- optional higher-effort paths such as OCR, external cross-verification, or file export

Then ask for the user's consent before continuing whenever the next step changes effort, scope, or output shape in a meaningful way:

- OCR on a scanned file
- external browsing or market/regulatory cross-checking
- generating deliverables such as `docx` or `pptx`

Use the checkpoint pattern in `references/delivery-and-consent.md`.

### 1. Ingest the source by format

Pick the lightest extraction path that preserves evidence:

- `pdf`: extract text, tables, exhibit labels, page references, and appendix structure
- `pptx`: extract slide titles, bullets, charts, speaker notes if present, and slide numbers
- `docx`: extract headings, tables, footnotes, and appendix sections
- `md` / `txt`: read directly and preserve heading or line anchors when possible

When format-specific help is available, prefer the matching document skill or tool first:

- `pdf` for PDF extraction or exhibit reading
- `pptx` for slide decks
- `docx` for Word documents

Fallback order when those tools are unavailable:

1. use any host-provided document connector or parser that can expose quoted text or slide/page anchors
2. if only partial extraction is possible, continue with the readable sections and mark the blind spots explicitly
3. if the file cannot be read with enough fidelity for evidence-based analysis, stop and report the minimum missing capability instead of pretending to understand the case

While ingesting, keep the user informed with short progress notes:

- whether the file has a text layer or requires OCR
- whether exhibits appear machine-readable or only image-readable
- whether the current evidence is already enough for a draft analysis

Do not start analysis until the source is readable enough to quote or cite specific evidence.

### 2. Build the decision pivot first

Start with the protagonist and the exact moment of choice:

- Who is the decision owner
- What decision must be made now
- What changed to force urgency
- What happens if the decision is delayed

Use the timeline and urgency checklist in `references/decision-pivot-checklist.md`.

### 3. Map company, industry, and structural context

Reconstruct the setting with only the context needed to understand the dilemma:

- company history, business model, core capabilities
- industry size, growth, concentration, and competitor posture
- regulation, channel power, supplier dependence, or technology constraints

Decompose the situation across business dimensions:

- market and channel
- cost and supply chain
- technology and organization

Use `references/analysis-template.md` for the section structure.

### 4. Diagnose the deep problem

Do not jump to recommendations after the first visible symptom.

Apply two layers:

- surface problem: revenue decline, margin compression, project delay, talent conflict, failed expansion
- root dilemma: incentive mismatch, capability gap, sequencing error, governance weakness, business-model contradiction

Run a compact 5 Whys pass when the case gives enough evidence.
Then define the central trade-off clearly:

- short-term profit vs long-term transformation
- control vs speed
- internal development vs acquisition or partnership
- localization vs standardization

If the evidence is incomplete, state the competing hypotheses instead of inventing certainty.

### 5. Validate exhibits and claims

Treat tables, charts, and quotes as claims to be tested.

Check internally:

- do totals, ratios, and year-on-year changes reconcile
- do margins, unit costs, capacity limits, or working-capital implications make sense
- does the narrative match the numbers

Check externally when the user asks for cross-verification or when live context materially affects the answer:

- official regulations
- company annual reports or investor materials
- peer public filings
- primary industry research or regulator publications

Use `references/evidence-and-verification.md` for the validation checklist.

Before doing that external step, tell the user what you plan to verify and ask if they want that broader pass.

### 6. Synthesize action options

End with decision-ready options, not generic advice.

For each option, answer:

- `How`: what management would actually do
- `Why`: what evidence and logic support it
- `Trade-off`: what cost, risk, or sacrifice comes with it

Prefer 2-4 mutually distinct options. Include a recommended path only if the user asks, or if the task clearly calls for a point of view.

### 7. Produce the canonical case spec first

Before any file export, normalize the analysis into one canonical `case_spec.json`.

This spec is the single source of truth for:

- `md`
- `docx`
- `pptx`

Use `scripts/examples/case_spec.sample.json` as the contract.
Do not maintain separate content specs for different output formats.

**Save path**: write the file alongside the output (e.g. `outputs/<case-slug>/case_spec.json`).
If the user has not specified an output directory, default to a sibling folder named after the case.

**Chart data**: if the case contains numeric indicators suitable for a bar chart (growth rates,
margins, market share, utilization), populate `evidence.chart_data` with real values extracted
from the source material. Only include `chart_data` when actual numbers are available — leave the
field absent rather than inventing placeholder values. All generators treat `chart_data` as optional
and fall back to a text-only layout when it is missing.

### 8. Offer output format and route to the right skill

Before final delivery, ask the user which output they want:

- inline chat answer only
- `md`
- `docx`
- `pptx`

Routing rules:

- `md`: prefer `scripts/generate_case_md.py` from the canonical case spec when a file is requested
- `docx`: use a document-oriented skill or tool if available
- `pptx`: use a presentation-oriented skill or tool if available

For repo-local exports from already-structured case findings:

- prefer `scripts/generate_case_pptx.py` for `pptx` when the session has `python-pptx`
- prefer `scripts/generate_case_docx.py` for `docx` when the session has `python-docx`
- prefer `scripts/generate_case_md.py` for `md` file export

Use the schema examples before composing new export specs:

- `scripts/examples/case_spec.sample.json`

If the user asks for `docx` or `pptx` and this session does not have a suitable skill or tool:

- stop before fabricating the file
- say which capability is missing
- provide a Google query the user can use to search the Anthropic skill repo

Default search queries:

- `site:github.com anthropic skill docx codex`
- `site:github.com anthropic skill pptx codex`
- `site:github.com anthropic skills presentation document generation`

## Output Contract

Unless the user requests a different format, produce this structure:

1. `一、導言與決策切入點`
2. `二、公司與產業總體檢`
3. `三、核心衝突與根本問題診斷`
4. `四、數據驗證與實例支持`
5. `五、課堂思辨與行動決策`
6. `附錄與參考資料`

Within those sections, cover the user's requested sub-questions from `references/analysis-template.md`.

## Evidence Rules

- Distinguish `個案明示`, `推論`, and `待驗證` when certainty differs.
- Cite the source anchor whenever practical: page, slide, heading, table, or appendix.
- If a number cannot be reconciled, flag it explicitly.
- If the case is missing a key exhibit, say what is missing and how it limits the conclusion.
- Do not fabricate interview quotes, market size, or regulatory text.

## External Research Rules

Use external sources only when they improve correctness:

- the case references laws, rules, standards, or industry facts that may be outdated
- the user explicitly asks for external cross-checking
- a recommendation depends on current market or regulatory conditions

When researching, prefer primary or official sources first. Keep the case itself as the base narrative unless external evidence disproves it or adds necessary context.

## Interaction Rules

- Recommend a method before acting when there are multiple viable paths.
- Ask for consent before OCR, external browsing, or export generation.
- Give short, concrete progress updates during extraction and validation.
- If the user declines a higher-effort step, continue with the best lower-effort path and state the limitation.
- If a requested export format is unsupported in the current session, stop cleanly and give the Anthropic skill repo search keywords instead of improvising.

## Good Practice

- Rebuild the timeline before diagnosing blame
- Translate descriptive chaos into one crisp decision question
- Convert exhibits into implications, not just copied numbers
- Keep classroom discussion space open when the user wants analysis without a final answer

## Failure Modes

Avoid these mistakes:

- writing a company summary without a decision pivot
- giving recommendations before naming the real trade-off
- trusting case exhibits without checking the arithmetic
- importing outside facts that overwrite the case chronology without saying so
- treating every issue as strategy when the root cause is organizational or operational

## Reference Files

- `references/analysis-template.md`: default section structure and prompting scaffolds
- `references/delivery-and-consent.md`: capability detection, consent checkpoints, and export routing
- `references/decision-pivot-checklist.md`: timeline, urgency, and protagonist framing
- `references/evidence-and-verification.md`: internal exhibit checks and external validation rules
