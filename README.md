# Python Script Runner

## 项目简介
Python Script Runner 是一个使用 FastAPI 和 Vue 3 构建的 Web 应用，允许用户创建、管理和执行 Python 脚本。

## 技术栈
- **后端**: FastAPI + SQLAlchemy
- **前端**: Vue 3 + Vite
- **包管理**: uv

## 使用 uv 和 FastAPI 的优势

### uv 包管理工具优势
1. **速度优势**: uv 是一个用 Rust 编写的 Python 包管理工具，比 pip 快 10-100 倍
2. **确定性**: 使用 lock 文件确保依赖版本的确定性，避免"依赖地狱"
3. **兼容性**: 完全兼容 pip 和 PyPI
4. **并行安装**: 支持并行安装依赖，大幅提升安装速度
5. **内存效率**: 更高效的内存使用，适合资源受限环境
6. **现代设计**: 采用现代架构设计，提供更好的开发者体验

### FastAPI 优势
1. **性能卓越**: 基于 Starlette 和 Pydantic，性能接近 NodeJS 和 Go
2. **异步支持**: 原生支持异步编程，提高并发处理能力
3. **自动文档**: 自动生成 OpenAPI 和 ReDoc 文档
4. **类型提示**: 基于 Python 类型提示，提供更好的编辑器支持和代码补全
5. **数据验证**: 通过 Pydantic 提供强大的数据验证功能
6. **依赖注入**: 内置依赖注入系统，简化代码组织
7. **安全性**: 内置安全特性，包括 OAuth2、JWT 支持等
8. **WebSocket 支持**: 原生支持 WebSocket，适合实时应用

## 项目结构
```
backend/
  ├── app.py           # Flask 兼容层 (保留用于向后兼容)
  ├── main.py          # FastAPI 主应用
  ├── models/          # 数据库模型
  ├── schemas/         # Pydantic 模型
  ├── services/        # 业务逻辑服务
  │   ├── project_service.py        # 项目管理服务
  │   └── script_execution_service.py  # 脚本执行服务
scripts/               # 工具脚本
```

## 安装指南

### 使用 uv 安装依赖
```bash
# 安装 uv (如果尚未安装)
pip install uv

# 使用 uv 安装项目依赖
uv pip install -r requirements.txt
```

## 运行应用

### 运行 FastAPI 后端
```bash
# 直接运行
python -m uvicorn backend.main:app --reload

# 或使用环境变量指定端口
PORT=8000 python -m uvicorn backend.main:app --reload
```

### 运行前端开发服务器
```bash
cd backend/static
npm install
npm run dev
```

## API 文档
启动 FastAPI 后端后，可以访问以下文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要功能
1. **项目管理**: 创建、读取、更新和删除项目
2. **脚本管理**: 在项目中管理 Python 脚本
3. **脚本执行**: 执行 Python 脚本并查看输出
4. **展示界面**: 创建和管理展示界面

## 从 Flask 迁移到 FastAPI 的收益
1. **性能提升**: 异步处理大幅提升并发性能
2. **自动文档**: 无需额外配置即可获得交互式 API 文档
3. **类型安全**: 通过 Pydantic 提供更强的数据验证和类型安全
4. **现代开发体验**: 更好的开发工具集成和代码补全
5. **可扩展性**: 更好的模块化和组件重用能力