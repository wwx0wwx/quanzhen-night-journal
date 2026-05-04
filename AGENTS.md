# Codex Collaboration Rules

This file defines persistent repository-level instructions for Codex agents working on this project.

## Git Commit Policy

- Every time Codex changes the repository, it must create a Git commit before finishing the task, unless the user explicitly says not to commit.
- The goal is to keep every codebase change rollbackable.
- Do not push commits unless the user explicitly asks for a push.
- Do not rewrite history, reset branches, or discard user changes unless the user explicitly requests that operation.
- If tests cannot be run or fail, still commit the requested change when appropriate, and mention the verification result clearly in the final response.
