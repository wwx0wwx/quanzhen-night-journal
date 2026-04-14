import { mount, RouterLinkStub } from '@vue/test-utils'

import Ghost from '../Ghost.vue'
import Posts from '../Posts.vue'

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  api,
  unwrap: vi.fn((value) => value),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('Posts and Ghost views', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
    window.confirm = vi.fn(() => true)
  })

  it('renders publish decision and task failure details', async () => {
    api.get
      .mockResolvedValueOnce({
        items: [
          {
            id: 12,
            title: '全真夜记：雨点与屏息',
            slug: '12-quanzhen-night-note',
            summary: '窗外的风沿着机房慢慢滑过。',
            status: 'published',
            persona_id: 1,
            task_id: 9,
            task_status: 'published',
            task_error_code: '',
            task_error_message: '',
            review_reason: 'waiting_human_signoff',
            updated_at: '2026-04-12T04:00:00+00:00',
            published_at: '2026-04-12T04:03:00+00:00',
            queue_wait_ms: 30,
            qa_risk_level: 'high',
            publish_decision_path: 'human_approved_legacy_inferred',
            human_approved: true,
            human_approval_recorded: false,
          },
        ],
        total: 1,
      })
      .mockResolvedValueOnce([
        {
          id: 1,
          name: '默认风格',
        },
      ])

    const wrapper = mount(Posts, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('12-quanzhen-night-note')
    expect(wrapper.text()).toContain('人工签发（历史推断）')
    expect(wrapper.text()).toContain('发布判定')
    expect(wrapper.text()).toContain('历史记录推断')
    expect(wrapper.text()).toContain('默认风格')
    expect(wrapper.text()).toContain('开始写一篇')
    expect(wrapper.text()).toContain('进入休眠')
    expect(wrapper.text()).toContain('恢复写作')
  })

  it('triggers publish, hibernate and wake actions from posts page header', async () => {
    api.get
      .mockResolvedValueOnce({ items: [], total: 0 })
      .mockResolvedValueOnce([])
    api.post
      .mockResolvedValueOnce({ id: 19 })
      .mockResolvedValueOnce({ items: [], total: 0 })
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ hibernating: true })
      .mockResolvedValueOnce({ ok: true })

    const wrapper = mount(Posts, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    await flushPromises()

    const buttons = wrapper.findAll('button')
    await buttons.find((button) => button.text().includes('开始写一篇')).trigger('click')
    await flushPromises()
    await buttons.find((button) => button.text().includes('进入休眠')).trigger('click')
    await flushPromises()
    await buttons.find((button) => button.text().includes('恢复写作')).trigger('click')
    await flushPromises()

    expect(api.post).toHaveBeenNthCalledWith(1, '/tasks/trigger', { trigger_source: 'manual', semantic_hint: '请开始今晚的写作' })
    expect(api.post).toHaveBeenNthCalledWith(2, '/cost/hibernate')
    expect(api.post).toHaveBeenNthCalledWith(3, '/cost/wake-up')
  })

  it('renders ghost empty export state', async () => {
    api.get.mockResolvedValue([])

    const wrapper = mount(Ghost)

    await flushPromises()

    expect(wrapper.text()).toContain('还没有导出记录')
    expect(wrapper.text()).toContain('还没有预览结果')
  })
})
