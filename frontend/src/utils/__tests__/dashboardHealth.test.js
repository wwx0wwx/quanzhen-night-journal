import { describe, expect, it } from 'vitest'

import {
  buildHealthCards,
  deriveNextStep,
  deriveSystemState,
  statusLabel,
} from '../dashboardHealth'

describe('dashboardHealth', () => {
  it('labels health statuses', () => {
    expect(statusLabel('ok')).toBe('正常')
    expect(statusLabel('error')).toBe('错误')
  })

  it('builds health cards from checks', () => {
    const cards = buildHealthCards({
      api: { status: 'ok' },
      database: { status: 'ok', encoding: 'UTF-8' },
    })
    expect(cards.length).toBeGreaterThan(3)
    expect(cards[0].statusLabel).toBe('正常')
  })

  it('derives system state and next step', () => {
    const state = deriveSystemState({
      systemInitialized: true,
      llmReady: true,
      waitingHuman: 1,
      unackedCircuitOpen: 0,
      unackedFailed: 0,
    })
    expect(state.label).toContain('关注')
    const step = deriveNextStep({
      systemInitialized: true,
      llmReady: true,
      embeddingReady: true,
      waitingHuman: 1,
      unackedCircuitOpen: 0,
      unackedFailed: 0,
    })
    expect(step.title).toContain('签发')
  })
})
