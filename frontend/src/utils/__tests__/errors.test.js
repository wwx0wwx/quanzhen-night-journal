import { describeError } from '../errors'

describe('describeError', () => {
  it('maps internal lock errors to user-facing copy', () => {
    expect(describeError(new Error('database is locked'))).toBe('系统正在处理其他写入，请稍后重试。')
  })

  it('prefers structured code mapping when available', () => {
    expect(describeError({ code: 3001 }, 'fallback')).toBe('系统尚未初始化，请先完成初始化配置。')
  })
})
