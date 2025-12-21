<template>
  <n-card title="流程编辑器" class="flow-editor-card">
    <div class="flow-container">
      <div class="flow-controls">
        <n-button type="primary" @click="saveFlow" class="mr-2">保存流程</n-button>
        <n-button @click="clearFlow" class="mr-2">清空画布</n-button>
        <n-button @click="loadSampleFlow" class="mr-2">加载示例</n-button>
        <n-dropdown trigger="hover">
          <n-button>添加节点</n-button>
          <n-dropdown-menu slot="options">
            <n-dropdown-item @click="addInputNode">输入节点</n-dropdown-item>
            <n-dropdown-item @click="addProcessNode">处理节点</n-dropdown-item>
            <n-dropdown-item @click="addOutputNode">输出节点</n-dropdown-item>
            <n-dropdown-item @click="addConditionNode">条件节点</n-dropdown-item>
          </n-dropdown-menu>
        </n-dropdown>
        <n-message-provider>
        </n-message-provider>
      </div>
      <div ref="editorContainer" class="flow-canvas"></div>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { Core, Node } from '@baklavajs/core';
import { VueFlow } from '@baklavajs/renderer-vue';
import { useMessage } from 'naive-ui';
import { onMounted, onUnmounted, ref } from 'vue';

// 容器引用
const editorContainer = ref<HTMLElement | null>(null);
// 创建核心实例
const core = ref(new Core());
// 编辑器实例
let editorInstance: VueFlow | null = null;
// 消息提示
const message = useMessage();

// 自定义节点类
class InputNode extends Node {
  constructor() {
    super();
    this.name = '输入节点';
    this.addOutputInterface('输出');
    // 添加属性
    this.addOption('名称', 'StringOption', '数据输入');
    this.addOption('类型', 'SelectOption', '文本', {
      items: ['文本', '数字', '布尔值', '数组', '对象']
    });
  }
}

class ProcessNode extends Node {
  constructor() {
    super();
    this.name = '处理节点';
    this.addInputInterface('输入');
    this.addOutputInterface('成功');
    // 添加处理选项
    this.addOption('处理方式', 'SelectOption', '转换', {
      items: ['转换', '过滤', '映射', '计算']
    });
    this.addOption('参数', 'StringOption', '');
  }
}

class OutputNode extends Node {
  constructor() {
    super();
    this.name = '输出节点';
    this.addInputInterface('输入');
    // 添加输出选项
    this.addOption('输出类型', 'SelectOption', '控制台', {
      items: ['控制台', '文件', 'API', '变量']
    });
  }
}

class ConditionNode extends Node {
  constructor() {
    super();
    this.name = '条件节点';
    this.addInputInterface('输入');
    this.addOutputInterface('真');
    this.addOutputInterface('假');
    // 添加条件选项
    this.addOption('条件', 'SelectOption', '等于', {
      items: ['等于', '大于', '小于', '包含', '不等于']
    });
    this.addOption('比较值', 'StringOption', '');
  }
}

// 组件挂载时初始化
onMounted(() => {
  if (!editorContainer.value) return;
  
  try {
    // 注册自定义节点类型
    core.value.registerNodeType('InputNode', InputNode);
    core.value.registerNodeType('ProcessNode', ProcessNode);
    core.value.registerNodeType('OutputNode', OutputNode);
    core.value.registerNodeType('ConditionNode', ConditionNode);
    
    // 初始化VueFlow编辑器
    editorInstance = new VueFlow(core.value);
    editorInstance.mount(editorContainer.value);
    
    console.log('FlowEditor 已初始化');
    message.success('流程编辑器已加载');
  } catch (error) {
    console.error('初始化FlowEditor失败:', error);
    message.error('流程编辑器加载失败');
  }
});

// 组件卸载时清理
onUnmounted(() => {
  if (editorInstance) {
    try {
      editorInstance.unmount();
      console.log('FlowEditor 已卸载');
    } catch (error) {
      console.error('卸载FlowEditor失败:', error);
    }
  }
});

// 保存流程
const saveFlow = () => {
  try {
    const flow = core.value.exportNodes();
    console.log('保存流程:', flow);
    // 模拟保存到后端
    message.success('流程已保存');
    
    // 这里可以使用axios将流程保存到后端
    // axios.post('/api/flows', { flow })
    //   .then(response => {
    //     message.success('流程保存成功');
    //   })
    //   .catch(error => {
    //     message.error('流程保存失败');
    //   });
  } catch (error) {
    console.error('保存流程失败:', error);
    message.error('流程保存失败');
  }
};

// 清空画布
const clearFlow = () => {
  try {
    core.value.clear();
    message.success('画布已清空');
  } catch (error) {
    console.error('清空画布失败:', error);
    message.error('清空画布失败');
  }
};

// 加载示例流程
const loadSampleFlow = () => {
  try {
    // 清空现有节点
    core.value.clear();
    
    // 创建示例流程图
    const inputNode = new InputNode();
    inputNode.position = { x: 100, y: 200 };
    core.value.addNode(inputNode);
    
    const processNode = new ProcessNode();
    processNode.position = { x: 300, y: 200 };
    core.value.addNode(processNode);
    
    const conditionNode = new ConditionNode();
    conditionNode.position = { x: 500, y: 200 };
    core.value.addNode(conditionNode);
    
    const outputNode1 = new OutputNode();
    outputNode1.name = '成功输出';
    outputNode1.position = { x: 700, y: 100 };
    core.value.addNode(outputNode1);
    
    const outputNode2 = new OutputNode();
    outputNode2.name = '失败输出';
    outputNode2.position = { x: 700, y: 300 };
    core.value.addNode(outputNode2);
    
    // 创建连接
    core.value.createConnection(inputNode.interfaces.outputs[0], processNode.interfaces.inputs[0]);
    core.value.createConnection(processNode.interfaces.outputs[0], conditionNode.interfaces.inputs[0]);
    core.value.createConnection(conditionNode.interfaces.outputs[0], outputNode1.interfaces.inputs[0]);
    core.value.createConnection(conditionNode.interfaces.outputs[1], outputNode2.interfaces.inputs[0]);
    
    message.success('示例流程已加载');
  } catch (error) {
    console.error('加载示例流程失败:', error);
    message.error('加载示例流程失败');
  }
};

// 添加输入节点
const addInputNode = () => {
  try {
    const node = new InputNode();
    node.position = { x: 100, y: 100 };
    core.value.addNode(node);
    message.success('输入节点已添加');
  } catch (error) {
    console.error('添加输入节点失败:', error);
    message.error('添加输入节点失败');
  }
};

// 添加处理节点
const addProcessNode = () => {
  try {
    const node = new ProcessNode();
    node.position = { x: 300, y: 100 };
    core.value.addNode(node);
    message.success('处理节点已添加');
  } catch (error) {
    console.error('添加处理节点失败:', error);
    message.error('添加处理节点失败');
  }
};

// 添加输出节点
const addOutputNode = () => {
  try {
    const node = new OutputNode();
    node.position = { x: 500, y: 100 };
    core.value.addNode(node);
    message.success('输出节点已添加');
  } catch (error) {
    console.error('添加输出节点失败:', error);
    message.error('添加输出节点失败');
  }
};

// 添加条件节点
const addConditionNode = () => {
  try {
    const node = new ConditionNode();
    node.position = { x: 500, y: 100 };
    core.value.addNode(node);
    message.success('条件节点已添加');
  } catch (error) {
    console.error('添加条件节点失败:', error);
    message.error('添加条件节点失败');
  }
};
</script>

<style scoped>
.flow-editor-card {
  height: 100%;
  min-height: calc(100vh - 120px);
}

.flow-container {
  height: calc(100% - 50px); /* 减去card header高度 */
  display: flex;
  flex-direction: column;
}

.flow-controls {
  padding: 12px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.flow-canvas {
  flex: 1;
  background-color: #f5f5f5;
  overflow: auto;
  position: relative;
  min-height: 400px;
}

.mr-2 {
  margin-right: 8px;
}

/* Baklava节点样式 */
:deep(.baklava-node) {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 180px;
}

:deep(.baklava-node-header) {
  background-color: #409eff;
  color: white;
  border-radius: 8px 8px 0 0;
  padding: 8px 12px;
  font-weight: 500;
}

:deep(.baklava-node-content) {
  padding: 12px;
}

:deep(.baklava-node-interface) {
  background-color: #409eff;
  color: white;
  border-radius: 4px;
  padding: 4px 8px;
  margin: 4px 0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.baklava-node-interface:hover) {
  background-color: #66b1ff;
  transform: scale(1.05);
}

:deep(.baklava-connection) {
  stroke: #409eff;
  stroke-width: 2px;
}

:deep(.baklava-port) {
  background-color: #409eff;
  border: 2px solid white;
  transition: all 0.2s;
}

:deep(.baklava-port:hover) {
  background-color: #66b1ff;
  transform: scale(1.2);
}

:deep(.baklava-node-options) {
  margin-top: 8px;
}

:deep(.baklava-edge-preview) {
  stroke: #409eff;
  stroke-width: 2px;
  stroke-dasharray: 5, 5;
}

/* 确保编辑器可以正确滚动 */
:deep(.vue-flow__pane) {
  width: 100% !important;
  height: 100% !important;
}

:deep(.vue-flow__viewport) {
  transform-origin: 0 0;
}
</style>