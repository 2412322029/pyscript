// @ts-ignore
import { BaklavaVuePlugin } from '@baklavajs/plugin-renderer-vue'
import '@baklavajs/plugin-renderer-vue/dist/styles.css'
import { create, NButton, NCard, NLayout, NLayoutContent, NLayoutFooter, NLayoutHeader, NMenu } from 'naive-ui'
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// 创建 naive-ui 配置
const naive = create({
  components: [
    NButton,
    NLayout,
    NLayoutHeader,
    NLayoutContent,
    NLayoutFooter,
    NMenu,
    NCard
  ]
})

const app = createApp(App)
app.use(naive)
app.use(BaklavaVuePlugin)
app.mount('#app')

