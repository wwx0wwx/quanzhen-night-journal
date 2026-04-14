import { mount } from '@vue/test-utils'

import Observatory from '../Observatory.vue'

const replace = vi.fn()

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  api,
  unwrap: vi.fn((value) => value),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { panel: 'audit' } }),
  useRouter: () => ({ replace }),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('Observatory view', () => {
  beforeEach(() => {
    api.get.mockReset()
    replace.mockReset()
    api.get.mockImplementation((url) => {
      if (url === '/health/dashboard') return Promise.resolve({ persona_stability: 88, memory_coherence: 83, cost: { cost: 0.12, limit: 1 } })
      if (url === '/memories') return Promise.resolve({ items: [] })
      if (url === '/personas') return Promise.resolve([])
      if (url === '/tasks') return Promise.resolve({ items: [{ status: 'published' }] })
      if (url === '/sensory/current') return Promise.resolve({ translated_text: '夜色安静', tags: ['night'], cpu_percent: 20, memory_percent: 30 })
      if (url === '/sensory/history') return Promise.resolve([])
      if (url === '/events') return Promise.resolve({ items: [] })
      if (url === '/audit') {
        return Promise.resolve({
          items: [
            {
              id: 1,
              action: 'task.status_change',
              timestamp: '2026-04-12T12:00:00+00:00',
              actor: 'system',
              severity: 'warning',
              target_type: 'task',
              target_id: '7',
              ip_address: '127.0.0.1',
              detail: { to: 'waiting_human_signoff' },
            },
          ],
          total: 1,
        })
      }
      return Promise.resolve({})
    })
  })

  it('renders the merged audit panel inside observatory', async () => {
    const wrapper = mount(Observatory)
    await flushPromises()

    expect(wrapper.text()).toContain('观测中心')
    expect(wrapper.text()).toContain('系统日志')
    expect(wrapper.text()).toContain('task.status_change')
    expect(wrapper.text()).toContain('第 1 / 1 页，共 1 条')
  })
})
