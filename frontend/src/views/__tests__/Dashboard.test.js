import { mount, RouterLinkStub } from '@vue/test-utils'

import Dashboard from '../Dashboard.vue'

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

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('Dashboard view', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.post.mockReset()
  })

  it('renders failure reasons and publish decision hints', async () => {
    api.get.mockResolvedValue({
      recent_posts: [{ id: 1, title: '全真夜记：雨点与屏息', slug: '1-quanzhen-night-note', summary: '窗外起风。', status: 'published' }],
      recent_tasks: [
        {
          id: 7,
          status: 'published',
          started_at: '2026-04-12T04:00:00+00:00',
          error_code: '',
          error_message: '',
          qa_risk_level: 'high',
          queue_wait_ms: 40,
          publish_decision_path: 'human_approved_legacy_inferred',
        },
        {
          id: 8,
          status: 'failed',
          started_at: '2026-04-12T04:10:00+00:00',
          error_code: 'invalid_model_output',
          error_message: 'placeholder_question_marks_detected',
          qa_risk_level: 'high',
          queue_wait_ms: 18,
          publish_decision_path: 'blocked',
        },
      ],
      cost: { cost: 0.12, limit: 2 },
      click_stats: { today_page_views: 27 },
      domain_status: {
        domain: 'iuaa.de',
        enabled: true,
        status: 'enabled',
        reason: '域名解析与访问设置正常。',
        checked_at: '2026-04-12T04:20:00+00:00',
        base_url: 'https://iuaa.de/',
      },
      persona_stability: 82,
      memory_coherence: 77,
      risk_overview: { failed: 1, circuit_open: 0, waiting_human_signoff: 1 },
      attention_items: [
        {
          severity: 'warning',
          task_id: 7,
          label: 'legacy_publish_decision',
          message: '已发布高风险稿件的人工签发路径来自历史记录推断，建议复核。',
        },
        {
          severity: 'error',
          task_id: 8,
          label: 'invalid_model_output',
          message: 'placeholder_question_marks_detected',
        },
      ],
      config_status: {
        system_initialized: true,
        llm_ready: false,
        embedding_ready: true,
        domain_enabled: true,
      },
    })

    const wrapper = mount(Dashboard, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('模型输出格式异常')
    expect(wrapper.text()).toContain('placeholder_question_marks_detected')
    expect(wrapper.text()).toContain('人工签发（历史推断）')
    expect(wrapper.text()).toContain('大脑接入')
    expect(wrapper.text()).toContain('今日精力消耗')
    expect(wrapper.text()).toContain('域名配置诊断')
    expect(wrapper.text()).toContain('当日点击')
    expect(wrapper.text()).toContain('27')
    expect(wrapper.text()).not.toContain('立即发文')
    expect(wrapper.text()).not.toContain('解除休眠')
  })

  it('renders empty states when there are no posts or tasks', async () => {
    api.get.mockResolvedValue({
      recent_posts: [],
      recent_tasks: [],
      cost: { cost: 0, limit: 1 },
      click_stats: { today_page_views: 0 },
      domain_status: {
        domain: '',
        enabled: false,
        status: 'disabled',
        reason: '未配置域名，系统当前运行于 IP 模式。',
        checked_at: '',
        base_url: '/',
      },
      persona_stability: 0,
      memory_coherence: 0,
      risk_overview: { failed: 0, circuit_open: 0, waiting_human_signoff: 0 },
      attention_items: [],
      config_status: {
        system_initialized: true,
        llm_ready: true,
        embedding_ready: true,
        domain_enabled: true,
      },
    })

    const wrapper = mount(Dashboard, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('还没有文章')
    expect(wrapper.text()).toContain('还没有任务记录')
    expect(wrapper.text()).toContain('可以开始今晚写作')
    expect(wrapper.text()).toContain('博客未公开')
  })
})
