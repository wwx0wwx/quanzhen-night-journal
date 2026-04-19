import { mount } from '@vue/test-utils'

import Memories from '../Memories.vue'
import PersonaEdit from '../PersonaEdit.vue'

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
    await wrapper.findAll('button').find((button) => button.text().includes('下一页')).trigger('click')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/memories', { params: { page: 2, page_size: 20 } })
    expect(wrapper.text()).toContain('第二页记忆')
  })

  it('shows persona load errors instead of failing silently', async () => {
    api.get.mockRejectedValueOnce(new Error('boom'))

    const wrapper = mount(PersonaEdit)
    await flushPromises()

    expect(wrapper.text()).toContain('人格设定加载失败')
  })
})
