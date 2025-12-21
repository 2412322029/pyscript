<template>
  <n-layout>
    <n-layout-header>
      <n-card bordered="false" class="header-card">
        <div class="header-content">
          <h1 class="logo">PyScript Flow</h1>
          <div class="header-actions">
            <n-dropdown trigger="hover">
              <n-avatar circle>
                <img src="https://picsum.photos/id/237/100/100" alt="用户头像" />
              </n-avatar>
              <n-dropdown-menu slot="options">
                <n-dropdown-item @click="handleLogout">退出登录</n-dropdown-item>
              </n-dropdown-menu>
            </n-dropdown>
          </div>
        </div>
      </n-card>
    </n-layout-header>
    <n-layout has-sider>
      <n-layout-sider bordered collapse-mode="width" :width="240" :collapsed-width="64" :show-toggle-button="true" class="sidebar">
        <n-menu :active-key="activeMenuKey" @update:value="updateMenuKey" :collapsed="isCollapsed" mode="vertical">
          <n-menu-item key="projects" class="menu-item">
            <template #icon>
              <n-icon><project-outline /></n-icon>
            </template>
            <span v-if="!isCollapsed">项目管理</span>
          </n-menu-item>
          <n-menu-item key="editor" class="menu-item">
            <template #icon>
              <n-icon><code-slash-outline /></n-icon>
            </template>
            <span v-if="!isCollapsed">流程编辑器</span>
          </n-menu-item>
        </n-menu>
      </n-layout-sider>
      <n-layout>
        <n-layout-content class="main-content">
          <!-- 使用我们创建的组件 -->
          <projects-list v-if="activeMenuKey === 'projects'" />
          <flow-editor v-if="activeMenuKey === 'editor'" />
        </n-layout-content>
      </n-layout>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { CodeSlashOutline, ProjectOutline } from '@vicons/ionicons5'
import { computed, onMounted, ref } from 'vue'
import FlowEditor from './components/FlowEditor.vue'
import ProjectsList from './components/ProjectsList.vue'

// 响应式数据
const activeMenuKey = ref('projects')
const isCollapsed = ref(false)

// 计算属性 - 从URL获取当前标签页
const currentTab = computed(() => {
  const hash = window.location.hash
  return hash.replace('#/', '') || 'projects'
})

// 方法
const updateMenuKey = (key: string) => {
  activeMenuKey.value = key
  window.location.hash = `#/${key}`
}

const handleLogout = () => {
  // 退出登录逻辑
  console.log('退出登录')
}

// 监听侧边栏折叠状态变化
const handleSiderToggle = (collapsed: boolean) => {
  isCollapsed.value = collapsed
}

// 生命周期
onMounted(() => {
  // 根据URL初始化当前标签页
  if (currentTab.value) {
    activeMenuKey.value = currentTab.value
  }
  
  // 监听URL变化
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash
    const tab = hash.replace('#/', '')
    if (tab && ['projects', 'editor'].includes(tab)) {
      activeMenuKey.value = tab
    }
  })
})
</script>

<style scoped>
.header-card {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.sidebar {
  background-color: #fff;
  overflow: hidden;
}

.menu-item {
  transition: all 0.3s;
}

.menu-item:hover {
  background-color: #f5f7fa !important;
}

.main-content {
  padding: 24px;
  background-color: #f5f7fa;
  overflow-y: auto;
  min-height: calc(100vh - 64px);
}

/* 确保组件能够正确渲染 */
:deep(.n-layout) {
  height: 100%;
}

:deep(.n-layout-header) {
  padding: 0;
  height: 64px;
  min-height: 64px;
}

:deep(.n-layout-sider) {
  height: calc(100vh - 64px);
  top: 64px;
}

:deep(.n-layout-sider-rail) {
  top: 64px;
  height: calc(100vh - 64px);
}

:deep(.n-layout-content) {
  height: calc(100vh - 64px);
  overflow: auto;
}
</style>

<style>
/* 全局样式 */
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
  overflow: hidden;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>