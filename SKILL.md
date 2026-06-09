---
name: emba-case-study
description: Use when analyzing a business case, teaching case, company memo, board deck, strategy review, or executive decision document in PDF, PPTX, DOCX, Markdown, or TXT format. Use for EMBA case writeups, classroom discussion prep, CEO decision framing, trade-off analysis, exhibit checking, and evidence-backed synthesis that must surface the decision pivot, company and industry context, root dilemma, data validation, and action options in Traditional Chinese.
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

### 6. Synthesize action options

End with decision-ready options, not generic advice.

For each option, answer:
- `How`: what management would actually do
- `Why`: what evidence and logic support it
- `Trade-off`: what cost, risk, or sacrifice comes with it

Prefer 2-4 mutually distinct options. Include a recommended path only if the user asks, or if the task clearly calls for a point of view.

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
- `references/decision-pivot-checklist.md`: timeline, urgency, and protagonist framing
- `references/evidence-and-verification.md`: internal exhibit checks and external validation rules
