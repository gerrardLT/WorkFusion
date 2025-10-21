# 招投标AI提效系统 - 开发任务清单

**文档版本：** v1.0
**创建时间：** 2025年10月15日
**文档类型：** 项目管理与开发计划
**目标读者：** 项目经理、开发团队Leader、技术负责人

---

## 📋 文档说明

本文档提供招投标AI提效系统的详细开发任务规划，包含4个阶段共42个任务项。每个任务都明确标注：

- **【保留】** - 维护现有功能，不修改核心代码
- **【增强】** - 在现有功能上增加UI/交互，底层逻辑保持不变
- **【新增】** - 全新功能模块，作为独立模块添加

**核心原则：保护现有核心架构，模块化扩展，分阶段交付**

---

## 📊 进度跟踪说明

每个任务前都有复选框 `- [ ]`，完成后请手动修改为 `- [x]`：

- `- [ ]` 表示**未完成**
- `- [x]` 表示**已完成**

**当前总体进度：** 25/42 任务已完成（59.5%）

**阶段进度：**
- 阶段1（P0/P1）：12/12 已完成 🎉
- 阶段2（P2）：13/13 已完成 🎉
- 阶段3（P3）：0/12 已完成
- 阶段4（P3）：0/4 已完成

**首页核心功能优化进度（新增）：**
- ✅ 修复场景切换 - 使用真实API数据
- ✅ 移除硬编码会话列表 - 使用真实会话数据
- ✅ 实现Markdown渲染 - AI回复支持Markdown格式
- ✅ 实现会话搜索功能 - 根据标题过滤
- ✅ 实现会话重命名功能 - 双击或点击图标编辑
- ✅ 实现消息复制功能 - 一键复制AI回复
- ✅ 实现重新生成功能 - 重新生成AI答案
- ✅ 实现编辑消息功能 - 编辑已发送消息
- ✅ 实现删除消息功能 - 删除指定消息
- ✅ 检查所有组件 - 确保使用真实数据
- ❌ 文件上传进度条 - 暂时取消（当前通知机制可用）

---

## 目录

1. [任务总览](#1-任务总览)
2. [阶段1：核心交互优化（2个月）](#2-阶段1核心交互优化2个月)
3. [阶段2：信息流打通（3个月）](#3-阶段2信息流打通3个月)
4. [阶段3：决策智能化（4个月）](#4-阶段3决策智能化4个月)
5. [阶段4：协作与集成（长期）](#5-阶段4协作与集成长期)
6. [里程碑与交付物](#6-里程碑与交付物)
7. [资源需求](#7-资源需求)
8. [风险管理](#8-风险管理)
9. [核心技术架构保护原则](#9-核心技术架构保护原则)

---

## 1. 任务总览

### 1.1 任务统计

| 阶段 | 时间 | 任务组数 | 任务数 | 总工作量 | 优先级 |
|------|------|---------|--------|---------|--------|
| **阶段1** | 2个月 | 4 | 14 | 8周 | P0/P1 |
| **阶段2** | 3个月 | 4 | 12 | 12周 | P2 |
| **阶段3** | 4个月 | 4 | 12 | 16周 | P3 |
| **阶段4** | 长期 | 4 | 4 | 22周 | P3 |
| **总计** | 12个月+ | 16 | 42 | 58周 | - |

---

### 1.2 任务分类

| 类型 | 任务数 | 占比 | 说明 |
|------|--------|------|------|
| **【保留】** | 0 | 0% | 无需修改现有核心功能 |
| **【增强】** | 18 | 43% | 在现有基础上增强UI/交互 |
| **【新增】** | 24 | 57% | 全新功能模块开发 |

---

### 1.3 优先级分布

```
P0 (立即实现)    ████████░░ 35%
P1 (3个月内)     ███████░░░ 30%
P2 (6个月内)     ████░░░░░░ 20%
P3 (长期规划)    ███░░░░░░░ 15%
```

---

## 2. 阶段1：核心交互优化（2个月）

**目标：** 将"智能问答工具"升级为"智能辅助工作台"，提升标书制作员的工作效率

**实现度：** 从27% → 50%

**核心交付：** MVP版本，包含Checklist、风险高亮、知识库管理、内容生成

---

### 2.1 任务组1.1：自动生成响应清单【增强】

**目标：** 文档解析完成后，自动生成结构化的任务清单（Checklist）

**优先级：** P0

**总工作量：** 4周

---

#### - [x] **T1.1.1 后端：基于现有Pipeline，新增信息提取API**

**类型：** 【增强】
**工作量：** 2周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建API端点：`POST /api/v2/documents/{id}/checklist`
- 调用现有的`QuestionsProcessor`，不修改核心RAG逻辑
- 通过问答方式提取关键任务项：
  - "请列出本招标文件中需要提供的所有资质文件"
  - "请列出本招标文件中需要响应的技术参数"
  - "请列出本招标文件中的关键时间节点"
- 解析LLM返回的列表，生成结构化JSON

**技术方案：**
```python
# backend/api/checklist.py 【新增文件】
from fastapi import APIRouter, HTTPException
from backend.services.checklist_service import ChecklistService

router = APIRouter(prefix="/documents", tags=["checklist"])

@router.post("/{document_id}/checklist")
async def generate_checklist(document_id: str):
    service = ChecklistService()
    # 调用现有的QuestionsProcessor
    checklist = await service.generate(document_id)
    return checklist
```

**验收标准：**
- API响应时间 < 30秒
- 返回至少10个任务项
- 任务项准确率 > 90%
- 包含任务描述、优先级、截止日期

**风险：**
- LLM返回格式不稳定 → 多次重试 + 格式校验

---

#### - [x] **T1.1.2 前端：Checklist组件开发**

**类型：** 【增强】
**工作量：** 1周
**负责人：** 前端开发工程师
**依赖：** T1.1.1

**详细描述：**
- 新建组件：`components/checklist/checklist-panel.tsx`
- 实现功能：
  - 任务列表展示（可折叠分组）
  - 任务勾选（完成/未完成）
  - 任务展开（显示详情、备注）
  - 任务指派（下拉选择团队成员）
  - 添加新任务（点击展开输入框）
  - 任务拖拽排序

**技术方案：**
```typescript
// components/checklist/checklist-panel.tsx 【新增文件】
import { Task } from '@/types/task';

interface ChecklistPanelProps {
  documentId: string;
  tasks: Task[];
  onTaskUpdate: (taskId: string, updates: Partial<Task>) => void;
}

export function ChecklistPanel({ documentId, tasks, onTaskUpdate }: ChecklistPanelProps) {
  // 组件实现
  return (
    <div className="checklist-panel">
      {/* 任务列表 */}
    </div>
  );
}
```

**验收标准：**
- 支持勾选完成任务
- 支持任务分组（资质、技术、商务）
- 支持任务搜索和过滤
- 响应式设计（移动端友好）

---

#### - [x] **T1.1.3 集成：文档解析后自动调用**

**类型：** 【增强】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** T1.1.1, T1.1.2

**详细描述：**
- 修改：`backend/api/upload.py` 添加回调逻辑
- 文档解析完成后，自动触发Checklist生成
- 使用异步任务（Celery或FastAPI BackgroundTasks）
- 前端轮询或WebSocket实时更新

**技术方案：**
```python
# backend/api/upload.py 【修改现有文件】
from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    # 现有上传逻辑【保留】
    doc = await document_service.create(file)

    # 解析文档【保留】
    await pipeline.process(doc.id)

    # 【新增】异步生成Checklist
    background_tasks.add_task(
        checklist_service.generate,
        doc.id
    )

    return doc
```

**验收标准：**
- 解析完成后30秒内生成Checklist
- 前端能实时看到Checklist更新
- 不影响文档解析的核心流程

---

### 2.2 任务组1.2：风险条款高亮【增强】

**目标：** 自动识别招标文件中的风险条款并高亮显示

**优先级：** P0

**总工作量：** 3周

---

#### - [x] **T1.2.1 后端：基于现有问答能力的风险识别**

**类型：** 【增强】
**工作量：** 1.5周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建服务：`backend/services/risk_service.py`
- 调用现有的`QuestionsProcessor`，不修改核心RAG逻辑
- 通过多轮问答识别不同类型风险：
  - "请识别本招标文件中可能导致废标的条款"
  - "请识别本招标文件中对投标方不利的条款"
  - "请识别本招标文件中的无限责任条款"
- 提取页码和位置信息
- 分类风险等级（高/中/低）

**技术方案：**
```python
# backend/services/risk_service.py 【新增文件】
from src.questions_processing import QuestionsProcessor

class RiskService:
    def __init__(self):
        self.qa = QuestionsProcessor()

    async def detect_risks(self, document_id: str) -> List[Risk]:
        risks = []

        # 识别废标条款（高风险）
        answer = await self.qa.ask(
            "请列出本文档中所有可能导致废标的条款，并标注页码",
            document_id
        )
        risks.extend(self._parse_risks(answer, level='high'))

        # 识别不利条款（中风险）
        answer = await self.qa.ask(
            "请列出本文档中对投标方不利的条款，并标注页码",
            document_id
        )
        risks.extend(self._parse_risks(answer, level='medium'))

        return risks
```

**验收标准：**
- 识别至少3类风险（废标、无限责任、苛刻条款）
- 风险识别准确率 > 85%
- 每个风险包含：类型、等级、位置、描述、建议

---

#### - [x] **T1.2.2 前端：文档预览高亮功能**

**类型：** 【增强】
**工作量：** 1周
**负责人：** 前端开发工程师
**依赖：** T1.2.1

**详细描述：**
- 新建组件：`components/document/document-viewer.tsx`
- 使用PDF.js渲染PDF
- 在PDF上叠加高亮层（SVG/Canvas）
- 支持点击高亮查看风险详情
- 支持过滤显示（只看高风险/中风险）

**技术方案：**
```typescript
// components/document/document-viewer.tsx 【新增文件】
import { Document, Page } from 'react-pdf';
import { Risk } from '@/types/risk';

interface DocumentViewerProps {
  fileUrl: string;
  risks: Risk[];
  onRiskClick: (risk: Risk) => void;
}

export function DocumentViewer({ fileUrl, risks, onRiskClick }: DocumentViewerProps) {
  return (
    <div className="relative">
      <Document file={fileUrl}>
        {/* PDF渲染 */}
      </Document>

      {/* 高亮层 */}
      <svg className="absolute inset-0 pointer-events-none">
        {risks.map(risk => (
          <rect
            key={risk.id}
            x={risk.location.x}
            y={risk.location.y}
            width={risk.location.width}
            height={risk.location.height}
            fill={risk.level === 'high' ? 'red' : 'yellow'}
            opacity={0.3}
            className="pointer-events-auto cursor-pointer"
            onClick={() => onRiskClick(risk)}
          />
        ))}
      </svg>
    </div>
  );
}
```

**验收标准：**
- PDF正常显示，支持缩放
- 高亮准确标注在对应位置
- 点击高亮弹出风险详情
- 颜色区分风险等级（红/黄/绿）

---

#### - [x] **T1.2.3 测试：风险识别准确率验证**

**类型：** 【增强】
**工作量：** 0.5周
**负责人：** 测试工程师
**依赖：** T1.2.1, T1.2.2

**详细描述：**
- 准备10份真实招标文件
- 人工标注所有风险条款（Ground Truth）
- 运行系统自动识别
- 计算准确率、召回率、F1分数
- 分析误识别和漏识别案例

**验收标准：**
- 准确率 > 85%
- 召回率 > 80%
- 误识别率 < 10%

---

### 2.3 任务组1.3：知识库可视化管理【新增】

**目标：** 提供知识库管理界面，支持分类、搜索、标签

**优先级：** P1

**总工作量：** 4周

---

#### - [x] **T1.3.1 后端：知识库分类API**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建API：`backend/api/knowledge.py`
- 新建服务：`backend/services/knowledge_service.py`
- 新建数据表：`knowledge_items`
- 实现CRUD接口：
  - `GET /api/v2/knowledge?category=qualifications`
  - `POST /api/v2/knowledge`
  - `PUT /api/v2/knowledge/{id}`
  - `DELETE /api/v2/knowledge/{id}`
  - `GET /api/v2/knowledge/search?q=关键词`

**数据模型：**
```python
# backend/models/knowledge.py 【新增文件】
from sqlalchemy import Column, String, JSON, Date
from backend.models.base import Base

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(String(50), primary_key=True)
    category = Column(String(50), nullable=False)  # 资质/业绩/方案/人员
    doc_id = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    tags = Column(JSON)
    expire_date = Column(Date)  # 资质到期日期
    metadata = Column(JSON)
```

**验收标准：**
- 支持4类分类（资质、业绩、方案、人员）
- 搜索响应时间 < 1秒
- 支持多标签过滤

---

#### - [x] **T1.3.2 前端：知识库管理界面**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 前端开发工程师
**依赖：** T1.3.1

**详细描述：**
- 新建页面：`app/knowledge/page.tsx`
- 实现功能：
  - 分类Tab切换（资质/业绩/方案/人员）
  - 列表展示（卡片模式/表格模式）
  - 搜索和过滤（关键词、标签、日期）
  - 文件上传（拖拽上传）
  - 详情查看、编辑、删除
  - 资质到期提醒（即将到期变黄，已过期变红）

**页面布局：**
```
┌─────────────────────────────────────────────────┐
│  顶部导航栏                                      │
├─────────────────────────────────────────────────┤
│  [Tab] 资质证照 | 历史业绩 | 技术方案 | 人员档案 │
├──────────────┬──────────────────────────────────┤
│  左侧过滤     │  右侧列表                         │
│              │                                  │
│  [搜索框]     │  [视图切换] 卡片 | 列表           │
│  [标签过滤]   │                                  │
│  [日期过滤]   │  [知识卡片1]                     │
│              │  [知识卡片2]                     │
│              │  [知识卡片3]                     │
│              │  ...                             │
│              │  [分页控制]                      │
└──────────────┴──────────────────────────────────┘
```

**验收标准：**
- 支持卡片和列表两种视图
- 搜索实时过滤
- 拖拽上传文件
- 即将到期资质有明显提示

---

#### - [x] **T1.3.3 功能：文档标签、搜索、过滤**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 全栈开发工程师
**依赖：** T1.3.1, T1.3.2

**详细描述：**
- 复用现有的检索能力（BM25 + 向量）
- 实现标签系统：
  - 预设标签（电力设备、资质认证、项目业绩等）
  - 自定义标签
  - 标签自动推荐（基于文档内容）
- 实现多维度过滤：
  - 按分类过滤
  - 按标签过滤（多选）
  - 按日期范围过滤
  - 组合过滤

**技术方案：**
- 后端：使用SQLAlchemy的`filter()`和`join()`
- 前端：使用Zustand管理过滤状态

**验收标准：**
- 搜索能匹配标题、描述、标签
- 过滤响应时间 < 500ms
- 支持过滤条件组合

---

### 2.4 任务组1.4：内容一键生成【增强】

**目标：** 提供"一键生成"按钮，自动生成标书章节初稿

**优先级：** P1

**总工作量：** 2周

---

#### - [x] **T1.4.1 后端：基于现有LLM调用的内容生成API**

**类型：** 【增强】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建API端点：`POST /api/v2/generate/content`
- 复用现有的`DashScopeClient`
- 支持多种内容生成类型：
  - 公司简介
  - 技术方案
  - 服务承诺
  - 质量保证措施
  - 安全生产措施
- 基于知识库内容生成（自动检索相关信息）

**技术方案：**
```python
# backend/api/generate.py 【新增文件】
from backend.services.content_service import ContentService

@router.post("/generate/content")
async def generate_content(request: ContentGenerationRequest):
    service = ContentService()

    # 1. 检索相关知识库内容
    context = await service.retrieve_context(request.type, request.project_id)

    # 2. 构建提示词
    prompt = service.build_prompt(request.type, context)

    # 3. 调用LLM生成
    content = await service.llm.generate_text(prompt)

    return {"content": content}
```

**验收标准：**
- 生成响应时间 < 10秒
- 生成内容逻辑通顺、符合要求
- 支持重新生成

---

#### - [x] **T1.4.2 前端："生成初稿"按钮集成**

**类型：** 【增强】
**工作量：** 0.5周
**负责人：** 前端开发工程师
**依赖：** T1.4.1

**详细描述：**
- 修改：`components/chat/input-area.tsx` 添加按钮组
- 在输入框上方添加"生成内容"按钮组
- 点击按钮后：
  - 显示加载状态
  - 调用生成API
  - 在消息气泡中显示生成结果
  - 提供"复制"、"编辑"、"重新生成"按钮

**UI设计：**
```
┌────────────────────────────────────────┐
│  [生成公司简介] [生成技术方案]          │
│  [生成服务承诺] [生成质量保证措施]      │
├────────────────────────────────────────┤
│  [输入框]                               │
│  输入您的问题...                        │
└────────────────────────────────────────┘
```

**验收标准：**
- 按钮布局美观，易于点击
- 生成中有明显的加载提示
- 生成结果支持Markdown渲染

---

#### - [x] **T1.4.3 优化：生成质量调优**

**类型：** 【增强】
**工作量：** 0.5周
**负责人：** AI工程师
**依赖：** T1.4.1, T1.4.2

**详细描述：**
- 优化提示词模板（Prompt Engineering）
- 添加Few-shot示例
- 调整LLM参数（temperature、top_p）
- A/B测试不同模型（qwen-turbo vs qwen-plus）
- 收集用户反馈，持续优化

**优化目标：**
- 生成内容相关性 > 90%
- 生成内容完整性 > 95%
- 用户满意度 > 85%

---

## 3. 阶段2：信息流打通（3个月）

**目标：** 实现"商机发现 → 文档解析 → 标书制作"的完整流程

**实现度：** 从50% → 70%

**核心交付：** Beta版本，包含爬虫、推荐、项目管理、评估报告

---

### 3.1 任务组2.1：招标信息爬虫【新增】

**目标：** 自动搜集全网招标信息

**优先级：** P2

**总工作量：** 7周

---

#### - [x] **T2.1.1 爬虫框架搭建（Scrapy）**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建目录：`backend/crawler/`
- 搭建Scrapy项目
- 实现基础组件：
  - Spiders（爬虫）
  - Pipelines（数据处理）
  - Middlewares（中间件）
  - Settings（配置）
- 实现反爬措施：
  - 随机User-Agent
  - 代理IP池
  - 请求限速
  - 模拟浏览器（Selenium）

**目录结构：**
```
backend/crawler/
├── spiders/
│   ├── __init__.py
│   ├── tender_spider.py
│   └── ...
├── pipelines.py
├── middlewares.py
├── settings.py
└── items.py
```

**验收标准：**
- Scrapy项目可正常运行
- 反爬措施有效（不被封禁）
- 支持分布式爬取（Scrapy-Redis）

---

#### - [x] **T2.1.2 对接2-3个招标平台**

**类型：** 【新增】
**工作量：** 3周
**负责人：** 爬虫工程师
**依赖：** T2.1.1

**详细描述：**
- 平台1：某省公共资源交易中心（静态页面）
- 平台2：某地区招标网（动态加载）
- 平台3：某行业招标平台（需登录）
- 每个平台实现：
  - 列表页爬取
  - 详情页爬取
  - 数据字段提取（标题、金额、地域、截止日期等）
  - 增量更新（只爬新项目）

**技术难点：**
- 动态加载页面 → Selenium + Chrome Headless
- 需登录平台 → Cookie管理 + 定期刷新登录
- 反爬虫机制 → 代理IP + 限速 + 模拟人工操作

**验收标准：**
- 每个平台爬取成功率 > 90%
- 每日爬取量 > 100个项目
- 数据完整性 > 95%

---

#### - [x] **T2.1.3 数据清洗与存储**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** T2.1.2

**详细描述：**
- 实现数据清洗Pipeline
- 数据规范化：
  - 金额格式统一（万元、元）
  - 日期格式统一（ISO 8601）
  - 地域标准化（省/市/区）
- 去重：
  - 同一平台去重（URL）
  - 跨平台去重（标题+金额相似度）
- 存储到数据库（projects表）
- 原始数据备份（JSON文件）

**验收标准：**
- 去重准确率 > 95%
- 数据格式统一
- 存储失败率 < 1%

---

#### - [x] **T2.1.4 定时任务与监控**

**类型：** 【新增】
**工作量：** 1周
**负责人：** DevOps工程师
**依赖：** T2.1.1, T2.1.2, T2.1.3

**详细描述：**
- 使用APScheduler实现定时任务
- 爬取策略：
  - 每日凌晨2点全量爬取
  - 每隔2小时增量爬取
- 监控指标：
  - 爬取成功率
  - 爬取数量
  - 错误率
  - 响应时间
- 告警机制：
  - 爬取失败 > 5次 → 邮件告警
  - 爬取数量异常 → 钉钉告警

**验收标准：**
- 定时任务稳定运行
- 监控数据实时更新
- 告警及时准确

---

### 3.2 任务组2.2：企业画像系统【新增】

**目标：** 构建企业能力画像，用于项目匹配

**优先级：** P2

**总工作量：** 5周

---

#### - [x] **T2.2.1 数据模型设计**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** 无

**详细描述：**
- 新建表：`companies`
- 设计企业画像数据结构：
  - 基本信息（名称、规模、成立年份）
  - 资质列表（JSON数组）
  - 能力描述（擅长领域、技术优势）
  - 历史业绩（项目数量、金额范围）
  - 目标市场（区域、行业、预算范围）

**数据模型：**
```python
# backend/models/company.py 【新增文件】
class Company(Base):
    __tablename__ = "companies"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    qualifications = Column(JSON)  # [{"name": "电力施工", "level": "二级"}]
    capabilities = Column(JSON)    # {"fields": ["输变电", "配电"], "advantages": []}
    target_areas = Column(JSON)    # ["广东", "江苏"]
    target_industries = Column(JSON)
    budget_range = Column(JSON)    # {"min": 1000000, "max": 50000000}
```

**验收标准：**
- 数据模型设计合理
- 支持灵活查询
- 可扩展性强

---

#### - [x] **T2.2.2 前端：企业信息录入页面**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 前端开发工程师
**依赖：** T2.2.1

**详细描述：**
- 新建页面：`app/company/page.tsx` ✅
- 实现多步骤表单： ✅
  - Step 1: 基本信息 (`components/company/basic-info-step.tsx`)
  - Step 2: 资质管理（可添加多个）(`components/company/qualifications-step.tsx`)
  - Step 3: 能力描述（多选 + 自定义）(`components/company/capabilities-step.tsx`)
  - Step 4: 目标市场（区域选择 + 预算范围）(`components/company/target-market-step.tsx`)
- 实现表单验证 ✅
- 支持保存草稿和最终提交 ✅

**页面布局：**
```
┌────────────────────────────────────────┐
│  企业画像设置                           │
├────────────────────────────────────────┤
│  [Step 1] ━━━ [Step 2] ━━━ [Step 3] ━━ [Step 4] │
├────────────────────────────────────────┤
│                                        │
│  [表单内容]                             │
│                                        │
│  [上一步]           [保存草稿] [下一步] │
└────────────────────────────────────────┘
```

**验收标准：**
- ✅ 多步骤表单流畅
- ✅ 表单验证准确
- ✅ 支持保存和恢复

**完成文件：**
- `frontend-next/app/company/page.tsx` - 主页面
- `frontend-next/components/company/basic-info-step.tsx` - Step 1组件
- `frontend-next/components/company/qualifications-step.tsx` - Step 2组件
- `frontend-next/components/company/capabilities-step.tsx` - Step 3组件
- `frontend-next/components/company/target-market-step.tsx` - Step 4组件
- `frontend-next/types/company.ts` - 类型定义
- `frontend-next/lib/api-v2.ts` - API集成（Company相关接口）

---

#### - [x] **T2.2.3 后端：画像匹配算法**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 算法工程师
**依赖：** T2.2.1

**详细描述：**
- 新建服务：`backend/services/recommendation_service.py`
- 实现匹配算法（规则版）：
  - 资质匹配（必要条件）
  - 业绩匹配（历史业绩与项目规模）
  - 地域匹配（目标区域与项目地点）
  - 预算匹配（预算范围与项目金额）
- 计算综合匹配度（0-100分）
- 可选：使用BM25复用现有检索能力

**匹配算法：**
```python
# backend/services/recommendation_service.py 【新增文件】
class RecommendationService:
    def calculate_match_score(self, project: Project, company: Company) -> float:
        scores = []

        # 1. 资质匹配（40%）
        qualification_score = self._match_qualifications(project, company)
        scores.append(qualification_score * 0.4)

        # 2. 业绩匹配（30%）
        achievement_score = self._match_achievements(project, company)
        scores.append(achievement_score * 0.3)

        # 3. 地域匹配（20%）
        location_score = self._match_location(project, company)
        scores.append(location_score * 0.2)

        # 4. 预算匹配（10%）
        budget_score = self._match_budget(project, company)
        scores.append(budget_score * 0.1)

        return sum(scores)
```

**验收标准：**
- 匹配度计算准确
- 推荐结果符合预期
- 响应时间 < 1秒

---

### 3.3 任务组2.3：项目推荐引擎【新增】

**目标：** 根据企业画像推荐高匹配度项目

**优先级：** P2

**总工作量：** 4周

---

#### - [x] **T2.3.1 推荐算法（关键词 + 规则）**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 算法工程师
**依赖：** T2.2.3

**详细描述：**
- 基于T2.2.3的匹配算法
- 实现批量推荐：
  - 遍历所有新项目
  - 计算匹配度
  - 过滤低匹配度项目（< 60分）
  - 按匹配度排序
  - 返回Top 10
- 可复用现有的BM25检索能力（关键词匹配）

**推荐流程：**
```
新项目入库
    ↓
提取项目特征
    ↓
与企业画像匹配
    ↓
计算匹配度
    ↓
匹配度 > 70分?
    ↓ 是
推送到Dashboard
```

**验收标准：**
- 推荐准确率 > 80%
- 批量处理时间 < 5秒/100个项目
- 支持个性化推荐

---

#### - [x] **T2.3.2 推荐列表UI**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 前端开发工程师
**依赖：** T2.3.1

**详细描述：**
- 新建页面：`app/projects/page.tsx` ✅
- 实现项目列表： ✅
  - 表格视图（默认）- `components/projects/project-table-view.tsx`
  - 卡片视图（可选）- `components/projects/project-card-view.tsx`
  - 筛选器（匹配度、金额、地域、截止日期）- `components/projects/project-filters.tsx`
  - 排序（匹配度、金额、时间）- 集成在筛选器中
  - 收藏/忽略操作 - 集成在表格和卡片视图中
- 项目详情：⏳（待实现详情页）
  - 点击跳转到详情页
  - 显示完整信息
  - "快速评估"按钮

**验收标准：**
- ✅ 列表加载时间 < 1秒
- ✅ 支持分页（每页20条）
- ✅ 筛选和排序实时响应

**完成文件：**
- `frontend-next/app/projects/page.tsx` - 主页面
- `frontend-next/components/projects/project-table-view.tsx` - 表格视图
- `frontend-next/components/projects/project-card-view.tsx` - 卡片视图
- `frontend-next/components/projects/project-filters.tsx` - 筛选器组件
- `frontend-next/types/project.ts` - 类型定义
- `frontend-next/lib/api-v2.ts` - API集成（推荐相关接口）

---

#### - [x] **T2.3.3 订阅与通知功能**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 全栈开发工程师
**依赖：** T2.3.1

**详细描述：**
- 实现订阅机制：✅
  - 用户设置订阅规则（关键词、地域、金额）
  - 新项目匹配订阅规则时自动推送
- 通知方式：✅
  - 系统通知（Dashboard右上角铃铛图标）
  - 邮件通知（可选，已取消）
  - 钉钉/企业微信通知（可选，待后续实现）
- 通知管理：✅
  - 查看历史通知
  - 标记已读/归档
  - 删除通知

**验收标准：**
- ✅ 订阅规则准确匹配
- ✅ 通知系统可管理
- ✅ 单元测试覆盖

**完成文件：**
- `backend/models/subscription.py` - 订阅数据模型
- `backend/models/notification.py` - 通知数据模型
- `backend/services/subscription_service.py` - 订阅服务
- `backend/services/notification_service.py` - 通知服务
- `backend/api/subscription.py` - 订阅API
- `backend/api/notification.py` - 通知API
- `frontend-next/app/subscriptions/page.tsx` - 订阅管理UI
- `frontend-next/app/notifications/page.tsx` - 通知中心UI
- `frontend-next/types/subscription.ts` - 订阅类型定义
- `frontend-next/types/notification.ts` - 通知类型定义
- `backend/tests/test_subscription_service.py` - 订阅服务单元测试
- `backend/tests/test_notification_service.py` - 通知服务单元测试

---

### 3.4 任务组2.4：项目评估自动化【新增】

**目标：** 一键生成项目评估报告PDF

**优先级：** P2

**总工作量：** 4周

---

#### - [x] **T2.4.1 评估报告模板设计 + 前端UI**

**类型：** 【新增 + 增强】
**工作量：** 1周
**负责人：** 产品经理 + 设计师 + 前端开发工程师
**依赖：** T2.4.2, T2.4.3

**详细描述：**
- 设计评估报告结构： ✅
  1. 项目概况摘要
  2. 核心资质要求对比（✓符合 / ✗不符合）
  3. 关键时间节点表
  4. 历史类似项目中标情况分析
  5. 风险点提示
  6. 综合评估结论和建议
- 设计报告样式（PDF排版） ✅
- 提供Word/PDF模板 ✅（后端已实现PDF导出）
- **前端实现：** ✅
  - 评估报告列表页面 (`app/evaluations/page.tsx`)
  - 评估报告详情页面 (`app/evaluations/[reportId]/page.tsx`)
  - 项目列表中添加"快速评估"按钮
  - PDF下载功能

**验收标准：**
- ✅ 报告结构合理
- ✅ 样式专业美观
- ✅ 内容完整全面
- ✅ 前端展示美观
- ✅ PDF下载功能正常

**完成文件：**
- `frontend-next/app/evaluations/page.tsx` - 报告列表页
- `frontend-next/app/evaluations/[reportId]/page.tsx` - 报告详情页
- `frontend-next/types/evaluation.ts` - 类型定义
- `frontend-next/lib/api-v2.ts` - API集成（评估报告接口）
- `frontend-next/components/projects/project-table-view.tsx` - 添加快速评估按钮
- `frontend-next/components/projects/project-card-view.tsx` - 添加快速评估按钮

---

#### - [x] **T2.4.2 自动生成报告API**

**类型：** 【新增】
**工作量：** 2周
**负责人：** 后端开发工程师
**依赖：** T2.4.1

**详细描述：**
- 新建API：`backend/api/evaluation.py`
- 新建服务：`backend/services/evaluation_service.py`
- 实现报告生成逻辑：
  - 调用现有问答能力提取信息
  - 比对企业资质
  - 查询历史中标数据
  - 调用风险识别服务
  - 汇总生成报告数据
- 存储报告数据（`evaluation_reports`表）

**技术方案：**
```python
# backend/services/evaluation_service.py 【新增文件】
class EvaluationService:
    async def generate_report(self, project_id: str, company_id: str) -> Report:
        # 1. 提取项目信息（复用问答能力）
        project_info = await self.extract_project_info(project_id)

        # 2. 比对企业资质
        qualification_match = await self.match_qualifications(project_id, company_id)

        # 3. 分析历史中标数据
        historical_analysis = await self.analyze_historical_data(project_info)

        # 4. 识别风险
        risks = await self.risk_service.detect_risks(project_id)

        # 5. 生成综合结论
        conclusion = await self.generate_conclusion(
            qualification_match,
            historical_analysis,
            risks
        )

        # 6. 汇总报告
        report = Report(
            project_info=project_info,
            qualification_match=qualification_match,
            historical_analysis=historical_analysis,
            risks=risks,
            conclusion=conclusion
        )

        return report
```

**验收标准：**
- 报告生成时间 < 1分钟
- 报告数据准确完整
- 支持自定义模板

---

#### - [x] **T2.4.3 PDF导出功能**

**类型：** 【新增】
**工作量：** 1周
**负责人：** 后端开发工程师
**依赖：** T2.4.2

**详细描述：**
- 使用ReportLab或WeasyPrint生成PDF
- 支持自定义模板（HTML → PDF）
- 实现水印、页眉页脚
- 支持图表嵌入
- 支持中文字体

**技术方案：**
```python
# backend/services/pdf_generator.py 【新增文件】
from weasyprint import HTML

class PDFGenerator:
    def generate(self, report: Report, template: str = "default") -> bytes:
        # 1. 渲染HTML模板
        html = self.render_template(template, report)

        # 2. 转换为PDF
        pdf_bytes = HTML(string=html).write_pdf()

        return pdf_bytes
```

**验收标准：**
- PDF正常生成
- 中文显示正常
- 样式符合模板设计

---

## 4. 阶段3：决策智能化（4个月）

**目标：** 提供数据驱动的投标决策支持

**实现度：** 从70% → 85%

**核心交付：** V1.0版本，包含中标预测、报价建议、竞争分析、数据看板

**优先级：** P3

**说明：** 此阶段为高级功能，需要大量历史数据和机器学习模型训练，属于长期规划。

---

### 4.1 任务组3.1：中标概率预测【新增】

**总工作量：** 12周

*(由于篇幅限制，此部分仅列出任务概要，详细任务描述略)*

- [ ] **T3.1.1** 历史数据采集（3周）
- [ ] **T3.1.2** 特征工程（4周）
- [ ] **T3.1.3** 模型训练（3周）
- [ ] **T3.1.4** 预测API与UI（2周）

---

### 4.2 任务组3.2：报价策略建议【新增】

**总工作量：** 5周

- [ ] **T3.2.1** 报价数据分析（2周）
- [ ] **T3.2.2** 规则引擎开发（2周）
- [ ] **T3.2.3** 报价建议UI（1周）

---

### 4.3 任务组3.3：竞争对手画像【新增】

**总工作量：** 5周

- [ ] **T3.3.1** 数据采集与存储（2周）
- [ ] **T3.3.2** 画像生成算法（2周）
- [ ] **T3.3.3** 可视化展示（1周）

---

### 4.4 任务组3.4：数据看板【新增】

**总工作量：** 3周

- [ ] **T3.4.1** 数据统计API（1周）
- [ ] **T3.4.2** 可视化图表开发（2周）

---

## 5. 阶段4：协作与集成（长期）

**目标：** 打造完整的团队协作平台

**优先级：** P3

**总工作量：** 22周

*(此阶段为长期规划，任务列表略)*

- [ ] **T4.1** 在线编辑器集成（6周）
- [ ] **T4.2** 多人协作功能（4周）
- [ ] **T4.3** ERP/CRM集成（4周）
- [ ] **T4.4** 移动端App（8周）

---

## 6. 里程碑与交付物

### 6.1 里程碑规划

| 里程碑 | 时间 | 核心交付 | 验收标准 |
|--------|------|---------|---------|
| **M1: MVP发布** | 2个月 | Checklist、风险高亮、知识库、内容生成 | - 功能可用<br>- 用户满意度 > 80% |
| **M2: Beta发布** | 5个月 | 爬虫、推荐、项目管理、评估报告 | - 功能稳定<br>- Bug < 10个/月 |
| **M3: V1.0发布** | 9个月 | 中标预测、报价建议、竞争分析 | - 预测准确率 > 70%<br>- 用户留存率 > 60% |
| **M4: 企业版** | 12个月+ | 编辑器、协作、集成、移动端 | - 企业客户 > 10家<br>- ARR > 100万 |

---

### 6.2 交付物清单

#### **M1 (MVP)**
- [ ] 后端API文档
- [ ] 前端用户手册
- [ ] 部署文档
- [ ] 测试报告
- [ ] 演示视频

#### **M2 (Beta)**
- [ ] 完整功能文档
- [ ] 爬虫配置手册
- [ ] 推荐算法说明
- [ ] 性能测试报告
- [ ] 用户反馈报告

#### **M3 (V1.0)**
- [ ] 模型训练文档
- [ ] 预测算法白皮书
- [ ] 数据分析报告
- [ ] 商业化方案
- [ ] 市场推广资料

---

## 7. 资源需求

### 7.1 人员需求

| 角色 | 人数 | 投入 | 职责 |
|------|------|------|------|
| **产品经理** | 1 | 全职 | 需求管理、项目协调 |
| **前端开发** | 2 | 全职 | React/Next.js开发 |
| **后端开发** | 2 | 全职 | Python/FastAPI开发 |
| **算法工程师** | 1 | 全职 | AI能力开发、模型训练 |
| **测试工程师** | 1 | 全职 | 功能测试、性能测试 |
| **UI/UX设计师** | 1 | 兼职 | 界面设计、交互设计 |
| **DevOps工程师** | 1 | 兼职 | 部署、运维、监控 |

**总计：** 7人（6全职 + 2兼职）

---

### 7.2 预算需求（估算）

| 项目 | 金额（人民币/年） | 说明 |
|------|------------------|------|
| **人力成本** | 150万 | 7人团队 |
| **服务器/云服务** | 10万 | 阿里云/腾讯云 |
| **API调用费用** | 5万 | DashScope API |
| **第三方服务** | 3万 | OSS、CDN等 |
| **办公设备** | 5万 | 开发电脑、服务器 |
| **其他** | 7万 | 市场推广、培训等 |
| **总计** | 180万 | 年度预算 |

---

### 7.3 技术资源

| 资源类型 | 配置 | 用途 |
|---------|------|------|
| **开发服务器** | 16核 32GB 500GB SSD | 后端开发测试 |
| **数据库服务器** | 8核 16GB 1TB SSD | PostgreSQL |
| **爬虫服务器** | 8核 16GB | Scrapy分布式爬虫 |
| **GPU服务器（可选）** | V100 16GB | MinerU OCR加速 |
| **对象存储** | 1TB | 文件存储 |
| **CDN** | 100GB/月 | 静态资源加速 |

---

## 8. 风险管理

### 8.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 | 应急方案 |
|------|------|------|----------|----------|
| **爬虫反爬** | 高 | 高 | - 代理IP池<br>- 限速<br>- 模拟人工 | - 人工采集<br>- API对接 |
| **API限流** | 中 | 中 | - 多账号<br>- 请求队列<br>- 缓存 | - 切换备用API<br>- 本地模型 |
| **性能瓶颈** | 中 | 高 | - 缓存<br>- 异步处理<br>- 负载均衡 | - 限流<br>- 降级 |
| **数据安全** | 低 | 高 | - 加密<br>- 权限控制<br>- 审计 | - 数据备份<br>- 应急响应 |
| **模型准确率低** | 中 | 中 | - 持续优化<br>- A/B测试<br>- 用户反馈 | - 人工审核<br>- 规则补充 |

---

### 8.2 项目风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **需求变更** | 中 | 中 | - 敏捷开发<br>- 定期评审<br>- 需求冻结期 |
| **人员流失** | 低 | 高 | - 知识沉淀<br>- 代码规范<br>- 文档完善 |
| **进度延期** | 中 | 中 | - 缓冲时间<br>- 里程碑管理<br>- 定期沟通 |
| **预算超支** | 低 | 中 | - 成本控制<br>- 分期投入<br>- 优先级管理 |

---

### 8.3 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **市场需求不足** | 低 | 高 | - 用户调研<br>- MVP验证<br>- 快速迭代 |
| **竞品压力** | 中 | 中 | - 技术壁垒<br>- 用户体验<br>- 差异化功能 |
| **政策法规变化** | 低 | 中 | - 合规设计<br>- 灵活架构<br>- 及时调整 |

---

## 9. 核心技术架构保护原则

### 9.1 绝对不修改的核心模块

**以下模块在所有阶段都不得修改：**

```
src/
├── pipeline.py              【保留】RAG主流程
├── questions_processing.py  【保留】问答处理器
├── ingestion.py            【保留】文档摄取
├── pdf_parsing_mineru.py   【保留】PDF解析
├── dashscope_client.py     【保留】DashScope客户端
├── retrieval/              【保留】检索组件
│   ├── hybrid_retriever.py
│   ├── bm25_retriever.py
│   ├── vector_retriever.py
│   └── layered_navigator.py
├── agents/                 【保留】智能Agent
│   └── routing_agent.py
├── cache/                  【保留】缓存系统
│   └── smart_cache.py
└── verification/           【保留】验证系统
    └── answer_verifier.py
```

**数据库表：**
- `scenarios`
- `documents`
- `chat_sessions`
- `chat_messages`
- `document_types`

---

### 9.2 可扩展的方式

**1. 新建独立服务类**
```python
# backend/services/new_service.py 【新增】
from src.questions_processing import QuestionsProcessor

class NewService:
    def __init__(self):
        self.qa = QuestionsProcessor()  # 复用现有能力
```

**2. 新建独立API路由**
```python
# backend/api/new_api.py 【新增】
from fastapi import APIRouter

router = APIRouter(prefix="/new", tags=["new"])
```

**3. 新建独立数据表**
```sql
-- 新表通过外键关联现有表
CREATE TABLE new_table (
    id VARCHAR(50) PRIMARY KEY,
    doc_id VARCHAR(50),
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);
```

---

### 9.3 增强的方式

**1. UI组件增强**
```typescript
// 在现有组件中添加新按钮，不改变核心逻辑
<ChatInterface>
  {/* 【保留】现有输入框 */}
  <Textarea />

  {/* 【增强】新增按钮组 */}
  <ButtonGroup>
    <Button>生成内容</Button>
  </ButtonGroup>
</ChatInterface>
```

**2. API参数扩展**
```python
# 在现有API中添加可选参数，向后兼容
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    auto_checklist: bool = False  # 【增强】新增参数
):
    # 现有逻辑【保留】
    result = await process(file)

    # 新增逻辑【增强】
    if auto_checklist:
        await generate_checklist(result.id)

    return result
```

---

### 9.4 代码审查清单

**每次PR（Pull Request）前必须检查：**

- [ ] 是否修改了核心模块（src/目录下的【保留】文件）？
- [ ] 是否修改了现有数据库表结构？
- [ ] 新增代码是否作为独立模块？
- [ ] 是否有单元测试覆盖新功能？
- [ ] 是否更新了API文档？
- [ ] 是否进行了性能测试？
- [ ] 是否有代码审查（Code Review）？

---

## 10. 附录

### 10.1 任务看板（Kanban）

使用Jira/Trello管理任务，按以下状态分类：

- **待办（To Do）**
- **进行中（In Progress）**
- **待审查（In Review）**
- **测试中（Testing）**
- **已完成（Done）**

---

### 10.2 每周站会议程

**时间：** 每周一上午9:30
**时长：** 30分钟

**议程：**
1. 上周完成任务回顾（5分钟）
2. 本周任务计划（10分钟）
3. 遇到的问题和风险（10分钟）
4. 协调和支持需求（5分钟）

---

### 10.3 参考文档

- [功能交互设计文档](./招投标AI系统功能交互设计.md)
- [系统架构设计文档](./招投标AI系统架构设计.md)
- [招投标PRD与当前系统功能对比分析](./招投标PRD与当前系统功能对比分析.md)
- [中国电力行业招投标全流程AI提效工具PRD](./中国电力行业招投标全流程AI提效工具产品需求文档_(PRD).md)

---

**文档版本：** v1.0
**创建时间：** 2025年10月15日
**下次更新：** 每周一站会后更新进度
**维护者：** 项目管理办公室（PMO）

---

## 🎉 结语

本开发任务清单提供了完整的4阶段开发计划，共42个任务项，预计58周完成。

**核心原则：**
- ✅ **保护现有架构**：核心Agentic RAG架构完全不动
- ✅ **模块化扩展**：新功能作为独立模块添加
- ✅ **分阶段交付**：每2-3个月一个里程碑
- ✅ **用户价值优先**：先做高价值、低难度的功能（P0/P1）

**成功关键：**
1. 严格遵守架构保护原则
2. 持续的用户反馈和迭代
3. 团队高效协作和沟通
4. 技术债务及时偿还

让我们一起打造一个**功能强大、架构优雅、用户喜爱**的招投标AI提效系统！🚀

