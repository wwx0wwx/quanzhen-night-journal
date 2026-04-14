import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'

import Login from '../Login.vue'
import Setup from '../Setup.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

describe('auth forms', () => {
  beforeEach(() => {
    push.mockReset()
  })

  it('renders login password as empty by default', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [createPinia()],
      },
    })

    expect(wrapper.find('input[type="password"]').element.value).toBe('')
  })

  it('renders setup new password as empty by default', () => {
    const wrapper = mount(Setup, {
      global: {
        plugins: [createPinia()],
      },
    })

    expect(wrapper.find('input[autocomplete="new-password"]').element.value).toBe('')
  })
})
