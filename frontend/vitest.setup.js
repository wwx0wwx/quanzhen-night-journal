import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import i18n from './src/i18n'

const pinia = createPinia()
setActivePinia(pinia)

config.global.plugins = [...(config.global.plugins || []), pinia, i18n]
