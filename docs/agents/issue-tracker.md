# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub issues.
Use the `gh` CLI for all operations.

## Repository

GitHub repository: `sarimjang/emba-case-study`.

Infer the repo from `git remote -v` when running inside this clone.

## Conventions

- Create an issue with `gh issue create --title "..." --body "..."`.
- Use a heredoc for multi-line issue bodies.
- Read an issue with `gh issue view <number> --comments`.
- When machine-readable output is needed, include labels and comments in the JSON output.
- List issues with `gh issue list --state open --json number,title,body,labels,comments` and apply appropriate `--label` and `--state` filters.
- Comment on an issue with `gh issue comment <number> --body "..."`.
- Apply labels with `gh issue edit <number> --add-label "..."`.
- Remove labels with `gh issue edit <number> --remove-label "..."`.
- Close an issue with `gh issue close <number> --comment "..."`.

## Pull requests as a triage surface

PRs as a request surface: no.

Do not pull external PRs into the issue triage queue by default.
Treat PRs as code review or implementation surfaces unless the maintainer explicitly asks otherwise.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.
