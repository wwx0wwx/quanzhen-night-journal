import { mount, RouterLinkStub } from '@vue/test-utils'

import Ghost from '../Ghost.vue'
import Posts from '../Posts.vue'

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
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
    api.delete.mockReset()
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
    expect(wrapper.text()).toContain('立即写一篇')
    expect(wrapper.text()).toContain('暂停自动写作')
    expect(wrapper.text()).toContain('恢复自动写作')
    expect(wrapper.find('button[data-tooltip="让系统自动写一篇文章"]').exists()).toBe(true)
    expect(wrapper.findComponent(RouterLinkStub).attributes('data-tooltip')).toBe('手动新建一篇文章草稿')
  })

  it('triggers publish, hibernate and wake actions from posts page header', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/posts') return Promise.resolve({ items: [], total: 0 })
      if (url === '/personas') return Promise.resolve([])
      return Promise.resolve([])
    })
    api.post
      .mockResolvedValueOnce({ id: 19 })
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
    await buttons.find((button) => button.text().includes('立即写一篇')).trigger('click')
    await flushPromises()
    await buttons.find((button) => button.text().includes('暂停自动写作')).trigger('click')
    await flushPromises()
    await buttons.find((button) => button.text().includes('恢复自动写作')).trigger('click')
    await flushPromises()

    expect(api.post).toHaveBeenNthCalledWith(1, '/tasks/trigger', {
      trigger_source: 'manual',
      semantic_hint: '请开始今晚的写作',
    })
    expect(api.post).toHaveBeenNthCalledWith(2, '/cost/hibernate')
    expect(api.post).toHaveBeenNthCalledWith(3, '/cost/wake-up')
  })

  it('renders ghost empty export state', async () => {
    api.get.mockResolvedValue([])

    const wrapper = mount(Ghost)

    await flushPromises()

    expect(wrapper.text()).toContain('还没有导出记录')
    expect(wrapper.text()).toContain('还没有数据库快照')
    expect(wrapper.text()).toContain('还没有预览结果')
  })

  it('rejects oversized ghost files before upload', async () => {
    api.get.mockResolvedValue([])

    const wrapper = mount(Ghost)
    await flushPromises()

    const input = wrapper.find('input[type="file"]')
    const largeFile = new File(['x'.repeat(1024)], 'too-large.ghost', { type: 'application/octet-stream' })
    Object.defineProperty(largeFile, 'size', { value: 25 * 1024 * 1024 })
    Object.defineProperty(input.element, 'files', { value: [largeFile] })

    await input.trigger('change')

    expect(wrapper.text()).toContain('文件过大')
  })

  it('deletes a ghost export from the list', async () => {
    api.get
      .mockResolvedValueOnce([{ filename: 'night.ghost', path: '/tmp/night.ghost', size: 128 }])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
    api.delete.mockResolvedValue({ deleted: true, filename: 'night.ghost' })

    const wrapper = mount(Ghost)
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find((button) => button.text().includes('删除'))
    await deleteButton.trigger('click')
    await flushPromises()

    expect(window.confirm).toHaveBeenCalled()
    expect(api.delete).toHaveBeenCalledWith('/ghost/night.ghost')
    expect(wrapper.text()).toContain('已删除导出包：night.ghost')
  })

  it('prunes old ghost exports from the retention control', async () => {
    api.get
      .mockResolvedValueOnce([
        { filename: 'a.ghost', path: '/tmp/a.ghost', size: 128 },
        { filename: 'b.ghost', path: '/tmp/b.ghost', size: 128 },
        { filename: 'c.ghost', path: '/tmp/c.ghost', size: 128 },
        { filename: 'd.ghost', path: '/tmp/d.ghost', size: 128 },
        { filename: 'e.ghost', path: '/tmp/e.ghost', size: 128 },
        { filename: 'f.ghost', path: '/tmp/f.ghost', size: 128 },
        { filename: 'g.ghost', path: '/tmp/g.ghost', size: 128 },
        { filename: 'h.ghost', path: '/tmp/h.ghost', size: 128 },
        { filename: 'i.ghost', path: '/tmp/i.ghost', size: 128 },
        { filename: 'j.ghost', path: '/tmp/j.ghost', size: 128 },
        { filename: 'k.ghost', path: '/tmp/k.ghost', size: 128 },
      ])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
    api.post.mockResolvedValue({ deleted: 1 })

    const wrapper = mount(Ghost)
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text().includes('清理旧导出')).trigger('click')
    await flushPromises()

    expect(api.post).toHaveBeenCalledWith('/ghost/prune', null, { params: { keep: 10 } })
    expect(wrapper.text()).toContain('已清理 1 个旧导出包')
  })
})
