# 投研RAG系统 - Next.js前端

这是投研RAG系统的现代化Next.js前端界面，采用最新的React技术栈构建。

## 🚀 技术栈

- **Next.js 14** - React全栈框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 原子化CSS框架
- **Lucide React** - 现代图标库
- **Framer Motion** - 动画库
- **Zustand** - 状态管理
- **React Hook Form** - 表单处理
- **Axios** - HTTP客户端

## 📱 主要功能

- ✨ **现代化UI设计** - 美观、直观的用户界面
- 💬 **智能聊天界面** - 实时对话体验
- 📤 **文件拖拽上传** - 支持多种文档格式
- 🌓 **主题切换** - 深色/浅色模式
- 📱 **响应式设计** - 完美适配所有设备
- 🔍 **历史记录管理** - 搜索、筛选对话记录
- 📊 **数据可视化** - 直观展示分析结果

## 🛠 开发环境

### 系统要求

- Node.js 18+
- npm 或 yarn
- Python 3.8+ (后端)

### 快速启动

1. **自动启动** (推荐)
   ```bash
   # 在项目根目录运行
   python start_system.py
   ```

2. **手动启动**
   ```bash
   # 安装依赖
   npm install

   # 启动开发服务器
   npm run dev

   # 访问 http://localhost:3005
   ```

### 可用脚本

- `npm run dev` - 启动开发服务器 (端口3005)
- `npm run build` - 构建生产版本
- `npm run start` - 启动生产服务器
- `npm run lint` - 代码检查
- `npm run test` - 运行测试

## 📁 项目结构

```
frontend-next/
├── app/                    # Next.js App Router
│   ├── (routes)/          # 路由组
│   ├── api/               # API路由
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 首页
├── components/            # React组件
│   ├── ui/               # 基础UI组件
│   ├── chat/             # 聊天相关组件
│   ├── upload/           # 上传相关组件
│   ├── layout/           # 布局组件
│   └── providers/        # Context提供者
├── lib/                  # 工具库
│   ├── types.ts          # TypeScript类型定义
│   ├── utils.ts          # 工具函数
│   ├── api.ts            # API客户端
│   └── hooks.ts          # 自定义Hooks
├── hooks/                # React Hooks
├── stores/               # Zustand状态管理
├── styles/               # 样式文件
└── public/               # 静态资源
```

## 🎨 核心组件

### 聊天系统
- `ChatInterface` - 主聊天界面
- `MessageBubble` - 消息气泡
- `InputArea` - 消息输入区

### 文件上传
- `FileUpload` - 拖拽上传组件
- `UploadProgress` - 上传进度显示
- `FilePreview` - 文件预览

### UI组件库
- `Button` - 按钮组件
- `Card` - 卡片组件
- `Input` - 输入框组件
- `Badge` - 标签组件

## 🔧 配置说明

### 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=投研RAG智能问答系统
```

### Tailwind配置

主题配置在 `tailwind.config.js` 中，支持：
- 自定义颜色系统
- 深色模式
- 响应式断点
- 自定义动画

## 📞 API集成

前端通过 `lib/api.ts` 与后端通信：

- `POST /ask` - 发送问题
- `GET /companies` - 获取公司列表
- `POST /upload` - 上传文档
- `GET /history` - 获取对话历史

## 🧪 测试

```bash
# 单元测试
npm run test

# 监听模式
npm run test:watch

# E2E测试
npm run test:e2e
```

## 🚀 部署

### 构建生产版本

```bash
npm run build
npm run start
```

### Docker部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3005
CMD ["npm", "start"]
```

## 🔗 相关链接

- [Next.js文档](https://nextjs.org/docs)
- [Tailwind CSS文档](https://tailwindcss.com/docs)
- [TypeScript文档](https://www.typescriptlang.org/docs)
- [项目主仓库](../README.md)

---

如有问题，请查看项目文档或提交Issue。
