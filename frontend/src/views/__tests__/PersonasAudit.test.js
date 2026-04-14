import { mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia } from 'pinia'

import Audit from '../Audit.vue'
import Personas from '../Personas.vue'

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  api,
  unwrap: vi.fn((value) => value),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('Personas and Audit views', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.delete.mockReset()
    window.confirm = vi.fn(() => true)
  })

  it('deletes a non-default persona from the list', async () => {
    api.get.mockResolvedValue([
      {
        id: 1,
        name: '全真',
        description: '默认人格',
        is_default: true,
        is_active: true,
        structure_preference: 'medium',
      },
      {
        id: 2,
        name: '待修复人格 2',
        description: '等待人工修订',
        is_default: false,
        is_active: false,
        structure_preference: 'medium',
      },
    ])
    api.delete.mockResolvedValue({ deleted: true })

    const wrapper = mount(Personas, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    await flushPromises()
    const deleteButtons = wrapper.findAll('button').filter((button) => button.text().includes('删除'))
    await deleteButtons[1].trigger('click')
    await flushPromises()

    expect(api.delete).toHaveBeenCalledWith('/personas/2')
    expect(wrapper.text()).not.toContain('待修复人格 2')
  })

  it('renders audit log entries and pagination summary', async () => {
    api.get.mockResolvedValue({
      items: [
        {
          id: 9,
          action: 'task.status_change',
          timestamp: '2026-04-12T12:00:00+00:00',
          actor: 'system',
          severity: 'warning',
          target_type: 'task',
          target_id: '7',
          ip_address: '127.0.0.1',
          detail: { to: 'waiting_human_signoff' },
          processed_event: '夜里下雨，机房风扇声更清楚了',
        },
      ],
      total: 1,
    })

    const wrapper = mount(Audit)
    await flushPromises()

    expect(wrapper.text()).toContain('事件映射')
    expect(wrapper.text()).toContain('task.status_change')
    expect(wrapper.text()).toContain('waiting_human_signoff')
    expect(wrapper.text()).toContain('夜里下雨，机房风扇声更清楚了')
    expect(wrapper.text()).toContain('第 1 / 1 页，共 1 条')
  })
})
