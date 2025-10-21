# Agentic RAG 系统 API 文档

## 📋 目录

- [1. 核心模块 API](#1-核心模块-api)
  - [1.1 BM25Retriever](#11-bm25retriever)
  - [1.2 VectorRetriever](#12-vectorretriever)
  - [1.3 HybridRetriever](#13-hybridretriever)
  - [1.4 RoutingAgent](#14-routingagent)
  - [1.5 LayeredNavigator](#15-layerednavigator)
  - [1.6 SmartCache](#16-smartcache)
  - [1.7 AnswerVerifier](#17-answerverifier)
- [2. QuestionsProcessor API](#2-questionsprocessor-api)
- [3. Pipeline API](#3-pipeline-api)
- [4. 后端 API 接口](#4-后端-api-接口)
- [5. 数据模型](#5-数据模型)
- [6. 错误码](#6-错误码)

---

## 1. 核心模块 API

### 1.1 BM25Retriever

**路径**: `src/retrieval/bm25_retriever.py`

#### 类定义

```python
class BM25Retriever:
    """BM25 关键词检索器"""

    def __init__(self, scenario_id: str)
```

**参数**:
- `scenario_id` (str): 业务场景ID，如 "tender", "enterprise"

**功能**: 加载指定场景的BM25索引文件

---

#### 方法：search()

```python
def search(self, query: str, k: int = 10) -> List[Dict]
```

**功能**: 使用BM25算法检索相关文档块

**参数**:
- `query` (str): 查询文本
- `k` (int, 可选): 返回结果数量，默认10

**返回值**: `List[Dict]`
```python
[
    {
        "text": "文档内容...",
        "file_id": "tender_uuid_filename",
        "page": 3,
        "score": 8.52,
        "chunk_id": 15,
        "metadata": {...}
    },
    ...
]
```

**示例**:
```python
from src.retrieval.bm25_retriever import BM25Retriever

retriever = BM25Retriever(scenario_id="tender")
results = retriever.search("项目预算", k=5)

for result in results:
    print(f"Score: {result['score']:.2f}, Page: {result['page']}")
    print(f"Text: {result['text'][:100]}...")
```

---

### 1.2 VectorRetriever

**路径**: `src/retrieval/vector_retriever.py`

#### 类定义

```python
class VectorRetriever:
    """FAISS 向量检索器"""

    def __init__(self, scenario_id: str)
```

**参数**:
- `scenario_id` (str): 业务场景ID

**功能**: 加载FAISS索引和元数据

---

#### 方法：search()

```python
def search(
    self,
    query: str,
    k: int = 10,
    min_similarity: float = 0.5
) -> List[Dict]
```

**功能**: 使用向量相似度检索相关文档

**参数**:
- `query` (str): 查询文本
- `k` (int, 可选): 返回结果数量，默认10
- `min_similarity` (float, 可选): 最小相似度阈值，默认0.5

**返回值**: `List[Dict]`
```python
[
    {
        "text": "文档内容...",
        "file_id": "tender_uuid_filename",
        "page": 3,
        "similarity": 0.87,
        "chunk_id": 15,
        "metadata": {...}
    },
    ...
]
```

**示例**:
```python
from src.retrieval.vector_retriever import VectorRetriever

retriever = VectorRetriever(scenario_id="tender")
results = retriever.search("项目预算", k=5, min_similarity=0.6)

for result in results:
    print(f"Similarity: {result['similarity']:.2f}")
    print(f"Text: {result['text'][:100]}...")
```

**注意事项**:
- 需要调用 DashScope API 生成查询向量
- 首次查询会有网络延迟（约1-2秒）
- 建议使用查询向量缓存优化性能

---

### 1.3 HybridRetriever

**路径**: `src/retrieval/hybrid_retriever.py`

#### 类定义

```python
class HybridRetriever:
    """混合检索器（BM25 + FAISS + RRF融合）"""

    def __init__(self, scenario_id: str)
```

**参数**:
- `scenario_id` (str): 业务场景ID

**功能**: 初始化BM25和向量检索器，以及RRF重排序器

---

#### 方法：retrieve()

```python
def retrieve(
    self,
    question: str,
    top_k: int = 10,
    use_bm25: bool = True,
    use_vector: bool = True,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> List[Dict]
```

**功能**: 混合检索并使用RRF融合结果

**参数**:
- `question` (str): 查询问题
- `top_k` (int, 可选): 返回结果数量，默认10
- `use_bm25` (bool, 可选): 是否使用BM25，默认True
- `use_vector` (bool, 可选): 是否使用向量检索，默认True
- `bm25_weight` (float, 可选): BM25权重，默认0.5
- `vector_weight` (float, 可选): 向量检索权重，默认0.5

**返回值**: `List[Dict]`
```python
[
    {
        "text": "文档内容...",
        "file_id": "tender_uuid_filename",
        "page": 3,
        "rrf_score": 0.0234,  # RRF融合分数
        "bm25_score": 8.52,   # 原始BM25分数
        "vector_score": 0.87, # 原始向量相似度
        "chunk_id": 15,
        "metadata": {...}
    },
    ...
]
```

**示例**:
```python
from src.retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(scenario_id="tender")

# 混合检索
results = retriever.retrieve(
    question="项目预算是多少？",
    top_k=10,
    bm25_weight=0.6,
    vector_weight=0.4
)

# 查看统计信息
stats = retriever.get_stats()
print(f"总查询数: {stats['total_queries']}")
print(f"平均耗时: {stats['avg_time']:.2f}秒")
```

---

#### 方法：get_stats()

```python
def get_stats(self) -> Dict[str, Any]
```

**功能**: 获取检索统计信息

**返回值**: `Dict`
```python
{
    "total_queries": 42,
    "avg_time": 1.23,
    "bm25_only_count": 5,
    "vector_only_count": 3,
    "hybrid_count": 34,
    "failed_count": 0
}
```

---

### 1.4 RoutingAgent

**路径**: `src/agents/routing_agent.py`

#### 类定义

```python
class RoutingAgent:
    """LLM驱动的智能路由代理"""

    def __init__(self, scenario_id: str)
```

**参数**:
- `scenario_id` (str): 业务场景ID

**功能**: 初始化场景化关键词库和API处理器

---

#### 方法：analyze_query()

```python
def analyze_query(self, question: str) -> Dict[str, Any]
```

**功能**: 使用LLM分析查询意图

**参数**:
- `question` (str): 用户问题

**返回值**: `Dict`
```python
{
    "intent": "信息查询",
    "keywords": ["预算", "金额", "资金"],
    "difficulty": "简单",
    "requires_context": True,
    "estimated_chunks_needed": 5
}
```

**示例**:
```python
from src.agents.routing_agent import RoutingAgent

agent = RoutingAgent(scenario_id="tender")
analysis = agent.analyze_query("项目预算是多少？")

print(f"意图: {analysis['intent']}")
print(f"关键词: {', '.join(analysis['keywords'])}")
```

---

#### 方法：route_documents()

```python
def route_documents(
    self,
    chunks: List[Dict],
    question: str,
    history: str = "",
    top_k: int = 10
) -> Dict[str, Any]
```

**功能**: LLM驱动的文档路由和筛选

**参数**:
- `chunks` (List[Dict]): 候选文档块列表
- `question` (str): 用户问题
- `history` (str, 可选): 对话历史，默认空
- `top_k` (int, 可选): 返回文档数量，默认10

**返回值**: `Dict`
```python
{
    "success": True,
    "chunks": [
        {
            "text": "...",
            "relevance_score": 0.92,
            "reasoning": "包含预算相关信息"
        },
        ...
    ],
    "confidence": 0.85,
    "reasoning": "找到5个高度相关的文档块"
}
```

**示例**:
```python
agent = RoutingAgent(scenario_id="tender")

# 先检索候选文档
from src.retrieval.hybrid_retriever import HybridRetriever
retriever = HybridRetriever(scenario_id="tender")
candidates = retriever.retrieve("项目预算", top_k=20)

# 智能路由筛选
result = agent.route_documents(
    chunks=candidates,
    question="项目预算是多少？",
    top_k=5
)

if result["success"]:
    print(f"筛选出 {len(result['chunks'])} 个文档")
    print(f"置信度: {result['confidence']:.2f}")
```

---

### 1.5 LayeredNavigator

**路径**: `src/retrieval/layered_navigator.py`

#### 类定义

```python
class LayeredNavigator:
    """分层导航器（多轮筛选 + Token控制）"""

    def __init__(self, routing_agent: RoutingAgent)
```

**参数**:
- `routing_agent` (RoutingAgent): 路由代理实例

**功能**: 初始化导航器

---

#### 方法：navigate()

```python
def navigate(
    self,
    chunks: List[Dict],
    question: str,
    max_rounds: int = 3,
    target_tokens: int = 2000
) -> List[Dict]
```

**功能**: 多轮分层导航，控制Token数量

**参数**:
- `chunks` (List[Dict]): 初始文档块列表
- `question` (str): 用户问题
- `max_rounds` (int, 可选): 最大导航轮数，默认3
- `target_tokens` (int, 可选): 目标Token数，默认2000

**返回值**: `List[Dict]` - 优化后的文档块列表

**示例**:
```python
from src.retrieval.layered_navigator import LayeredNavigator
from src.agents.routing_agent import RoutingAgent

agent = RoutingAgent(scenario_id="tender")
navigator = LayeredNavigator(routing_agent=agent)

# 假设已有20个候选文档
chunks = retriever.retrieve("项目预算", top_k=20)

# 分层导航
final_chunks = navigator.navigate(
    chunks=chunks,
    question="项目预算是多少？",
    max_rounds=3,
    target_tokens=1500
)

print(f"导航前: {len(chunks)} 个文档")
print(f"导航后: {len(final_chunks)} 个文档")
```

---

### 1.6 SmartCache

**路径**: `src/cache/smart_cache.py`

#### 类定义

```python
class SmartCache:
    """智能缓存（精确 + 语义）"""

    def __init__(
        self,
        max_size: int = 1000,
        exact_ttl_days: int = 7,
        semantic_ttl_days: int = 3,
        semantic_threshold: float = 0.95
    )
```

**参数**:
- `max_size` (int, 可选): 最大缓存条目数，默认1000
- `exact_ttl_days` (int, 可选): 精确缓存TTL（天），默认7
- `semantic_ttl_days` (int, 可选): 语义缓存TTL（天），默认3
- `semantic_threshold` (float, 可选): 语义相似度阈值，默认0.95

---

#### 方法：get()

```python
def get(self, question: str) -> Optional[Dict]
```

**功能**: 获取缓存的答案（先精确，后语义）

**参数**:
- `question` (str): 用户问题

**返回值**: `Optional[Dict]`
```python
{
    "answer": "根据第3页，项目预算为100万元。",
    "confidence": 0.92,
    "sources": [...],
    "cached_at": 1696234567.89
}
```

**示例**:
```python
from src.cache.smart_cache import SmartCache

cache = SmartCache(max_size=500)

# 尝试获取缓存
result = cache.get("项目预算是多少？")

if result:
    print("✅ 缓存命中！")
    print(f"答案: {result['answer']}")
else:
    print("❌ 缓存未命中，需要执行检索")
```

---

#### 方法：set()

```python
def set(
    self,
    question: str,
    answer: Dict,
    use_semantic: bool = False
)
```

**功能**: 存储答案到缓存

**参数**:
- `question` (str): 用户问题
- `answer` (Dict): 答案数据
- `use_semantic` (bool, 可选): 是否同时存储语义缓存，默认False

**示例**:
```python
cache = SmartCache()

answer_data = {
    "answer": "项目预算为100万元。",
    "confidence": 0.92,
    "sources": [...]
}

# 存储（精确 + 语义）
cache.set(
    question="项目预算是多少？",
    answer=answer_data,
    use_semantic=True
)
```

---

#### 方法：get_stats()

```python
def get_stats(self) -> Dict[str, Any]
```

**功能**: 获取缓存统计信息

**返回值**: `Dict`
```python
{
    "exact_hits": 42,
    "semantic_hits": 15,
    "misses": 23,
    "evictions": 5,
    "total_queries": 80,
    "hit_rate": 0.7125,
    "exact_cache_size": 50,
    "semantic_cache_size": 30,
    "total_cache_size": 80
}
```

---

### 1.7 AnswerVerifier

**路径**: `src/verification/answer_verifier.py`

#### 类定义

```python
class AnswerVerifier:
    """答案验证器（三层验证）"""

    def __init__(self)
```

**功能**: 初始化验证器和引用提取模式

---

#### 方法：verify_answer()

```python
def verify_answer(
    self,
    answer: str,
    source_chunks: List[Dict],
    question: str
) -> Dict[str, Any]
```

**功能**: 三层验证答案准确性

**参数**:
- `answer` (str): LLM生成的答案
- `source_chunks` (List[Dict]): 源文档块
- `question` (str): 原始问题

**返回值**: `Dict`
```python
{
    "is_valid": True,
    "confidence": 0.92,
    "reasoning": "引用真实存在，LLM验证通过",
    "citations": ["第3页", "第5页"],
    "citation_check": {
        "total": 2,
        "valid": 2,
        "invalid": 0
    },
    "llm_verification": {
        "consistent": True,
        "confidence": 0.95
    }
}
```

**示例**:
```python
from src.verification.answer_verifier import AnswerVerifier

verifier = AnswerVerifier()

answer = "根据第3页，项目预算为100万元。"
source_chunks = [
    {"page": 3, "text": "项目总预算：100万元"},
    {"page": 5, "text": "其他相关信息"}
]

result = verifier.verify_answer(
    answer=answer,
    source_chunks=source_chunks,
    question="项目预算是多少？"
)

print(f"验证结果: {'通过' if result['is_valid'] else '失败'}")
print(f"置信度: {result['confidence']:.2f}")
print(f"引用检查: {result['citation_check']}")
```

---

## 2. QuestionsProcessor API

**路径**: `src/questions_processing.py`

### 类定义

```python
class QuestionsProcessor:
    """问题处理器（集成 Agentic RAG）"""

    def __init__(
        self,
        api_provider: str = "dashscope",
        scenario_id: str = "tender"
    )
```

**参数**:
- `api_provider` (str, 可选): API提供商，默认"dashscope"
- `scenario_id` (str, 可选): 业务场景ID，默认"tender"

---

### 方法：process_question()

```python
def process_question(
    self,
    question: str,
    company: Optional[str] = None,
    question_type: str = "string"
) -> Dict[str, Any]
```

**功能**: 完整的问题处理流程（Agentic RAG）

**参数**:
- `question` (str): 用户问题
- `company` (Optional[str], 可选): 目标公司，默认None
- `question_type` (str, 可选): 问题类型，默认"string"

**返回值**: `Dict`
```python
{
    "success": True,
    "answer": "根据第3页，项目预算为100万元。",
    "reasoning": "基于LLM分析生成 (验证: passed)",
    "relevant_pages": [3, 5],
    "confidence": 0.92,
    "processing_time": 4.2,
    "context_docs_count": 5,
    "verification": {
        "is_valid": True,
        "confidence": 0.92,
        "citations": ["第3页"]
    }
}
```

**示例**:
```python
from src.questions_processing import QuestionsProcessor

processor = QuestionsProcessor(
    api_provider="dashscope",
    scenario_id="tender"
)

result = processor.process_question(
    question="项目预算是多少？",
    company="某某公司"
)

if result["success"]:
    print(f"答案: {result['answer']}")
    print(f"置信度: {result['confidence']:.2f}")
    print(f"耗时: {result['processing_time']:.2f}秒")
else:
    print(f"错误: {result.get('error')}")
```

---

### 方法：get_agentic_rag_stats()

```python
def get_agentic_rag_stats(self) -> Dict[str, Any]
```

**功能**: 获取 Agentic RAG 统计信息

**返回值**: `Dict`
```python
{
    "enabled": True,
    "cache_stats": {
        "exact_hits": 42,
        "semantic_hits": 15,
        "hit_rate": 0.71
    },
    "retrieval_stats": {
        "total_queries": 80,
        "avg_time": 1.23
    },
    "scenario_id": "tender"
}
```

---

## 3. Pipeline API

**路径**: `src/pipeline.py`

### 类定义

```python
class Pipeline:
    """多场景RAG系统主流水线"""

    def __init__(
        self,
        root_path: Path,
        subset_name: str = "subset.csv",
        questions_file_name: str = "questions.json",
        pdf_reports_dir_name: str = "pdf_reports",
        run_config: RunConfig = None,
        scenario_id: str = "tender"
    )
```

**参数**:
- `root_path` (Path): 数据根目录
- `subset_name` (str, 可选): 元数据文件名
- `questions_file_name` (str, 可选): 问题文件名
- `pdf_reports_dir_name` (str, 可选): PDF目录名
- `run_config` (RunConfig, 可选): 运行配置
- `scenario_id` (str, 可选): 场景ID

---

### 方法：prepare_documents()

```python
def prepare_documents(
    self,
    force_rebuild: bool = False
) -> Dict[str, Any]
```

**功能**: 文档准备（PDF解析 + 向量化）

**参数**:
- `force_rebuild` (bool, 可选): 是否强制重建，默认False

**返回值**: `Dict`
```python
{
    "parsing_results": {
        "total_files": 10,
        "successful": 10,
        "failed": 0
    },
    "ingestion_results": {
        "success": True,
        "processed_files": 10
    },
    "success": True,
    "total_time": 125.5
}
```

---

### 方法：answer_question()

```python
def answer_question(
    self,
    question: str,
    company: Optional[str] = None,
    question_type: str = "string"
) -> Dict[str, Any]
```

**功能**: 回答单个问题（使用 Agentic RAG）

**参数**:
- `question` (str): 问题文本
- `company` (Optional[str], 可选): 目标公司
- `question_type` (str, 可选): 问题类型

**返回值**: 同 `QuestionsProcessor.process_question()`

---

## 4. 后端 API 接口

### 4.1 问答接口

**端点**: `POST /api/v2/ask`

**请求体**:
```json
{
  "question": "项目预算是多少？",
  "scenario_id": "tender",
  "company": "某某公司",
  "question_type": "string"
}
```

**响应**:
```json
{
  "answer": "根据第3页，项目预算为100万元。",
  "confidence": 0.92,
  "sources": [
    {
      "title": "文档第3页",
      "content": "来自第3页的相关内容",
      "page": 3,
      "score": 0.95
    }
  ],
  "reasoning": "基于LLM分析生成 (验证: passed)",
  "processing_time": 4.2
}
```

---

### 4.2 文档上传接口

**端点**: `POST /api/v2/upload`

**请求**: `multipart/form-data`
- `file`: PDF文件
- `scenario_id`: 场景ID
- `document_type`: 文档类型

**响应**:
```json
{
  "success": true,
  "document_id": "doc_12345",
  "filename": "招标文件.pdf",
  "processing_status": "completed"
}
```

---

### 4.3 场景管理接口

**端点**: `GET /api/v2/scenarios`

**响应**:
```json
[
  {
    "id": "tender",
    "name": "招投标",
    "description": "招投标文件分析",
    "ui_config": {
      "theme_color": "#3B82F6",
      "welcome_title": "招投标智能助手"
    },
    "preset_questions": [
      "项目预算是多少？",
      "截止日期是什么时候？"
    ]
  }
]
```

---

## 5. 数据模型

### 5.1 文档块 (Chunk)

```python
{
    "text": str,           # 文档内容
    "file_id": str,        # 文件ID
    "page": int,           # 页码
    "chunk_id": int,       # 块ID
    "score": float,        # 相关性分数
    "similarity": float,   # 向量相似度
    "metadata": {
        "word_count": int,
        "char_count": int,
        "has_table": bool
    }
}
```

### 5.2 问答结果 (QA Result)

```python
{
    "success": bool,
    "answer": str,
    "reasoning": str,
    "relevant_pages": List[int],
    "confidence": float,
    "processing_time": float,
    "context_docs_count": int,
    "verification": Dict
}
```

---

## 6. 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `PIPELINE_NOT_READY` | Pipeline未就绪 | 调用 `prepare_documents()` |
| `NO_DOCUMENTS_FOUND` | 未找到相关文档 | 检查索引文件是否存在 |
| `API_CALL_FAILED` | API调用失败 | 检查网络和API密钥 |
| `CACHE_ERROR` | 缓存错误 | 清空缓存重试 |
| `VERIFICATION_FAILED` | 答案验证失败 | 检查源文档质量 |

---

## 📝 使用建议

1. **首次使用**: 先调用 `Pipeline.prepare_documents()` 准备文档
2. **性能优化**: 启用缓存可减少50%响应时间
3. **准确性**: 使用答案验证确保引用真实性
4. **成本控制**: 合理设置 `top_k` 和 `target_tokens`

---

**文档版本**: v1.0
**最后更新**: 2025-09-30
**维护团队**: Agentic RAG 开发团队

