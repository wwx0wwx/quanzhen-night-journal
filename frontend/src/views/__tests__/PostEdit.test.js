import { mount } from '@vue/test-utils'

import PostEdit from '../PostEdit.vue'

const { api, replace } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
  replace: vi.fn(),
}))

vi.mock('../../api', () => ({
  api,
  unwrap: vi.fn((value) => value),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '12' } }),
  useRouter: () => ({ replace }),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('PostEdit view', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
    api.put.mockReset()
    replace.mockReset()
    window.confirm = vi.fn(() => true)
  })

  it('renders preview and revision history for an existing post', async () => {
    api.get
      .mockResolvedValueOnce({
        id: 12,
        title: '雨夜标题',
        slug: 'rain-night-note',
        summary: '一段摘要',
        content_markdown: '# 雨夜标题\n\n第一段内容。',
        status: 'pending_review',
        revision: 3,
        task_id: 7,
        updated_at: '2026-04-12T04:00:00+00:00',
        published_at: '',
        review_info: {},
      })
      .mockResolvedValueOnce([
        {
          id: 30,
          revision: 2,
          title: '旧版本',
          content_markdown: '旧内容',
          change_reason: 'manual_update',
          created_at: '2026-04-12T03:00:00+00:00',
        },
      ])

    const wrapper = mount(PostEdit)
    await flushPromises()

    expect(wrapper.text()).toContain('Markdown 预览')
    expect(wrapper.text()).toContain('修订历史')
    expect(wrapper.text()).toContain('版本 #2')
    expect(wrapper.text()).toContain('自动生成稿')
    expect(wrapper.html()).toContain('<h1>雨夜标题</h1>')
  })
})
