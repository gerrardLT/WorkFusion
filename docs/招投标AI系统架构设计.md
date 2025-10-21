# 招投标AI提效系统 - 系统架构设计文档

**文档版本：** v1.0
**创建时间：** 2025年10月15日
**文档类型：** 技术架构设计
**目标读者：** 技术架构师、后端/前端开发工程师、DevOps工程师

---

## 📋 文档说明

本文档描述招投标AI提效系统的完整技术架构，明确标注**现有架构保留**与**新增模块扩展**：

- **【保留】** - 当前系统已有，完全不修改核心代码和架构
- **【增强】** - 在现有模块上增加功能，但保持架构不变
- **【新增】** - 全新模块，作为独立服务添加，不影响现有代码

**核心原则：保持现有架构，模块化扩展，向后兼容**

---

## 1. 架构概览

### 1.1 总体架构图

```
                     ┌─────────────────────────────────────┐
                     │         前端层 (Frontend)           │
                     │                                     │
                     │  Next.js 14 + React 18 + TypeScript │
                     │  Tailwind CSS + Zustand            │
                     │                                     │
                     │  【保留】聊天界面 + 文档上传         │
                     │  【新增】Dashboard + 知识库管理      │
                     └──────────────┬──────────────────────┘
                                    │ HTTP/REST API
                                    │ WebSocket (可选)
                     ┌──────────────▼──────────────────────┐
                     │      API网关层 (API Gateway)        │
                     │                                     │
                     │    FastAPI + Uvicorn               │
                     │    /api/v2/*                       │
                     │                                     │
                     │  【保留】/chat, /upload, /scenarios │
                     │  【新增】/projects, /knowledge      │
                     └──────────────┬──────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
┌─────────▼────────┐   ┌───────────▼──────────┐   ┌────────▼─────────┐
│  业务服务层       │   │   AI核心引擎层       │   │   数据服务层      │
│  (Services)      │   │   (AI Engine)       │   │   (Data Layer)   │
│                  │   │                     │   │                  │
│【保留】场景服务   │   │【保留】Agentic RAG  │   │【保留】SQLite    │
│【保留】文档服务   │   │  - 混合检索器       │   │【保留】FAISS     │
│【保留】进度管理   │   │  - 智能路由Agent    │   │【保留】BM25      │
│                  │   │  - 分层导航器       │   │                  │
│【新增】爬虫服务   │   │  - 智能缓存         │   │【新增】项目库    │
│【新增】推荐服务   │   │  - 答案验证器       │   │【新增】企业库    │
│【新增】评估服务   │   │                     │   │【新增】知识库    │
│                  │   │【新增】内容生成     │   │                  │
└──────────────────┘   │【新增】风险识别     │   └──────────────────┘
                       │【新增】项目匹配     │
                       │【新增】概率预测     │
                       └─────────────────────┘
                                    │
                     ┌──────────────▼──────────────────────┐
                     │      外部服务层 (External)          │
                     │                                     │
                     │  【保留】DashScope API (通义千问)   │
                     │  【新增】招标平台 (爬虫对接)         │
                     │  【新增】OSS存储 (可选)             │
                     └─────────────────────────────────────┘
```

---

### 1.2 技术栈总览

#### **前端技术栈【保留 + 新增】**

| 技术 | 版本 | 用途 | 状态 |
|------|------|------|------|
| **Next.js** | 14 | React框架（App Router） | 【保留】 |
| **React** | 18 | UI库 | 【保留】 |
| **TypeScript** | 5+ | 类型安全 | 【保留】 |
| **Tailwind CSS** | 3+ | 样式框架 | 【保留】 |
| **Zustand** | 4+ | 状态管理 | 【保留】 |
| **Axios** | 1+ | HTTP客户端 | 【保留】 |
| **Lucide React** | - | 图标库 | 【保留】 |
| **React Markdown** | - | Markdown渲染 | 【保留】 |
| **Recharts** | 2+ | 图表库 | 【新增】 |
| **React Dropzone** | 14+ | 文件上传 | 【保留】 |

---

#### **后端技术栈【保留 + 新增】**

| 技术 | 版本 | 用途 | 状态 |
|------|------|------|------|
| **Python** | 3.10+ | 后端开发语言 | 【保留】 |
| **FastAPI** | 0.104+ | Web框架 | 【保留】 |
| **Uvicorn** | 0.24+ | ASGI服务器 | 【保留】 |
| **SQLAlchemy** | 2.0+ | ORM | 【保留】 |
| **SQLite** | 3.x | 数据库（开发/小规模） | 【保留】 |
| **PostgreSQL** | 14+ | 数据库（生产环境） | 【新增-可选】 |
| **Pydantic** | 2.0+ | 数据验证 | 【保留】 |
| **Scrapy** | 2.11+ | 爬虫框架 | 【新增】 |
| **APScheduler** | 3.10+ | 定时任务 | 【新增】 |
| **Redis** | 7+ | 缓存/消息队列 | 【新增-可选】 |

---

#### **AI/ML技术栈【保留 + 新增】**

| 技术 | 版本 | 用途 | 状态 |
|------|------|------|------|
| **DashScope** | 1.17+ | 通义千问API | 【保留】 |
| **FAISS** | 1.7+ | 向量数据库 | 【保留】 |
| **BM25** | 0.2+ | 关键词检索 | 【保留】 |
| **MinerU** | 2.5.4 | PDF解析引擎 | 【保留】 |
| **PyMuPDF** | 1.23+ | PDF文本提取 | 【保留】 |
| **pdfplumber** | 0.9+ | PDF表格提取 | 【保留】 |
| **scikit-learn** | 1.3+ | 机器学习 | 【新增】 |
| **XGBoost** | 2.0+ | 梯度提升树 | 【新增】 |
| **sentence-transformers** | 2.2+ | 本地嵌入模型（可选） | 【新增-可选】 |

---

### 1.3 核心设计原则

1. **【保留】模块化设计**
   - 每个功能模块独立封装
   - 低耦合、高内聚
   - 便于单独测试和维护

2. **【保留】多场景支持**
   - 场景配置化管理
   - 场景间数据隔离
   - 动态切换无需重启

3. **【新增】可扩展架构**
   - 新功能作为独立服务添加
   - 通过API网关统一入口
   - 支持水平扩展

4. **【保留】性能优先**
   - 多层缓存策略
   - 异步处理
   - 批量操作优化

5. **【新增】数据安全**
   - 数据加密传输（HTTPS）
   - 敏感数据加密存储
   - 权限控制和审计日志

---

## 2. 前端架构

### 2.1 目录结构

```
frontend-next/
├── app/                          # Next.js 14 App Router
│   ├── page.tsx                  【保留】主页（聊天界面）
│   ├── dashboard/                【新增】
│   │   └── page.tsx              仪表盘页面
│   ├── knowledge/                【新增】
│   │   └── page.tsx              知识库管理页面
│   ├── projects/                 【新增】
│   │   ├── page.tsx              项目列表页面
│   │   └── [id]/page.tsx         项目详情页面
│   ├── documents/                【新增】
│   │   └── [id]/page.tsx         文档解析页面（三栏布局）
│   ├── layout.tsx                【保留】全局布局
│   └── globals.css               【保留】全局样式
│
├── components/                   # React组件
│   ├── chat/                     【保留】聊天组件
│   │   ├── chat-interface.tsx   聊天界面
│   │   ├── message-bubble.tsx   消息气泡
│   │   └── input-area.tsx       输入区域
│   │
│   ├── scenario/                 【保留】场景组件
│   │   └── scenario-selector.tsx 场景选择器
│   │
│   ├── upload/                   【保留】上传组件
│   │   └── file-uploader.tsx    文件上传器
│   │
│   ├── dashboard/                【新增】仪表盘组件
│   │   ├── todo-list.tsx        待办列表
│   │   ├── project-card.tsx     项目卡片
│   │   ├── project-board.tsx    项目看板
│   │   └── kpi-panel.tsx        KPI面板
│   │
│   ├── checklist/                【新增】清单组件
│   │   ├── checklist-panel.tsx  清单面板
│   │   └── task-item.tsx        任务项
│   │
│   ├── document/                 【新增】文档组件
│   │   ├── document-viewer.tsx  文档预览器
│   │   ├── risk-highlight.tsx   风险高亮
│   │   └── info-card.tsx        信息卡片
│   │
│   ├── knowledge/                【新增】知识库组件
│   │   ├── knowledge-list.tsx   知识列表
│   │   ├── knowledge-filter.tsx 过滤器
│   │   └── knowledge-card.tsx   知识卡片
│   │
│   └── ui/                       【保留】基础UI组件
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       └── ...
│
├── contexts/                     # React Context
│   └── scenario-context.tsx     【保留】场景上下文
│
├── stores/                       # Zustand状态管理
│   ├── chat-store.ts            【保留】聊天状态
│   ├── upload-store.ts          【保留】上传状态
│   ├── project-store.ts         【新增】项目状态
│   └── knowledge-store.ts       【新增】知识库状态
│
├── lib/                          # 工具库
│   ├── api-v2.ts                【保留 + 扩展】API客户端
│   ├── utils.ts                 【保留】工具函数
│   └── constants.ts             【保留】常量定义
│
├── hooks/                        # 自定义Hooks
│   ├── use-chat.ts              【保留】聊天Hook
│   ├── use-upload.ts            【保留】上传Hook
│   ├── use-projects.ts          【新增】项目Hook
│   └── use-knowledge.ts         【新增】知识库Hook
│
└── types/                        # TypeScript类型定义
    ├── chat.ts                  【保留】聊天类型
    ├── document.ts              【保留】文档类型
    ├── project.ts               【新增】项目类型
    └── knowledge.ts             【新增】知识库类型
```

---

### 2.2 状态管理架构

#### **Zustand Store设计**

**【保留】Chat Store (chat-store.ts)**
```typescript
interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;

  // Actions
  createSession: () => void;
  sendMessage: (content: string) => Promise<void>;
  loadMessages: (sessionId: string) => void;
  // ... 现有方法保持不变
}
```

**【新增】Project Store (project-store.ts)**
```typescript
interface ProjectState {
  projects: Project[];
  filteredProjects: Project[];
  currentProject: Project | null;
  filters: ProjectFilters;

  // Actions
  fetchProjects: () => Promise<void>;
  filterProjects: (filters: ProjectFilters) => void;
  selectProject: (id: string) => void;
  bookmarkProject: (id: string) => void;
}
```

**【新增】Knowledge Store (knowledge-store.ts)**
```typescript
interface KnowledgeState {
  items: KnowledgeItem[];
  categories: string[];
  filters: KnowledgeFilters;

  // Actions
  fetchItems: (category?: string) => Promise<void>;
  searchItems: (query: string) => void;
  uploadItem: (file: File, metadata: any) => Promise<void>;
  deleteItem: (id: string) => Promise<void>;
}
```

---

### 2.3 路由设计

| 路由 | 页面 | 权限 | 状态 |
|------|------|------|------|
| `/` | 聊天界面（主页） | 公开 | 【保留】 |
| `/dashboard` | 仪表盘 | 需登录 | 【新增】 |
| `/projects` | 项目列表 | 需登录 | 【新增】 |
| `/projects/[id]` | 项目详情 | 需登录 | 【新增】 |
| `/documents/[id]` | 文档解析（三栏） | 需登录 | 【新增】 |
| `/knowledge` | 知识库管理 | 需登录 | 【新增】 |
| `/settings` | 系统设置 | 需登录 | 【新增】 |

---

### 2.4 API客户端设计

**【保留 + 扩展】lib/api-v2.ts**

```typescript
// 【保留】现有API客户端
class MultiScenarioAPIClient {
  // 【保留】现有方法
  async ask(question: string, scenarioId: string): Promise<Answer>;
  async uploadFile(file: File, scenarioId: string): Promise<Document>;
  async getSessions(scenarioId: string): Promise<Session[]>;

  // 【新增】项目相关API
  async getProjects(filters?: ProjectFilters): Promise<Project[]>;
  async getProjectDetail(id: string): Promise<ProjectDetail>;
  async evaluateProject(id: string): Promise<EvaluationReport>;

  // 【新增】知识库相关API
  async getKnowledgeItems(category?: string): Promise<KnowledgeItem[]>;
  async uploadKnowledge(file: File, metadata: any): Promise<KnowledgeItem>;
  async searchKnowledge(query: string): Promise<KnowledgeItem[]>;

  // 【新增】Checklist相关API
  async generateChecklist(documentId: string): Promise<Checklist>;
  async updateTaskStatus(taskId: string, status: string): Promise<void>;

  // 【新增】风险识别API
  async detectRisks(documentId: string): Promise<Risk[]>;
}
```

---

## 3. 后端架构

### 3.1 目录结构

```
backend/
├── api/                          # API路由层
│   ├── chat.py                   【保留】问答接口
│   ├── upload.py                 【保留】文件上传接口
│   ├── scenarios.py              【保留】场景管理接口
│   │
│   ├── projects.py               【新增】项目管理接口
│   ├── knowledge.py              【新增】知识库接口
│   ├── evaluation.py             【新增】项目评估接口
│   ├── checklist.py              【新增】清单管理接口
│   └── risks.py                  【新增】风险识别接口
│
├── services/                     # 业务逻辑层
│   ├── scenario_service.py       【保留】场景服务
│   ├── document_service.py       【保留】文档服务
│   ├── progress_manager.py       【保留】进度管理
│   │
│   ├── crawler_service.py        【新增】爬虫服务
│   ├── recommendation_service.py 【新增】推荐服务
│   ├── evaluation_service.py     【新增】评估服务
│   ├── knowledge_service.py      【新增】知识库服务
│   ├── risk_service.py           【新增】风险识别服务
│   └── content_service.py        【新增】内容生成服务
│
├── models/                       # 数据模型
│   ├── base.py                   【保留】基础模型
│   ├── scenario.py               【保留】场景模型
│   ├── document.py               【保留】文档模型
│   ├── chat.py                   【保留】聊天模型
│   │
│   ├── project.py                【新增】项目模型
│   ├── company.py                【新增】企业模型
│   ├── knowledge.py              【新增】知识库模型
│   └── task.py                   【新增】任务模型
│
├── crawler/                      【新增】爬虫模块
│   ├── spiders/                  爬虫实现
│   │   ├── tender_spider.py     招标平台爬虫
│   │   └── ...
│   ├── pipelines.py             数据处理管道
│   ├── middlewares.py           中间件
│   └── settings.py              配置
│
├── database.py                   【保留】数据库连接
├── main_multi_scenario.py        【保留】主入口
└── config.py                     【保留】配置管理
```

---

### 3.2 API路由设计

#### **【保留】现有路由（完全不动）**

```python
# /api/v2/chat/*
POST   /api/v2/chat/ask              # 问答
GET    /api/v2/chat/sessions         # 获取会话列表
POST   /api/v2/chat/sessions         # 创建会话
DELETE /api/v2/chat/sessions/{id}    # 删除会话

# /api/v2/upload/*
POST   /api/v2/upload                # 上传文件
GET    /api/v2/upload/progress/{id}  # 获取进度

# /api/v2/scenarios/*
GET    /api/v2/scenarios             # 获取场景列表
GET    /api/v2/scenarios/{id}        # 获取场景详情
```

---

#### **【新增】独立路由**

```python
# /api/v2/projects/* 【新增】
GET    /api/v2/projects              # 获取项目列表
GET    /api/v2/projects/{id}         # 获取项目详情
POST   /api/v2/projects/{id}/bookmark # 收藏项目
DELETE /api/v2/projects/{id}/bookmark # 取消收藏

# /api/v2/knowledge/* 【新增】
GET    /api/v2/knowledge             # 获取知识库列表
POST   /api/v2/knowledge             # 上传知识项
GET    /api/v2/knowledge/{id}        # 获取知识详情
DELETE /api/v2/knowledge/{id}        # 删除知识项
GET    /api/v2/knowledge/search      # 搜索知识库

# /api/v2/evaluation/* 【新增】
POST   /api/v2/evaluation/generate   # 生成评估报告
GET    /api/v2/evaluation/{id}       # 获取评估报告

# /api/v2/checklist/* 【新增】
POST   /api/v2/documents/{id}/checklist  # 生成Checklist
PUT    /api/v2/checklist/tasks/{id}      # 更新任务状态
POST   /api/v2/checklist/tasks           # 添加新任务

# /api/v2/risks/* 【新增】
POST   /api/v2/documents/{id}/risks      # 识别风险
GET    /api/v2/risks/{id}                # 获取风险详情

# /api/v2/generate/* 【新增】
POST   /api/v2/generate/content          # 生成内容
POST   /api/v2/generate/section          # 生成章节
```

---

### 3.3 服务层设计

#### **【保留】现有服务（完全不修改）**

**ScenarioService (scenario_service.py)**
```python
class ScenarioService:
    """【保留】场景管理服务 - 不修改"""

    def get_all_scenarios(self) -> List[Dict]:
        """获取所有场景"""
        pass

    def get_scenario(self, scenario_id: str) -> Dict:
        """获取特定场景"""
        pass

    def validate_scenario(self, scenario_id: str) -> bool:
        """验证场景是否存在"""
        pass
```

**DocumentService (document_service.py)**
```python
class DocumentService:
    """【保留】文档管理服务 - 不修改"""

    def create_document(self, file, scenario_id: str) -> Document:
        """创建文档记录"""
        pass

    def get_documents(self, scenario_id: str) -> List[Document]:
        """获取文档列表"""
        pass
```

---

#### **【新增】独立服务**

**CrawlerService (crawler_service.py)**
```python
class CrawlerService:
    """【新增】爬虫服务"""

    def __init__(self):
        self.scheduler = APScheduler()

    def start_crawler(self, spider_name: str):
        """启动爬虫"""
        pass

    def get_new_projects(self) -> List[Project]:
        """获取新项目"""
        pass

    def schedule_crawl(self, spider_name: str, cron: str):
        """定时爬取"""
        pass
```

**RecommendationService (recommendation_service.py)**
```python
class RecommendationService:
    """【新增】推荐服务"""

    def __init__(self, bm25_retriever=None):
        # 可复用现有的BM25检索能力
        self.bm25 = bm25_retriever

    def calculate_match_score(
        self,
        project: Project,
        company: Company
    ) -> float:
        """计算项目匹配度"""
        pass

    def recommend_projects(
        self,
        company: Company,
        limit: int = 10
    ) -> List[Project]:
        """推荐项目"""
        pass
```

**RiskService (risk_service.py)**
```python
class RiskService:
    """【新增】风险识别服务"""

    def __init__(self, questions_processor=None):
        # 复用现有的问答能力
        self.qa = questions_processor

    def detect_risks(self, document_id: str) -> List[Risk]:
        """识别风险条款"""
        # 调用现有的QuestionsProcessor
        # 不修改核心RAG逻辑
        pass

    def classify_risk_level(self, risk: Risk) -> str:
        """分类风险等级"""
        pass
```

**ContentService (content_service.py)**
```python
class ContentService:
    """【新增】内容生成服务"""

    def __init__(self, dashscope_client=None):
        # 复用现有的LLM调用
        self.llm = dashscope_client

    def generate_section(
        self,
        section_name: str,
        context: str
    ) -> str:
        """生成章节内容"""
        # 调用现有的DashScope客户端
        pass

    def generate_company_profile(
        self,
        company: Company
    ) -> str:
        """生成公司简介"""
        pass
```

---

## 4. AI核心引擎架构

### 4.1 Agentic RAG架构【保留 - 完全不修改】

```
src/
├── pipeline.py              【保留】RAG主流程
├── questions_processing.py  【保留】问答处理器
├── ingestion.py            【保留】文档摄取
├── pdf_parsing_mineru.py   【保留】PDF解析
├── dashscope_client.py     【保留】DashScope客户端
│
├── retrieval/              【保留】检索组件
│   ├── hybrid_retriever.py    混合检索器
│   ├── bm25_retriever.py      BM25检索
│   ├── vector_retriever.py    向量检索
│   └── layered_navigator.py   分层导航
│
├── agents/                 【保留】智能Agent
│   └── routing_agent.py       路由Agent
│
├── cache/                  【保留】缓存系统
│   └── smart_cache.py         智能缓存
│
└── verification/           【保留】验证系统
    └── answer_verifier.py     答案验证器
```

**核心原则：** 以上所有模块**完全不修改**，保持当前的代码和逻辑不变。

---

### 4.2 新增AI能力【新增 - 独立模块】

```
src/
├── generation/             【新增】内容生成
│   ├── content_generator.py   内容生成引擎
│   ├── template_manager.py    模板管理
│   └── quality_checker.py     质量检查
│
├── analysis/               【新增】分析能力
│   ├── risk_detector.py       风险识别
│   ├── matcher.py             项目匹配
│   └── extractor.py           信息提取
│
└── prediction/             【新增】预测能力
    ├── probability_model.py   中标概率预测
    ├── price_predictor.py     报价预测
    └── feature_engineer.py    特征工程
```

**技术实现：**
- 【新增】模块可以**调用**现有的`QuestionsProcessor`、`DashScopeClient`等
- 【新增】模块通过**组合而非修改**的方式复用现有能力
- 新建独立的Python文件，不修改现有文件

---

### 4.3 AI能力调用关系

```mermaid
graph TD
    A[用户请求] --> B{请求类型}

    B -->|问答| C[【保留】QuestionsProcessor]
    C --> D[【保留】Agentic RAG]
    D --> E[返回答案]

    B -->|生成Checklist| F[【新增】RiskService]
    F --> G[调用现有QA能力]
    G --> C

    B -->|生成内容| H[【新增】ContentService]
    H --> I[调用现有LLM客户端]
    I --> J[【保留】DashScopeClient]

    B -->|项目推荐| K[【新增】RecommendationService]
    K --> L[复用现有BM25检索]
    L --> M[【保留】BM25Retriever]
```

**关键设计：**
- 新功能通过**组合**现有组件实现，不修改核心逻辑
- 新服务作为**独立层**，调用底层能力
- 保持**单向依赖**：新服务可以依赖旧服务，反之不行

---

## 5. 数据架构

### 5.1 数据库设计

#### **【保留】现有数据表（完全不动）**

```sql
-- 场景表
CREATE TABLE scenarios (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    config JSON,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
);

-- 会话表
CREATE TABLE chat_sessions (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
);

-- 消息表
CREATE TABLE chat_messages (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- 文档类型表
CREATE TABLE document_types (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    file_extensions JSON,
    processing_config JSON,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
);
```

---

#### **【新增】独立数据表**

```sql
-- 招标项目表
CREATE TABLE projects (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(100),                -- 来源平台
    source_url VARCHAR(500),            -- 原始链接
    amount DECIMAL(15, 2),              -- 预算金额
    location VARCHAR(100),              -- 地域
    industry VARCHAR(50),               -- 行业
    deadline TIMESTAMP,                 -- 截止时间
    status VARCHAR(20) DEFAULT 'active', -- 状态
    content TEXT,                       -- 项目内容
    requirements JSON,                  -- 要求（结构化）
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 企业信息表
CREATE TABLE companies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    qualifications JSON,                -- 资质列表
    capabilities JSON,                  -- 能力描述
    target_areas JSON,                  -- 目标区域
    target_industries JSON,             -- 目标行业
    budget_range JSON,                  -- 预算范围
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识库分类表
CREATE TABLE knowledge_items (
    id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,     -- 分类：资质/业绩/方案/人员
    doc_id VARCHAR(50),                 -- 关联文档ID
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSON,                          -- 标签
    expire_date DATE,                   -- 到期日期（资质用）
    metadata JSON,                      -- 结构化元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

-- 任务清单表
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50),             -- 关联项目
    doc_id VARCHAR(50),                 -- 关联文档
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending/in_progress/completed
    priority VARCHAR(20) DEFAULT 'normal',
    assigned_to VARCHAR(50),            -- 负责人
    deadline TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

-- 风险记录表
CREATE TABLE risks (
    id VARCHAR(50) PRIMARY KEY,
    doc_id VARCHAR(50) NOT NULL,
    risk_type VARCHAR(50),              -- 废标/无限责任/苛刻条款
    risk_level VARCHAR(20),             -- high/medium/low
    description TEXT,
    location JSON,                      -- 位置信息（页码、坐标）
    suggestion TEXT,                    -- 应对建议
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

-- 项目收藏表
CREATE TABLE project_bookmarks (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),                -- 用户ID（后续加入用户系统）
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 评估报告表
CREATE TABLE evaluation_reports (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,
    company_id VARCHAR(50),
    match_score DECIMAL(5, 2),          -- 匹配度分数
    qualification_match JSON,            -- 资质匹配情况
    risk_analysis JSON,                  -- 风险分析
    recommendation TEXT,                 -- 建议
    report_data JSON,                    -- 完整报告数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
```

---

### 5.2 数据库索引策略

**【保留】现有索引（不修改）**
```sql
-- 现有索引保持不变
CREATE INDEX idx_documents_scenario ON documents(scenario_id);
CREATE INDEX idx_chat_sessions_scenario ON chat_sessions(scenario_id);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
```

**【新增】新表索引**
```sql
-- 项目表索引
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_deadline ON projects(deadline);
CREATE INDEX idx_projects_location ON projects(location);
CREATE INDEX idx_projects_amount ON projects(amount);

-- 知识库表索引
CREATE INDEX idx_knowledge_category ON knowledge_items(category);
CREATE INDEX idx_knowledge_doc ON knowledge_items(doc_id);
CREATE INDEX idx_knowledge_expire ON knowledge_items(expire_date);

-- 任务表索引
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_doc ON tasks(doc_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);

-- 风险表索引
CREATE INDEX idx_risks_doc ON risks(doc_id);
CREATE INDEX idx_risks_level ON risks(risk_level);
```

---

### 5.3 文件存储架构

**【保留】现有存储（完全不动）**

```
data/
├── uploads/                      【保留】用户上传文件
│   └── {scenario_id}/
│       └── {doc_id}.pdf
│
└── stock_data/
    ├── databases/
    │   ├── stock_rag.db          【保留】SQLite数据库
    │   ├── vector_dbs/           【保留】FAISS向量索引
    │   │   └── {scenario_id}/
    │   │       └── index.faiss
    │   └── bm25/                 【保留】BM25索引
    │       └── {scenario_id}/
    │           └── bm25_index.pkl
    │
    └── debug_data/
        └── parsed_reports/       【保留】解析后的文档
            └── {doc_id}.json
```

**【新增】扩展存储**

```
data/
├── projects/                     【新增】爬取的项目数据
│   └── raw/
│       └── {date}/
│           └── {project_id}.json
│
├── knowledge/                    【新增】知识库文件
│   ├── qualifications/           资质证照
│   ├── achievements/             历史业绩
│   ├── solutions/                技术方案
│   └── personnel/                人员档案
│
├── reports/                      【新增】生成的报告
│   ├── evaluation/               评估报告
│   └── checklist/                清单报告
│
└── cache/                        【新增】缓存文件
    └── embeddings/               嵌入向量缓存
```

**存储策略：**
- 小文件（< 10MB）：本地存储
- 大文件（> 10MB）：可选OSS（阿里云OSS / MinIO）
- 热数据：本地 + Redis缓存
- 冷数据：归档到OSS

---

## 6. 外部集成架构

### 6.1 DashScope API集成【保留】

**现有集成（完全不修改）：**

```python
# src/dashscope_client.py 【保留】
class DashScopeClient:
    """【保留】通义千问API客户端 - 不修改"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "qwen-turbo-latest"

    def generate_text(
        self,
        prompt: str,
        messages: List[Dict] = None
    ) -> str:
        """生成文本"""
        # 现有逻辑保持不变
        pass

    def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """生成嵌入向量"""
        # 现有逻辑保持不变
        pass
```

**调用方式：**
- 【保留】`QuestionsProcessor` 调用（不变）
- 【新增】`ContentService` 复用（新建，调用现有客户端）
- 【新增】`RiskService` 复用（新建，调用现有客户端）

---

### 6.2 爬虫框架集成【新增】

**Scrapy框架配置：**

```python
# backend/crawler/settings.py 【新增】
BOT_NAME = 'tender_crawler'

SPIDER_MODULES = ['backend.crawler.spiders']
NEWSPIDER_MODULE = 'backend.crawler.spiders'

# 爬虫设置
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1

# 中间件
DOWNLOADER_MIDDLEWARES = {
    'backend.crawler.middlewares.RandomUserAgentMiddleware': 400,
    'backend.crawler.middlewares.ProxyMiddleware': 410,
}

# 数据管道
ITEM_PIPELINES = {
    'backend.crawler.pipelines.DataCleanPipeline': 300,
    'backend.crawler.pipelines.DatabasePipeline': 400,
}
```

**爬虫示例：**

```python
# backend/crawler/spiders/tender_spider.py 【新增】
import scrapy
from backend.models.project import Project

class TenderSpider(scrapy.Spider):
    name = "tender_spider"

    start_urls = [
        'https://example-tender-platform.com/projects'
    ]

    def parse(self, response):
        """解析项目列表"""
        for project in response.css('.project-item'):
            yield {
                'title': project.css('.title::text').get(),
                'amount': project.css('.amount::text').get(),
                'deadline': project.css('.deadline::text').get(),
                # ...
            }
```

**定时任务：**

```python
# backend/services/crawler_service.py 【新增】
from apscheduler.schedulers.background import BackgroundScheduler

class CrawlerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def schedule_daily_crawl(self):
        """每天凌晨2点爬取"""
        self.scheduler.add_job(
            self.run_spider,
            'cron',
            hour=2,
            args=['tender_spider']
        )
        self.scheduler.start()
```

---

### 6.3 招标平台对接【新增】

**对接平台列表（规划）：**

| 平台 | 对接方式 | 优先级 | 难度 |
|------|---------|--------|------|
| 国家电网ECP | API（需申请） | P2 | 高 |
| 南方电网 | API（需申请） | P2 | 高 |
| 各省公共资源交易中心 | 爬虫 | P2 | 中 |
| 中国招标投标公共服务平台 | 爬虫 | P2 | 中 |

**技术方案：**
- API对接：使用官方SDK（如果提供）
- 爬虫对接：Scrapy + Selenium（应对JavaScript渲染）
- 反爬对策：代理池 + User-Agent轮换 + 限速

---

## 7. 性能与扩展性

### 7.1 缓存策略

#### **【保留】现有缓存（不修改）**

**SmartCache (src/cache/smart_cache.py)**
```python
class SmartCache:
    """【保留】智能缓存 - 不修改"""

    def __init__(self, max_size=1000):
        self.exact_cache = {}       # 精确匹配缓存
        self.semantic_cache = {}    # 语义缓存
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    def set(self, key: str, value: Any, ttl: int):
        """设置缓存"""
        pass
```

---

#### **【新增】多层缓存**

```
┌─────────────────────────────────────┐
│  L1: 内存缓存（SmartCache）【保留】   │
│  - 问答结果缓存                      │
│  - TTL: 7天（精确）/ 3天（语义）      │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│  L2: Redis缓存【新增-可选】          │
│  - API响应缓存                       │
│  - 会话状态缓存                      │
│  - TTL: 1小时                        │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│  L3: 数据库查询缓存【新增】          │
│  - SQLAlchemy查询缓存                │
│  - TTL: 5分钟                        │
└─────────────────────────────────────┘
```

---

### 7.2 性能指标

| 指标 | 当前系统 | 目标系统 | 优化方案 |
|------|---------|---------|----------|
| **文档解析** | 5-10秒/100页 | 5-10秒/100页 | 【保留】已优化 |
| **问答响应** | 2-10秒 | 2-10秒 | 【保留】已优化 |
| **Checklist生成** | N/A | < 30秒 | 【新增】异步处理 |
| **风险识别** | N/A | < 30秒 | 【新增】异步处理 |
| **项目列表加载** | N/A | < 1秒 | 【新增】分页+缓存 |
| **知识库搜索** | N/A | < 1秒 | 【新增】索引优化 |
| **并发用户** | 100 | 200+ | 【新增】水平扩展 |

---

### 7.3 水平扩展方案

**当前架构（单体）：**
```
                 ┌──────────────┐
用户 ────────────▶│  单一服务器   │
                 │  (All-in-One)│
                 └──────────────┘
```

**扩展架构（微服务）：**
```
                 ┌─────────────┐
用户 ────────────▶│  Nginx      │
                 │  (负载均衡)  │
                 └──────┬──────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
  │  Web服务1  │  │  Web服务2  │  │  Web服务3  │
  │  (FastAPI) │  │  (FastAPI) │  │  (FastAPI) │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                 ┌──────▼──────┐
                 │  PostgreSQL │
                 │  (主从复制)  │
                 └─────────────┘
```

**扩展策略：**
1. **阶段1（当前）**：单体应用 + SQLite
2. **阶段2（100+ 用户）**：单体应用 + PostgreSQL
3. **阶段3（500+ 用户）**：负载均衡 + 多实例 + PostgreSQL主从
4. **阶段4（1000+ 用户）**：微服务拆分 + Redis集群 + PostgreSQL集群

---

## 8. 部署架构

### 8.1 开发环境

```
开发机（Windows/Mac/Linux）
├── Python 3.10+ (venv)
├── Node.js 18+
├── SQLite 3.x
├── FAISS (CPU版本)
└── 代码编辑器（VSCode）
```

**启动方式：**
```bash
# 后端
python run_backend.py

# 前端
cd frontend-next && npm run dev
```

---

### 8.2 生产环境（推荐）

```
┌─────────────────────────────────────────────┐
│  云服务器（阿里云/腾讯云/AWS）                │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │  Docker Compose                     │  │
│  │                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐│  │
│  │  │  前端容器     │  │  后端容器     ││  │
│  │  │  (Next.js)   │  │  (FastAPI)   ││  │
│  │  └──────────────┘  └──────────────┘│  │
│  │                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐│  │
│  │  │  PostgreSQL  │  │  Redis       ││  │
│  │  └──────────────┘  └──────────────┘│  │
│  │                                     │  │
│  │  ┌──────────────┐                  │  │
│  │  │  Nginx       │                  │  │
│  │  │  (反向代理)   │                  │  │
│  │  └──────────────┘                  │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Docker Compose配置示例：**

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend-next
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  backend:
    build: ./
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tender_db
      - REDIS_URL=redis://redis:6379
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}

  db:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=tender_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  pgdata:
```

---

### 8.3 CI/CD流程

```mermaid
graph LR
    A[代码提交] --> B[GitHub Actions]
    B --> C{单元测试}
    C -->|通过| D[构建Docker镜像]
    C -->|失败| E[通知开发者]
    D --> F[推送到镜像仓库]
    F --> G[部署到测试环境]
    G --> H{集成测试}
    H -->|通过| I[部署到生产环境]
    H -->|失败| E
```

---

## 9. 安全架构

### 9.1 数据安全

| 层级 | 安全措施 | 实现方案 |
|------|---------|---------|
| **传输层** | HTTPS加密 | Nginx配置SSL证书 |
| **应用层** | API认证 | JWT Token |
| **数据层** | 敏感数据加密 | AES-256加密存储 |
| **访问控制** | RBAC权限管理 | 基于角色的访问控制 |
| **审计** | 操作日志 | 记录所有关键操作 |

---

### 9.2 API安全

**认证流程（规划）：**

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Auth

    User->>Frontend: 登录
    Frontend->>API: POST /auth/login
    API->>Auth: 验证凭据
    Auth-->>API: 返回JWT Token
    API-->>Frontend: 返回Token
    Frontend->>Frontend: 存储Token

    Frontend->>API: GET /api/v2/* (带Token)
    API->>Auth: 验证Token
    Auth-->>API: Token有效
    API-->>Frontend: 返回数据
```

---

## 10. 监控与运维

### 10.1 日志系统

**日志级别：**
- DEBUG: 开发调试信息
- INFO: 一般信息（API调用、业务流程）
- WARNING: 警告信息（性能下降、资源不足）
- ERROR: 错误信息（异常、失败）
- CRITICAL: 严重错误（系统崩溃）

**日志存储：**
```
logs/
├── app.log              # 应用日志
├── api.log              # API请求日志
├── error.log            # 错误日志
├── crawler.log          # 爬虫日志
└── performance.log      # 性能日志
```

---

### 10.2 监控指标

| 指标类别 | 监控项 | 告警阈值 |
|---------|--------|----------|
| **系统资源** | CPU使用率 | > 80% |
| | 内存使用率 | > 85% |
| | 磁盘使用率 | > 90% |
| **应用性能** | API响应时间 | > 5秒 |
| | 错误率 | > 5% |
| | QPS | < 预期50% |
| **业务指标** | 文档解析成功率 | < 95% |
| | 爬虫成功率 | < 90% |
| | 用户活跃度 | 下降20% |

---

## 11. 技术债务与风险

### 11.1 当前技术债务

| 项目 | 描述 | 优先级 | 计划 |
|------|------|--------|------|
| **会话持久化** | 当前会话存储在内存，重启丢失 | P1 | 阶段2迁移到数据库 |
| **用户系统** | 缺少完整的用户认证和权限管理 | P1 | 阶段2实现 |
| **数据库迁移** | 生产环境需从SQLite迁移到PostgreSQL | P2 | 阶段2实现 |
| **测试覆盖** | 单元测试覆盖率不足 | P2 | 持续改进 |

---

### 11.2 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **爬虫反爬** | 无法获取招标信息 | 代理池 + 限速 + 人工审核 |
| **API限流** | DashScope API被限流 | 多账号轮换 + 请求队列 |
| **性能瓶颈** | 并发用户增多导致响应变慢 | 缓存 + 负载均衡 + 异步处理 |
| **数据安全** | 用户数据泄露 | 加密存储 + 访问控制 + 审计 |

---

## 12. 附录

### 12.1 关键配置文件

**后端配置 (.env)**
```env
# DashScope API
DASHSCOPE_API_KEY=your_api_key

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/tender_db

# Redis
REDIS_URL=redis://localhost:6379

# 文件存储
DATA_DIR=data/stock_data

# 日志
LOG_LEVEL=INFO
```

**前端配置 (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

### 12.2 参考文档

- [功能交互设计文档](./招投标AI系统功能交互设计.md)
- [开发任务清单](./招投标AI系统开发任务清单.md)
- [招投标PRD与当前系统功能对比分析](./招投标PRD与当前系统功能对比分析.md)

---

**文档版本：** v1.0
**创建时间：** 2025年10月15日
**下次更新：** 架构评审后（预计1周后）
**维护者：** 技术架构团队

