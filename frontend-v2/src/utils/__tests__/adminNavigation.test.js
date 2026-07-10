import { getPostLoginRoute, shouldOpenSettingsAfterLogin } from '../adminNavigation'

describe('admin navigation helpers', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('routes the first initialized login to settings', () => {
    expect(shouldOpenSettingsAfterLogin()).toBe(true)
    expect(getPostLoginRoute(true)).toBe('/admin/settings')
    expect(window.localStorage.getItem('qz_admin_seen_settings')).toBe('1')
  })

  it('routes later initialized logins to dashboard', () => {
    window.localStorage.setItem('qz_admin_seen_settings', '1')
    expect(getPostLoginRoute(true)).toBe('/admin/')
  })

  it('keeps uninitialized users on setup', () => {
    expect(getPostLoginRoute(false)).toBe('/admin/setup')
  })
})
