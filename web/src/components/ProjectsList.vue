<template>
  <n-card title="项目列表" class="projects-list-card">
    <n-button type="primary" @click="createNewProject" class="mb-4">创建新项目</n-button>
    
    <n-data-table
      :columns="columns"
      :data="projects"
      :pagination="pagination"
      row-key="id"
      :single-line="false"
    >
      <template #default-header-cell="{ column }">
        <div v-if="column.key !== 'actions'" class="font-bold">
          {{ column.title }}
        </div
      </template
      <template #default="{ row }">
        <table-cell v-if="row.type === 'date'">
          {{ formatDate(row.rowData[row.key]) }}
        <table-cell
      </template
      <template #actions="{ row }">
        <n-space>
          <n-button size="small" @click="editProject(row)">编辑</n-button
          <n-button size="small" type="primary" @click="openFlowEditor(row)">流程编辑</n-button
          <n-button size="small" type="error" @click="deleteProject(row.id)">删除</n-button
        <n-space>
      </template
    </n-data-table
  </n-card
  
  <!-- 创建/编辑项目对话框 -->
  <n-modal v-model:show="projectModalVisible" :title="isEditMode ? '编辑项目' : '创建项目'"
    preset="dialog"
    positive-text="确认"
    negative-text="取消"
    @positive-click="saveProject"
  >
    <n-form ref="projectFormRef" :model="currentProject" :rules="projectRules"
      label-placement="top"
    >
      <n-form-item label="项目名称" path="name"
        <n-input v-model:value="currentProject.name" placeholder="请输入项目名称" />
      </n-form-item
      <n-form-item label="项目描述" path="description"
        <n-input
          v-model:value="currentProject.description"
          type="textarea"
          placeholder="请输入项目描述"
          :autosize="{ minRows: 3, maxRows: 6 }"
        />
      </n-form-item
    </n-form
  </n-modal
</template

<script setup lang="ts"
import { ref, reactive, computed, onMounted } from 'vue'
import type { FormInstance } from 'naive-ui'

// 项目列表数据
const projects = ref([
  {
    id: 1,
    name: '数据处理流程',
    description: '用于处理和转换数据的工作流',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    status: 'active'
  },
  {
    id: 2,
    name: 'API集成测试',
    description: '测试不同API的集成流程',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    status: 'active'
  }
])

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  pageSizes: [10, 20, 50],
  showSizePicker: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条数据`
})

// 表格列配置
const columns = [
  {
    title: '项目名称',
    key: 'name',
    width: 200
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: true
  },
  {
    title: '创建时间',
    key: 'createdAt',
    type: 'date',
    width: 180
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return (
        <n-tag type="success" v-if="row.status === 'active'">活跃</n-tag
        <n-tag type="info" v-else>非活跃</n-tag
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
]

// 对话框相关
const projectModalVisible = ref(false)
const isEditMode = ref(false)
const projectFormRef = ref<FormInstance | null>(null)

// 当前项目数据
const currentProject = reactive({
  id: 0,
  name: '',
  description: ''
})

// 表单验证规则
const projectRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: false, message: '请输入项目描述', trigger: 'blur' },
    { max: 200, message: '长度不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 创建新项目
const createNewProject = () => {
  isEditMode.value = false
  Object.assign(currentProject, {
    id: 0,
    name: '',
    description: ''
  })
  projectModalVisible.value = true
}

// 编辑项目
const editProject = (project) => {
  isEditMode.value = true
  Object.assign(currentProject, project)
  projectModalVisible.value = true
}

// 保存项目
const saveProject = () => {
  if (projectFormRef.value) {
    projectFormRef.value.validate((errors) => {
      if (!errors) {
        if (isEditMode.value) {
          // 编辑现有项目
          const index = projects.value.findIndex(p => p.id === currentProject.id)
          if (index !== -1) {
            projects.value[index] = {
              ...projects.value[index],
              ...currentProject,
              updatedAt: new Date().toISOString()
            }
          }
        } else {
          // 创建新项目
          const newProject = {
            ...currentProject,
            id: Date.now(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            status: 'active'
          }
          projects.value.unshift(newProject)
        }
        projectModalVisible.value = false
      }
    })
  }
}

// 删除项目
const deleteProject = (id) => {
  projects.value = projects.value.filter(p => p.id !== id)
}

// 打开流程编辑器
const openFlowEditor = (project) => {
  // 切换到流程编辑器标签页
  window.location.href = '#/editor'
  // 可以在这里存储当前选中的项目ID
  console.log('打开项目:', project.name)
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 组件挂载时获取项目列表
onMounted(() => {
  console.log('ProjectsList 已初始化')
  // 这里可以使用axios从后端获取项目列表
})
</script

<style scoped
.projects-list-card {
  height: calc(100vh - 200px);
  overflow: auto;
}

:deep(.n-data-table) {
  max-height: calc(100vh - 300px);
}

:deep(.n-data-table-empty) {
  min-height: 200px;
}

.n-space {
  display: flex;
  gap: 8px;
}

.table-cell {
  display: flex;
  align-items: center;
}
</style
