---
name: deprecated-module-check
description: "Use when you need to scan a workspace or project for deprecated, obsolete, or legacy modules, imports, or APIs and recommend supported alternatives."
---

# Deprecated Module Check

## Purpose

Use this skill to inspect the current workspace for code that depends on deprecated modules, packages, or APIs, then report what should be replaced and what to use instead.

## Workflow

1. Identify the project manifests and dependency sources.
   - Look for package manifests, lockfiles, requirements files, build files, and obvious import entry points.
   - Scan the codebase for imported modules, framework APIs, and direct package references.

2. Flag deprecated usage.
   - Treat a dependency as deprecated if it is marked deprecated by its ecosystem, removed from current guidance, or replaced by a newer supported package or API.
   - Distinguish between truly deprecated items and merely old but still supported items.

3. Confirm the impact.
   - Note where each deprecated module is used.
   - Prefer reporting the highest-impact or most user-visible usages first.

4. Suggest replacements.
   - Recommend the closest supported alternative.
   - If there is no direct replacement, explain the migration path or the minimum safe action.

5. Present the findings.
   - Group results by severity: critical, medium, low.
   - For each item, include the deprecated module, why it matters, where it appears, and the suggested alternative.

## Output Format

When used, return a concise audit with:

- Deprecated module or API name
- Location in the workspace
- Reason it is deprecated or risky
- Suggested replacement or migration path
- Any caveats if the alternative is not drop-in compatible

## Quality Bar

- Do not guess if a dependency is deprecated; verify it from the repository context or package metadata when possible.
- Do not flag normal old code as deprecated unless there is evidence it has been superseded.
- Keep recommendations practical and aligned with the project’s existing stack.
