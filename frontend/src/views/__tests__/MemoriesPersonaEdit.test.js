import { mount } from '@vue/test-utils'

import FolderMonitors from '../FolderMonitors.vue'
import Memories from '../Memories.vue'
import PersonaEdit from '../PersonaEdit.vue'
import Sensory from '../Sensory.vue'

const { api, replace, push } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  replace: vi.fn(),
  push: vi.fn(),
}))

vi.mock('../../api', () => ({
  api,
  unwrap: vi.fn((value) => value),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '7' } }),
  useRouter: () => ({ replace, push }),
  onBeforeRouteLeave: vi.fn(),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('Memories and PersonaEdit views', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
    api.put.mockReset()
    api.delete.mockReset()
    replace.mockReset()
    push.mockReset()
    window.confirm = vi.fn(() => true)
  })

  it('renders memories pagination and page navigation', async () => {
    api.get
      .mockResolvedValueOnce({
        items: [{ id: 1, level: 'L0', content: '雨夜记忆', summary: '雨夜记忆' }],
        total: 25,
        page: 1,
        page_size: 20,
      })
      .mockResolvedValueOnce([{ id: 1, name: '全真' }])
      .mockResolvedValueOnce({
        items: [{ id: 2, level: 'L1', content: '第二页记忆', summary: '第二页记忆' }],
        total: 25,
        page: 2,
        page_size: 20,
      })
      .mockResolvedValueOnce([{ id: 1, name: '全真' }])

    const wrapper = mount(Memories)
    await flushPromises()

    expect(wrapper.text()).toContain('第 1 / 2 页，共 25 条')
    await wrapper
      .findAll('button')
      .find((button) => button.text().includes('下一页'))
      .trigger('click')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/memories', { params: { page: 2, page_size: 20 } })
    expect(wrapper.text()).toContain('第二页记忆')
  })

  it('updates memory governance actions from the current page', async () => {
    api.get
      .mockResolvedValueOnce({
        items: [
          {
            id: 7,
            persona_id: 1,
            level: 'L1',
            content: '守夜素材',
            summary: '守夜素材',
            tags: ['night'],
            source: 'hand_written',
            weight: 1,
            review_status: 'unreviewed',
            is_core: false,
          },
        ],
        total: 1,
      })
      .mockResolvedValueOnce([{ id: 1, name: '全真' }])
      .mockResolvedValueOnce({
        items: [
          {
            id: 7,
            persona_id: 1,
            level: 'L1',
            content: '守夜素材',
            summary: '守夜素材',
            tags: ['night'],
            source: 'hand_written',
            weight: 1,
            review_status: 'reviewed',
            is_core: false,
          },
        ],
        total: 1,
      })
      .mockResolvedValueOnce([{ id: 1, name: '全真' }])
    api.put.mockResolvedValue({
      id: 7,
      persona_id: 1,
      level: 'L1',
      content: '守夜素材',
      summary: '守夜素材',
      tags: ['night'],
      weight: 1,
      review_status: 'reviewed',
      is_core: false,
    })

    const wrapper = mount(Memories)
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text().includes('复核')).trigger('click')
    await flushPromises()

    expect(api.put).toHaveBeenCalledWith('/memories/7', { review_status: 'reviewed' })
    expect(wrapper.text()).toContain('素材已标记为已复核')
  })

  it('renders sensory status with chart data', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/sensory/current') {
        return Promise.resolve({
          id: 1,
          source: 'container',
          sampled_at: '2026-05-04T03:00:00+00:00',
          cpu_percent: 12,
          memory_percent: 34,
          disk_usage_percent: 56,
          tags: ['normal'],
          translated_text: '夜色安稳。',
          is_in_blind_zone: false,
        })
      }
      if (url === '/sensory/chart-data') {
        return Promise.resolve([{ sampled_at: '2026-05-04T03:00:00+00:00', cpu_percent: 12, memory_percent: 34 }])
      }
      if (url === '/sensory/history') return Promise.resolve([])
      return Promise.resolve([])
    })

    const wrapper = mount(Sensory)
    await flushPromises()

    expect(wrapper.text()).toContain('感知状态')
    expect(wrapper.text()).toContain('夜色安稳')
    expect(wrapper.text()).toContain('12.0%')
  })

  it('adds a default inbox folder monitor', async () => {
    api.get.mockResolvedValue([])
    api.post.mockResolvedValue({ id: 1 })

    const wrapper = mount(FolderMonitors)
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text().includes('开始监听')).trigger('click')
    await flushPromises()

    expect(api.post).toHaveBeenCalledWith('/folder-monitors', { path: '/app/inbox', file_types: ['md', 'txt'] })
  })

  it('shows persona load errors instead of failing silently', async () => {
    api.get.mockRejectedValueOnce(new Error('boom'))

    const wrapper = mount(PersonaEdit)
    await flushPromises()

    expect(wrapper.text()).toContain('人格设定加载失败')
  })
})
