# Capability Detection, Consent, And Delivery

Use this interaction pattern at the start and before any higher-effort branch.

## 1. Startup capability brief

Tell the user:
- what file type was detected
- whether the file appears text-readable or likely needs OCR
- which relevant skills or tools appear available for reading and exporting
- your recommended next step

Suggested format:

```markdown
我先確認到這份材料是 `{filetype}`。
目前可用能力：
- 讀取：{available reading tools or skills}
- 外部驗證：{available or unavailable}
- 匯出：{md/docx/pptx availability}

建議做法：
- 先 {recommended path}
- 若你同意，我再 {optional higher-effort step}
```

## 2. Consent checkpoints

Ask before:
- OCR on scanned files
- external browsing or live cross-verification
- generating `docx` or `pptx`

Suggested wording:

```markdown
我目前建議先用 `{method}` 繼續，因為 {reason}。
如果你同意，我就往下做；如果不要，我會改用 `{fallback}`，但結果會有 {limitation}。
```

## 3. Progress prompts

During execution, keep the user updated on:
- whether the source is readable enough
- whether exhibits are usable
- whether current evidence is sufficient for a draft
- whether a requested export skill is available

## 4. Export routing

### Markdown

If the user wants `md`, produce structured markdown directly.

### DOCX

Use a document skill or tool only if the session actually has one.
For repo-local structured export, prefer `scripts/generate_case_docx.py`.
If no suitable capability is available, stop and provide:

`site:github.com anthropic skill docx codex`

### PPTX

Use a presentation skill or tool only if the session actually has one.
For repo-local structured export, prefer `scripts/generate_case_pptx.py`.
If no suitable capability is available, stop and provide:

`site:github.com anthropic skill pptx codex`

## 5. No-tool fallback rule

Never pretend export support exists.
If the requested format is unsupported, respond with:
- the missing capability
- the safest alternative you can do now
- a Google search query for the Anthropic skill repo
