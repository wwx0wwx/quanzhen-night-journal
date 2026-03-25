# Architecture

## Core loop

1. Load world state
2. Load pools, arcs, recent memories, and overrides
3. Read VPS signals
4. Translate signals into narrative events
5. Choose topic, scene, imagery, and emotions
6. Build prompt
7. Generate body
8. Refine body
9. Generate title and description
10. Run quality checks / repair pass
11. Publish or store draft
12. Update state, memories, stats

## Narrative layers

- Core memories (`memory_anchors`)
- Recent memories (`recent_memories`)
- Future fragments (`future_fragments`)
- Story arcs (`world_state.story_arcs`)

## Maintenance layers

- Manual overrides
- Analysis script
- Systemd timer
- Logs
