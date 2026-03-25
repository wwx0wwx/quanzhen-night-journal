# Review Workflow

## Modes

- `auto`: publish immediately
- `review-first`: generate to `draft_review/`
- `manual-only`: timer runs blocked

## Suggested review flow

1. Set `mode` to `review-first`
2. Let timer or manual run generate drafts
3. Review markdown under `draft_review/`
4. Move approved drafts into `content/posts/`
5. Rebuild Hugo

## Important

At the moment, review-first stores the draft but does not include a dedicated approval helper script yet. Approval is still manual.
