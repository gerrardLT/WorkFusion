# 🚀 多场景AI知识问答系统 - Agentic RAG 架构设计

## 📋 文档说明

**编写时间**: 2025-09-30
**文档类型**: 架构设计与技术方案
**目标**: 将当前基于简单向量检索的RAG系统升级为 Agentic RAG 智能体架构
**适用场景**: 招投标、企业管理两大业务场景
**配套文档**: [Agentic_RAG重构任务清单.md](./Agentic_RAG重构任务清单.md)
**技术参考**: [Agentic_RAG完整实现指南.md](./Agentic_RAG完整实现指南.md)

---

## 🎯 重构目标与价值

### 当前系统痛点分析

| 痛点类型 | 当前问题 | 影响程度 | 业务场景 |
|---------|---------|---------|---------|
| **检索逻辑缺失** | `retrieve_relevant_context()` 直接返回空列表 | ❌ 致命 | 所有场景 |
| **无混合检索** | BM25 和 FAISS 索引已构建但未使用 | ❌ 严重 | 所有场景 |
| **长文档处理弱** | 招标文件133页，单纯分块效果差 | ⚠️ 中等 | 招投标场景 |
| **答案缺乏引用** | 无法定位答案来源的具体页码/段落 | ⚠️ 中等 | 所有场景 |
| **成本控制缺失** | 无缓存机制，重复查询浪费API成本 | ⚠️ 中等 | 所有场景 |
| **无答案验证** | LLM可能编造不存在的引用 | ⚠️ 中等 | 所有场景 |

### 升级后的核心价值

| 价值点 | 技术实现 | 业务收益 |
|-------|---------|---------|
| **智能检索** | 路由代理 + 分层导航 | 准确率从 0% → 85%+ |
| **混合检索** | BM25 + FAISS + 重排序 | 召回率从 0% → 90%+ |
| **长文档处理** | 分层分块 + 上下文扩展 | 支持500页以上文档 |
| **精准引用** | 答案验证 + 来源追溯 | 用户信任度提升 |
| **成本优化** | 语义缓存 + 分层策略 | API成本降低 60% |
| **质量保证** | 答案验证层 | 虚假引用率 < 5% |

---

## 📊 当前系统架构分析

### 现有技术栈

```
前端层: Next.js 14 + React + Zustand
   ↓
API层: FastAPI (backend/api/chat.py)
   ↓
核心层: Pipeline (src/pipeline.py)
   ↓
处理层:
   - PDF解析: MinerU (src/pdf_parsing_mineru.py)
   - 文档摄取: Ingestion (src/ingestion.py) ✅ BM25 + FAISS已实现
   - 问题处理: QuestionsProcessor (src/questions_processing.py) ❌ 检索逻辑缺失
   ↓
数据层:
   - 向量数据库: FAISS (data/databases/vector_dbs/) ✅ 已构建
   - 关键词索引: BM25 (data/databases/bm25/) ✅ 已构建
   - 元数据库: SQLite (data/databases/stock_rag.db) ✅ 已完善
```

### 关键代码现状

#### ✅ **已完成的优质代码**

1. **BM25 索引构建** (`src/ingestion.py` Line 28-78)
   - 中文分词逻辑完整
   - 支持多文档索引
   - 序列化和持久化完善

2. **FAISS 向量化** (`src/ingestion.py` Line 216-400)
   - 批处理优化
   - 重试机制完善
   - 中文路径问题已解决（MD5 hash临时文件名）

3. **场景化提示词** (`src/questions_processing.py` Line 51-150)
   - 投资研究、招投标、企业管理三种场景
   - Prompt模板已定制化

#### ❌ **核心缺陷代码**

**问题1: 检索逻辑完全缺失**

```python
# src/questions_processing.py Line 195-226
def retrieve_relevant_context(self, question: str, question_analysis: Dict[str, Any], top_k: int = 5):
    """检索相关上下文"""
    try:
        # 简化版本：暂时返回空列表
        # 这里可以集成向量检索和BM25检索
        logger.debug(f"检索相关上下文: {question}")

        # TODO: 实现真正的检索逻辑
        # 1. 使用question生成embedding
        # 2. 在向量数据库中搜索
        # 3. 使用BM25进行关键词搜索
        # 4. 合并和重排序结果

        relevant_docs = []  # ❌ 直接返回空列表！

        logger.debug(f"检索到 {len(relevant_docs)} 个相关文档")
        return relevant_docs
```

**问题2: Pipeline未调用检索**

```python
# src/pipeline.py 中完全没有调用检索逻辑
# 导致即使索引已构建，也无法被使用
```

---

## 🏗️ Agentic RAG 架构设计

### 整体架构图

```
用户提问
   ↓
┌─────────────────────────────────────────────┐
│  第一层: 智能路由层 (Routing Agent)           │
│  - 问题理解与分类 (Qwen-Turbo)                │
│  - 场景识别 (招投标/企业管理)                  │
│  - 文档范围初筛                                │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  第二层: 混合检索层 (Hybrid Retrieval)        │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │  BM25 关键词检索 │  │ FAISS 向量检索  │   │
│  │  (快速初筛)      │  │(Text-Embedding-V3)│  │
│  └─────────────────┘  └─────────────────┘   │
│           ↓                    ↓              │
│       ┌─────────────────────────┐            │
│       │   RRF 结果融合与重排序   │            │
│       └─────────────────────────┘            │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  第三层: 分层导航层 (Layered Navigation)      │
│  - 粗粒度筛选 (20个大块) (Qwen-Turbo)         │
│  - 细粒度定位 (5个小块)                        │
│  - 上下文扩展 (保证条款完整性)                 │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  第四层: 智能缓存层 (Smart Cache)             │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ 精确缓存      │  │ 语义缓存      │         │
│  │ (100%匹配)    │  │ (>95%相似)    │         │
│  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  第五层: 答案生成层 (Answer Generation)       │
│  - 场景化Prompt模板                           │
│  - 上下文注入                                 │
│  - Qwen LLM生成答案 (Qwen-Turbo/Plus)        │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  第六层: 验证层 (Verification)                │
│  - 引用完整性检查                             │
│  - Qwen-Max 交叉验证                          │
│  - 来源可追溯性验证                           │
└─────────────────────────────────────────────┘
   ↓
结构化答案输出
```

### Qwen 模型选择策略

| 模块 | 推荐模型 | 原因 | 成本 |
|-----|---------|------|------|
| **路由代理** | `qwen-turbo-latest` | 快速决策，成本低 | 💚 低 |
| **分层导航** | `qwen-turbo-latest` | 多轮调用，需控制成本 | 💚 低 |
| **答案生成** | `qwen-plus` | 平衡质量与成本 | 💛 中 |
| **答案验证** | `qwen-max` | 最高质量，确保准确 | 💰 高 |
| **向量嵌入** | `text-embedding-v3` | 最新嵌入模型 | 💚 低 |

**成本优化建议**:
- 80% 查询使用 `qwen-turbo` (¥0.002/1K tokens)
- 15% 复杂查询使用 `qwen-plus` (¥0.004/1K tokens)
- 5% 验证层使用 `qwen-max` (¥0.04/1K tokens)

---

## 🧩 核心模块设计

### 模块1: 智能路由代理 (RoutingAgent)

**位置**: `src/agents/routing_agent.py` (新建)

**职责**:
1. 理解用户问题意图
2. 选择最相关的文档块
3. 动态调整检索策略
4. 记录推理过程

**核心方法**:
```python
class RoutingAgent:
    def __init__(self, scenario_id: str):
        """初始化路由代理"""

    def analyze_query(self, question: str) -> Dict[str, Any]:
        """分析问题，提取关键信息"""
        # 返回: 问题类型、关键词、难度、所需文档类型

    def route_documents(self, chunks: List[Dict], question: str, history: str) -> Dict[str, Any]:
        """智能选择相关文档块"""
        # 返回: selected_chunks, reasoning, confidence

    def should_expand_context(self, chunk: Dict) -> bool:
        """判断是否需要扩展上下文"""
        # 检查条款/段落完整性
```

**实现要点**:
- 使用 Qwen (通义千问) 进行路由决策
- 强制 JSON 输出格式（通过 Prompt 引导）
- `temperature=0` 保证稳定性
- 支持场景化关键词库

**场景化关键词库**:
```python
self.keyword_library = {
    "tender": {
        "budget": ["预算", "报价", "价格", "金额", "资金"],
        "deadline": ["截止", "期限", "时间", "日期"],
        "requirement": ["要求", "条件", "资格", "标准"],
        "technical": ["技术", "规格", "参数", "性能"]
    },
    "enterprise": {
        "policy": ["政策", "制度", "规定", "流程"],
        "process": ["流程", "步骤", "程序", "办理"],
        "benefit": ["福利", "待遇", "补贴", "保险"],
        "training": ["培训", "学习", "发展", "晋升"]
    }
}
```

---

### 模块2: 混合检索引擎 (HybridRetriever)

**位置**: `src/retrieval/hybrid_retriever.py` (新建)

**职责**:
1. 统一调用 BM25 和 FAISS 检索
2. 结果融合与重排序（RRF算法）
3. 动态调整检索参数
4. 检索结果质量评估

**核心方法**:
```python
class HybridRetriever:
    def __init__(self, scenario_id: str):
        """初始化混合检索器"""
        self.bm25_retriever = BM25Retriever(scenario_id)
        self.vector_retriever = VectorRetriever(scenario_id)
        self.reranker = RRFReranker()

    def retrieve(self, question: str, top_k: int = 10) -> List[Dict]:
        """混合检索主接口"""
        # 1. BM25 关键词检索 (快速初筛)
        bm25_results = self.bm25_retriever.search(question, k=20)

        # 2. FAISS 向量检索 (语义理解)
        vector_results = self.vector_retriever.search(question, k=20)

        # 3. RRF 融合重排序
        final_results = self.reranker.fuse(bm25_results, vector_results, top_k=top_k)

        return final_results

    def get_retrieval_stats(self) -> Dict:
        """获取检索统计信息"""
        # 返回: 命中率、平均相似度、检索耗时
```

**RRF（Reciprocal Rank Fusion）算法**:
```python
def rrf_score(rank, k=60):
    """RRF评分公式"""
    return 1 / (k + rank)

# 融合示例:
# BM25结果: [doc1(rank=1), doc2(rank=2), doc3(rank=3)]
# Vector结果: [doc2(rank=1), doc1(rank=3), doc4(rank=2)]
# 融合后: doc2(最高分), doc1(次高分), doc3/doc4...
```

**降级策略**:
- BM25失败 → 使用纯向量检索
- 向量检索失败 → 使用纯BM25检索
- 两者都失败 → 返回空结果，触发纯LLM模式

---

### 模块3: 分层导航器 (LayeredNavigator)

**位置**: `src/retrieval/layered_navigator.py` (新建)

**职责**:
1. 实现多轮文档分块与筛选
2. 保证条款/段落完整性
3. 动态扩展上下文
4. 优化Token使用

**核心流程**:
```python
class LayeredNavigator:
    def navigate(self, document: Dict, question: str, max_rounds: int = 3) -> List[Dict]:
        """多轮分层导航"""
        # 第一轮: 粗粒度分块 (20个大块)
        chunks = self.split_document(document, n_chunks=20)
        scratchpad = f"开始检索: {question}"

        for round in range(max_rounds):
            # 使用路由代理选择相关块
            selected = self.routing_agent.route_documents(chunks, question, scratchpad)

            # 检查总Token数
            total_tokens = sum(len(c['text']) for c in selected['chunks'])
            if total_tokens < 2000:  # 足够小，停止细分
                break

            # 继续细分
            chunks = self.refine_chunks(selected['chunks'], n_sub=5)
            scratchpad += f"\n第{round+1}轮: 选中{len(chunks)}个块"

        # 扩展上下文，保证完整性
        complete_chunks = self.expand_context(chunks, document)
        return complete_chunks
```

**分块策略**:
- 招投标场景: 按章节/条款分块（优先识别"第X条"、"第X章"）
- 企业管理场景: 按业务模块分块（如"薪酬制度"、"考勤管理"）

**完整性保证**:
- 检查段落是否以句号、分号结尾
- 若不完整，向前/后扩展200字符
- 记录扩展状态，便于追溯

---

### 模块4: 智能缓存管理 (SmartCache)

**位置**: `src/cache/smart_cache.py` (新建)

**职责**:
1. 精确匹配缓存（问题完全相同）
2. 语义匹配缓存（问题相似度>95%）
3. 缓存过期管理
4. 缓存命中率统计

**双层缓存架构**:
```python
class SmartCache:
    def __init__(self):
        """初始化智能缓存"""
        self.exact_cache = {}  # key: question_hash, value: answer
        self.semantic_cache = {}  # key: embedding, value: (question, answer)
        self.cache_stats = {"exact_hits": 0, "semantic_hits": 0, "misses": 0}

    def get(self, question: str) -> Optional[Dict]:
        """获取缓存答案"""
        # 1. 精确匹配 (MD5 hash)
        question_hash = hashlib.md5(question.encode()).hexdigest()
        if question_hash in self.exact_cache:
            self.cache_stats["exact_hits"] += 1
            return self.exact_cache[question_hash]

        # 2. 语义匹配 (余弦相似度 > 0.95)
        question_emb = self.get_embedding(question)
        for cache_emb, (cache_q, cache_ans) in self.semantic_cache.items():
            similarity = self.cosine_similarity(question_emb, cache_emb)
            if similarity > 0.95:
                self.cache_stats["semantic_hits"] += 1
                return cache_ans

        # 3. 缓存未命中
        self.cache_stats["misses"] += 1
        return None
```

**缓存策略**:
- 精确缓存: 7天过期
- 语义缓存: 3天过期
- 最大缓存数: 1000条
- LRU淘汰策略

**命中率计算**:
```python
def get_hit_rate(self) -> float:
    """计算缓存命中率"""
    total = sum(self.cache_stats.values())
    hits = self.cache_stats["exact_hits"] + self.cache_stats["semantic_hits"]
    return hits / total if total > 0 else 0.0
```

---

### 模块5: 答案验证器 (AnswerVerifier)

**位置**: `src/verification/answer_verifier.py` (新建)

**职责**:
1. 提取答案中的引用（页码、段落号）
2. 验证引用的真实性
3. Qwen交叉验证（使用 qwen-max 或 qwen-plus 模型）
4. 生成可信度评分

**三层验证机制**:
```python
class AnswerVerifier:
    def verify_answer(self, answer: str, source_chunks: List[Dict]) -> Dict[str, Any]:
        """验证答案的准确性"""
        # 1. 提取引用
        citations = self.extract_citations(answer)

        # 2. 验证引用存在性
        for citation in citations:
            if not self.citation_exists(citation, source_chunks):
                return {
                    "is_valid": False,
                    "error": f"虚假引用: {citation}",
                    "confidence": 0.1
                }

        # 3. Qwen交叉验证
        verification = self.qwen_verify(answer, source_chunks)

        return {
            "is_valid": verification["is_valid"],
            "confidence": verification["confidence"],
            "reasoning": verification["reasoning"]
        }
```

**引用提取（正则表达式）**:
```python
def extract_citations(self, answer: str) -> List[str]:
    """提取答案中的引用"""
    import re
    citations = []
    # 匹配 "第X页"
    citations.extend(re.findall(r"第(\d+)页", answer))
    # 匹配 "第X条"
    citations.extend(re.findall(r"第(\d+)条", answer))
    # 匹配 "段落X"
    citations.extend(re.findall(r"段落(\d+)", answer))
    return citations
```

**Qwen 交叉验证**:
```python
def qwen_verify(self, answer: str, source_chunks: List[Dict]) -> Dict:
    """使用Qwen-Max进行交叉验证"""
    prompt = f"""
    任务：判断答案是否完全基于源文档，无编造内容。
    答案：{answer}
    源文档块：{chr(10).join([c['text'] for c in source_chunks])}

    请以JSON格式输出：
    {{
        "is_valid": true/false,
        "confidence": 0-1的浮点数,
        "reasoning": "验证说明"
    }}
    """
    # 调用 qwen-max 进行验证
    response = self.api_processor.send_message(
        model="qwen-max",
        system_content="你是答案验证专家。",
        human_content=prompt,
        temperature=0
    )
    return json.loads(response)
```

---

## 📊 预期效果

### 定量指标

| 指标 | 重构前 | 重构后 | 提升 |
|-----|-------|-------|------|
| **检索准确率** | 0% (空实现) | 85%+ | +85% |
| **答案质量分** | 60分 (纯LLM) | 90分+ | +50% |
| **平均响应时间** | 2s | 4s | -50% (但有检索) |
| **API成本/query** | ¥0.3 | ¥0.2 | -33% (缓存优化) |
| **缓存命中率** | 0% | 30%+ | +30% |
| **虚假引用率** | 未知 | < 5% | 显著降低 |

### 定性提升

| 维度 | 重构前 | 重构后 |
|-----|-------|-------|
| **长文档处理** | ❌ 单纯分块效果差 | ✅ 分层导航，准确定位 |
| **答案可信度** | ⚠️ 无引用验证 | ✅ 引用验证 + 来源追溯 |
| **用户体验** | ⚠️ 答案质量不稳定 | ✅ 高质量稳定答案 |
| **成本控制** | ⚠️ 无缓存优化 | ✅ 智能缓存 + 分层策略 |
| **系统扩展性** | ⚠️ 单一场景 | ✅ 多场景支持 |

---

## 🔧 技术规范

### 代码规范

1. **命名规范**:
   - 类名: PascalCase (如 `HybridRetriever`)
   - 函数名: snake_case (如 `retrieve_context`)
   - 常量名: UPPER_SNAKE_CASE (如 `MAX_RETRIES`)

2. **文档字符串**:
   ```python
   def function_name(param1: str, param2: int) -> Dict[str, Any]:
       """函数简短描述

       Args:
           param1: 参数1说明
           param2: 参数2说明

       Returns:
           返回值说明

       Raises:
           ValueError: 错误情况说明
       """
   ```

3. **日志规范**:
   - DEBUG: 详细调试信息
   - INFO: 关键流程节点
   - WARNING: 降级或异常情况
   - ERROR: 严重错误

---

## 📚 参考资料

1. [Agentic RAG完整实现指南](./Agentic_RAG完整实现指南.md)
2. [多场景AI知识问答系统开发任务清单](./多场景AI知识问答系统开发任务清单.md)
3. [Agentic_RAG重构任务清单](./Agentic_RAG重构任务清单.md) *(配套文档)*
4. [RAG架构设计规则](.cursor/rules/rag-architecture.mdc)
5. [后端Python开发规则](.cursor/rules/backend-python.mdc)

---

**文档版本**: v1.0
**最后更新**: 2025-09-30
**文档状态**: ✅ 已完成

