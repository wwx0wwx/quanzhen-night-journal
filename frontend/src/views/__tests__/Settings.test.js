import { mount } from '@vue/test-utils'

import Settings from '../Settings.vue'

const { api, unwrap } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
  unwrap: vi.fn((value) => value),
}))

vi.mock('../../api', () => ({
  api,
  unwrap,
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

function makeConfig() {
  return {
    'site.title': { value: '全真夜记', category: 'site', encrypted: false },
    'site.subtitle': { value: '', category: 'site', encrypted: false },
    'site.domain': { value: 'iuaa.de', category: 'site', encrypted: false },
    'panel.title': { value: '', category: 'panel', encrypted: false },
    'panel.status_text': { value: '{user} 正在守夜', category: 'panel', encrypted: false },
    'llm.base_url': { value: 'https://688.qzz.io/v1', category: 'llm', encrypted: false },
    'llm.api_key': { value: '******', category: 'llm', encrypted: true },
    'llm.model_id': { value: 'Qwen--3.5-max', category: 'llm', encrypted: false },
    'embedding.base_url': { value: '', category: 'embedding', encrypted: false },
    'embedding.api_key': { value: '', category: 'embedding', encrypted: true },
    'embedding.model_id': { value: '', category: 'embedding', encrypted: false },
    'schedule.days_per_cycle': { value: '1', category: 'schedule', encrypted: false },
    'schedule.posts_per_cycle': { value: '1', category: 'schedule', encrypted: false },
    'schedule.publish_time': { value: '21:02', category: 'schedule', encrypted: false },
    'schedule.review_cron': { value: '0 3 * * 0', category: 'schedule', encrypted: false },
    'schedule.decay_cron': { value: '0 4 * * *', category: 'schedule', encrypted: false },
    'schedule.sample_interval_minutes': { value: '5', category: 'schedule', encrypted: false },
    'budget.daily_limit_usd': { value: '99999', category: 'budget', encrypted: false },
    'budget.monthly_limit_usd': { value: '99999', category: 'budget', encrypted: false },
    'qa.max_retries': { value: '3', category: 'qa', encrypted: false },
    'qa.min_length': { value: '200', category: 'qa', encrypted: false },
    'qa.max_length': { value: '5000', category: 'qa', encrypted: false },
    'qa.duplicate_threshold': { value: '0.85', category: 'qa', encrypted: false },
    'qa.forbidden_words': { value: '[]', category: 'qa', encrypted: false },
    'qa.template_phrases': { value: '[]', category: 'qa', encrypted: false },
    'webhook.auth_mode': { value: 'bearer', category: 'webhook', encrypted: false },
    'webhook.auth_token': { value: '', category: 'webhook', encrypted: true },
    'webhook.cooldown_seconds': { value: '1800', category: 'webhook', encrypted: false },
    'anti_perfection.enabled': { value: '1', category: 'anti_perfection', encrypted: false },
    'anti_perfection.consecutive_max': { value: '3', category: 'anti_perfection', encrypted: false },
    'anti_perfection.cooldown_hours': { value: '24', category: 'anti_perfection', encrypted: false },
    'sensory.blind_zone_minutes': { value: '30', category: 'sensory', encrypted: false },
    'sensory.cpu_high_threshold': { value: '80', category: 'sensory', encrypted: false },
    'sensory.mem_high_threshold': { value: '85', category: 'sensory', encrypted: false },
    'sensory.io_high_threshold': { value: '70', category: 'sensory', encrypted: false },
    'sensory.source_mode': { value: 'container', category: 'sensory', encrypted: false },
    'hugo.theme': { value: 'PaperMod', category: 'hugo', encrypted: false },
  }
}

describe('Settings view', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.put.mockReset()
    api.post.mockReset()
    unwrap.mockClear()
  })

  it('sends only changed budget fields with the correct category', async () => {
    api.get
      .mockResolvedValueOnce(makeConfig())
      .mockResolvedValueOnce({
        domain: 'iuaa.de',
        enabled: true,
        status: 'enabled',
        reason: 'ok',
        checked_at: '2026-04-12T00:00:00+00:00',
        base_url: 'https://iuaa.de/',
      })
      .mockResolvedValueOnce({
        domain: 'iuaa.de',
        enabled: true,
        status: 'enabled',
        reason: 'ok',
        checked_at: '2026-04-12T00:00:00+00:00',
        base_url: 'https://iuaa.de/',
      })
    api.put.mockResolvedValue({ site_runtime: { reason: '配置已保存。' } })

    const wrapper = mount(Settings)
    await flushPromises()

    expect(wrapper.text()).toContain('当前发文结论')
    expect(wrapper.text()).toContain('发文能力受限')
    expect(wrapper.text()).toContain('博客信息')
    expect(wrapper.text()).toContain('面板设置')
    expect(wrapper.text()).toContain('大脑接入（LLM）')
    expect(wrapper.text()).toContain('记忆检索（Embedding）')
    expect(wrapper.text()).toContain('测试大脑接入')
    expect(wrapper.text()).toContain('测试记忆检索')

    const fields = wrapper.findAll('.field')
    const dailyField = fields.find((item) => item.text().includes('每日预算上限（USD）'))
    const monthlyField = fields.find((item) => item.text().includes('每月预算上限（USD）'))
    await dailyField.find('input').setValue('100')
    await monthlyField.find('input').setValue('2000')
    await wrapper.find('button.btn.primary').trigger('click')
    await flushPromises()

    expect(api.put).toHaveBeenCalledTimes(1)
    expect(api.put.mock.calls[0][0]).toBe('/config')
    expect(api.put.mock.calls[0][1]).toEqual({
      items: [
        { key: 'budget.daily_limit_usd', value: '100', category: 'budget', encrypted: false },
        { key: 'budget.monthly_limit_usd', value: '2000', category: 'budget', encrypted: false },
      ],
    })
  })

  it('tests llm and embedding in place with existing endpoints', async () => {
    api.get
      .mockResolvedValueOnce(makeConfig())
      .mockResolvedValueOnce({
        domain: 'iuaa.de',
        enabled: true,
        status: 'enabled',
        reason: 'ok',
        checked_at: '2026-04-12T00:00:00+00:00',
        base_url: 'https://iuaa.de/',
      })
    api.post
      .mockResolvedValueOnce({ reply: 'pong' })
      .mockResolvedValueOnce({ dimensions: 1536 })

    const wrapper = mount(Settings)
    await flushPromises()

    const llmButton = wrapper.findAll('button').find((button) => button.text().includes('测试大脑接入'))
    const embeddingButton = wrapper.findAll('button').find((button) => button.text().includes('测试记忆检索'))

    await llmButton.trigger('click')
    await flushPromises()
    await embeddingButton.trigger('click')
    await flushPromises()

    expect(api.post.mock.calls[0][0]).toBe('/config/test-llm')
    expect(api.post.mock.calls[1][0]).toBe('/config/test-embedding')
    expect(wrapper.text()).toContain('记忆检索测试通过')
  })
})
