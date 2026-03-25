# Review Workflow

## Modes

- `auto`: publish immediately
- `review-first`: generate to `draft_review/`
- `manual-only`: timer runs blocked

## Suggested review flow

1. Set `mode` to `review-first`
2. Let timer or manual run generate drafts
3. Review markdown under `draft_review/`
4. Approve a draft:

```bash
bash scripts/publish_reviewed_post.sh <draft-file>
```

5. Or discard a draft:

```bash
bash scripts/discard_review_draft.sh <draft-file>
```

## Notes

- Publishing an approved draft moves it into `content/posts/` and rebuilds Hugo.
- Discarding a draft deletes the markdown file only.
- Review mode is recommended for major story arc milestones.
