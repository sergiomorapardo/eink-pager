# Repository instructions

## Project rules

- Python 3.12 with uv. Only runtime dependency: Pillow; the server uses the stdlib `http.server`.
- Run `uv run pytest` before every commit. After changing `pager/render.py`, regenerate `docs/preview.png` and look at it.
- `python -m pager.digest` without `--dry-run` calls `claude -p` and spends the user's plan quota. Ask for explicit approval before running it and report the cost of the previous run.
- Never edit `~/.claude/settings.json` (e.g. `scripts/install.py --apply`) without explicit approval.
- Claude Code hooks must never block or fail a session: short timeouts, background work, exit 0.
- Track pending work in `TODO.md`: check off what is done and add what comes up.
- Keep file, module, and function names short and in English.

## Current setup

- The repository is public on GitHub. `.github/workflows/` runs `local-validation` (CI), `review-size` (at most 12 files), and the Claude review; the review needs the `CLAUDE_CODE_OAUTH_TOKEN` secret.
- A ruleset protects `main`: no deletion, no force push, changes only through pull requests with squash merge, and `local-validation` and `review-size` must pass on an up-to-date branch.
- The initial commit landed directly on `main` before these rules were adopted.

## Git workflow

- Perform every task that may modify tracked files in a dedicated, isolated Git worktree. Never edit the primary checkout directly.
- If an isolated worktree cannot be created or used, stop and explain the blocker instead of falling back to the primary checkout.
- Worktrees are sibling working directories attached to the same repository; never create a worktree inside another worktree.
- Create every new branch as `feature/<name>`, where `<name>` is a short, descriptive, lowercase kebab-case slug.
- For an independent change, start the branch from the repository's current default branch unless the user explicitly selects another base.
- Never commit directly to `main`, `master`, `develop`, or another protected branch.
- Before starting changes and immediately before each squash merge, run `git pull --ff-only origin main` from the clean primary checkout. If it cannot fast-forward, inspect the divergence and preserve local work; never reset or force the update.
- Update the isolated feature branch against the refreshed default branch and resolve conflicts before merging. For a stack, update its bottom layer against the default branch, then propagate changes through each immediate base in order. Do not bypass existing authorization requirements for history rewrites or force-pushes.
- After updating branches or resolving conflicts, rerun relevant checks and re-request review when the changes require it. Verify each PR still changes at most 12 files against its immediate base.
- Preserve unrelated user changes and do not rewrite remote history or force-push without explicit authorization.

## Claude Code review commands

Use the local commands for the self-review and the GitHub workflow for the required review of each PR.

| Stage | Command | Who starts it |
| --- | --- | --- |
| Before opening a PR that qualifies (see below) | `/code-review high` on the worktree diff | The agent |
| Ready to publish a feature branch | `/ship` (commit, push, open PR, in-session review, then watch CI, conflicts, and comments) | The user only |
| PR already open and only needs babysitting | `/steward` (CI failures, conflicts, review comments; no initial review) | The user only |
| Required review of each PR, once | `Claude Code Review` workflow | Marking the draft PR ready for review; the `claude-review` label for a second review |

- Run `/code-review high` only when a PR meets at least one of these criteria:
  - **Refactor:** restructures existing code without intending to change behavior.
  - **Large:** at least 8 changed files or about 300 changed lines, excluding `uv.lock` and generated images.
  - **Critical:** touches code that can break or cost something outside the repo: `hooks/` (runs inside every Claude Code session), `scripts/install.py` (edits `~/.claude/settings.json`), `pager/digest.py` (spends plan quota and reads email/calendar), `pager/server.py` network exposure, or `.github/` workflows.
  - **Private data:** adds or changes sample data, fixtures, screenshots, or other content that could expose personal information in this public repository (names, emails, client or project names, local paths). The review must check for it before anything is pushed.
  - **Firmware:** touches `firmware/` code, where a bug can stop the device from booting or drain its battery, and fixing it means reflashing the device.
- For other PRs (docs, tests, small features or fixes), rely on local checks, a manual read of the diff, and the GitHub Claude review. State in the PR body whether `/code-review` ran and why.
- Fix confirmed findings before pushing and mention skipped ones in the PR body. Use `/code-review high --fix` only for findings you have verified.
- When a qualifying PR gets a substantive revision, run `/code-review high` again only on that revision's diff.
- Open every PR as a draft (`gh pr create --draft`). Pushes to a draft run CI and the size check but never the Claude review.
- Mark the PR ready (`gh pr ready`) only when its checks pass, the self-review is done, and the description is final. That triggers the single GitHub Claude review for the PR.
- If a PR was opened as ready (for example by `/ship`), request its single review with the `claude-review` label after the in-session fixes are pushed.
- Request a second review only after a substantive revision, by removing and re-adding the `claude-review` label. Tell the user first, since it spends plan quota. Spelling or formatting-only fixes never get another review.
- Never use the `max` or `ultra` levels unless the user asks for them; they are the most expensive reviews.
- Never invoke `/ship` or `/steward` yourself. When a branch is ready, tell the user to type `/ship`; when an open PR only needs babysitting, suggest `/steward`.
- `/ship` and `/steward` never merge. Merging still follows the rules below, including the user's approval and the squash merge command.
- The in-session review from `/code-review` or `/ship` is the self-review. It does not replace the GitHub Claude review: each PR still needs its own completed review on GitHub.
- When `/ship` already reviewed the diff in session, do not run `/code-review` again on the same diff.
- Managed Claude Code Review, PR Steward, and Claude Approvals (Claude Ship) require a Team or Enterprise plan and a GitHub organization. This repository uses the GitHub Actions workflows until that changes.

## Commits and pull requests

- Each pull request may change at most 12 files, counting additions, modifications, deletions, configuration, tests, documentation, and lockfiles against its immediate base branch.
- Split work into sequential, coherent groups. Complete and review each pull request before starting the next dependent group.
- Group each commit by responsibility. Prefer multiple meaningful commits in a pull request; never combine unrelated groups merely to create a single commit.
- Keep automatic deletion of remote source branches enabled after pull requests are merged. Do not recreate a merged branch merely to preserve its name; use the pull request to inspect its original commits.
- Merge from the clean primary checkout with `gh pr merge <PR-number> --squash --match-head-commit <head-sha>`, then run `git pull --ff-only origin main`. For a merge performed on GitHub, finalize locally with the same pull.
- After each squash merge, remove the merged pull request's worktree (`git worktree remove <path>`) and its local branch (`git branch -D feature/<name>`) once the squash commit is on the refreshed `main` and the branch tree matches it. Also remove older worktrees whose pull requests are already merged. Run the cleanup from the primary checkout, never from inside the worktree being removed.
- Never remove the primary checkout or a worktree that is dirty, locked, active in another session, divergent from its merged pull request, or tied to an open or closed-without-merge pull request.
- Preserve unmerged work and report any skipped branches instead of forcing removal.
- Review each finished pull request and run checks appropriate to its stage before proceeding. State any validation that requires a later integration layer.
- The review unit is each individual PR against its immediate base, never a group of pushes or an entire stack. Each PR needs its own completed Claude review; a review of another PR cannot satisfy that requirement.
- Optimize total Claude Opus executions per PR, including automatic push-triggered runs and manual mentions. Prepare and self-review that PR's complete diff (see Claude Code review commands), run relevant local checks, and batch all findings from a review round of that same PR before publishing its next substantive revision. Reducing mentions alone is not sufficient.
- Before every push, account for automatic review triggers and dependent branches. Complete the current PR's review cycle before advancing to the next dependent layer; do not trigger reviews across other PRs as if a group of pushes were a review unit.
- Before integrating independent PRs, inspect their bases, completed reviews, and automatic triggers. Choose an order that avoids invalidating completed reviews by merging documentation or another independent change first. Do not mechanically rebase or push an already reviewed PR without assessing whether the update is required and the cost of another review; still perform required base updates. Inform the user before causing an additional review and explain why it is needed.
- An explicit user exception to the reviewer requirement applies only to the identified PR. Record the exception, completed checks, and remaining limitations on that PR; it does not waive review for future PRs.
- Before requesting Claude review, inspect automatic and manual reviews on the same PR for the same head and immediate-base commits. Reuse an equivalent in-progress or completed review; do not trigger a duplicate. This applies separately to new PRs, each stacked layer, and subsequent revisions, and supersedes an unconditional mention after PR creation.
- If no equivalent review exists, request one with the `claude-review` label and post one concise comment with the scope, head/base SHAs, check results, and resolved or outstanding findings. Do not use `@claude` mentions to request reviews; they start a separate run outside these limits. Do not mention Claude in routine thread replies, commits, cosmetic updates, or status queries.
- Wait for the selected automatic or manual workflow to finish successfully and for Claude to publish its completed review; read all feedback, including inline comments. A successful workflow without a completed review, an acknowledgment, or no response does not satisfy this requirement. Saving quota never waives the final review.
- If the selected workflow fails or is cancelled, or no completed review is available within 15 minutes, report the blocker and investigate or retry as appropriate. Count from the review-request comment creation time for manual reviews, or from the workflow run creation time for automatic reviews (including queue time). Reusing a run does not reset this deadline. Elapsed time does not waive the review requirement; do not proceed until the review is complete.
- Evaluate each comment against the code, requirements, and product goals. Implement feedback that is valid, improves the product, and is in scope for this PR. Explain on the pull request why a suggestion is not applicable; record useful out-of-scope suggestions as follow-up work without exceeding the 12-file limit. Fix blocking issues before proceeding.
- Address all actionable feedback on the same PR and run the relevant checks for any changes. The PR author or agent must reply with the outcome and resolve review threads only after their concerns have been addressed. After batching that PR's substantive fixes to behavior, contracts, or workflow requirements, obtain a completed review of its updated revision, reusing an equivalent review on that PR before re-adding the `claude-review` label. Repeat its cycle for new actionable findings. Request again only when that PR has a substantive revision needing review or an investigated failure left no completed review; spelling or formatting-only fixes do not require another review.
- Continue to the next dependent group or merge only after this review cycle is complete and the existing check and approval requirements are satisfied.

- Use Conventional Commits for every commit: `<type>(<optional-scope>): <description>`.
- Prefer these types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, and `revert`.
- Keep the subject concise and imperative. Mark breaking changes with `!` and a `BREAKING CHANGE:` footer when applicable.
- Use a Conventional Commit title for every pull request so it can become the final squash commit message.
- Integrate pull requests exclusively with squash merge. Do not use merge commits or rebase merge.
- Every squash commit on the default branch must end with its pull request reference, ` (#<number>)`, so the branch that produced it stays traceable from `git log`.
- Never pass `--subject` or `--body` to `gh pr merge --squash`. GitHub appends ` (#<number>)` only when it builds the subject from the pull request title; an explicit subject silently drops it.
- If the pull request title is not the message you want on the default branch, correct it with `gh pr edit --title` before merging, then merge without overriding the subject.
- Merge only after required checks and approvals pass and all conflicts and actionable review comments are resolved.
- After merging, verify that the new commit on the default branch carries its ` (#<number>)` suffix. Repairing a missing one means rewriting published history, which needs explicit authorization.

## Stacked pull requests

- Use a stacked pull request only when a change genuinely depends on another unmerged change. Keep independent changes based on the default branch.
- Keep every stack in one repository as a single linear chain. The bottom branch targets the stack trunk, and each higher branch starts from and targets the branch immediately below it.
- Give every stack layer its own focused `feature/<name>` branch, isolated sibling worktree, Conventional Commit history, and reviewable pull request.
- Never describe this as a “worktree on a worktree.” Create the higher worktree from the lower branch ref while keeping both worktree directories separate.
- When stack branches are checked out in separate worktrees, use `gh stack link` or the GitHub website to create or link the stack. Do not run `gh stack checkout`, `gh stack rebase`, or `gh stack sync` across branches held by other worktrees.
- Apply corrections to the lowest layer that owns the change, then update dependent layers in order and verify the resulting ancestry and diffs.
- Merge stacked pull requests from bottom to top using squash merge. After each merge, verify that GitHub correctly rebases or retargets the remaining stack before continuing.


## Documentation

- Never publish private client or training-project names, repository links, internal commit identifiers, or client-specific material in public repositories, commit messages, PR descriptions, or review comments. Use project-local documentation and inspect the full diff and public metadata before publishing.
- Write READMEs, guides, contribution templates, and diagram labels in English.
- Prefer concise Mermaid flows, sequence diagrams, and comparison tables over long prose.
- Keep diagrams aligned with code and label planned capabilities explicitly.
- Keep on-device UI strings in Spanish (the pager is for a Spanish-speaking user); explain them in English in docs.
