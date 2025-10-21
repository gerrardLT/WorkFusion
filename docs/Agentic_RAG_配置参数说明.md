# Agentic RAG 系统配置参数说明

## 📋 目录

- [1. 环境变量配置](#1-环境变量配置)
- [2. 核心模块配置](#2-核心模块配置)
- [3. 场景配置](#3-场景配置)
- [4. 性能调优参数](#4-性能调优参数)
- [5. 缓存配置](#5-缓存配置)
- [6. 数据库配置](#6-数据库配置)

---

## 1. 环境变量配置

### 1.1 必需环境变量

在项目根目录创建 `.env` 文件（参考 `config_template.env`）：

```bash
# DashScope API 配置
DASHSCOPE_API_KEY=your_api_key_here

# 数据目录配置
DATA_DIR=data/stock_data

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/system.log
```

---

### 1.2 可选环境变量

```bash
# API 超时设置（秒）
API_TIMEOUT=30

# 最大重试次数
MAX_RETRIES=3

# 批处理大小
BATCH_SIZE=10

# 缓存目录
CACHE_DIR=.cache

# 临时文件目录
TEMP_DIR=.temp
```

---

## 2. 核心模块配置

### 2.1 BM25Retriever 配置

**位置**: `src/retrieval/bm25_retriever.py`

```python
class BM25Retriever:
    def __init__(self, scenario_id: str):
        # 配置参数
        self.scenario_id = scenario_id  # 场景ID
        self.bm25_dir = Path(f"data/databases/bm25/")  # BM25索引目录
```

**可调参数**:
- `k1` (float): BM25算法参数，控制词频饱和度，默认1.5
- `b` (float): BM25算法参数，控制文档长度归一化，默认0.75

**调优建议**:
- 短文档：降低 `b` 值（0.5-0.6）
- 长文档：提高 `b` 值（0.8-0.9）
- 提高召回率：降低 `k1` 值
- 提高精确率：提高 `k1` 值

---

### 2.2 VectorRetriever 配置

**位置**: `src/retrieval/vector_retriever.py`

```python
class VectorRetriever:
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.vector_db_dir = Path(f"data/databases/vector_dbs/")
        self.embedding_model = "text-embedding-v3"  # 嵌入模型
```

**可调参数**:
- `min_similarity` (float): 最小相似度阈值，默认0.5
- `embedding_model` (str): 嵌入模型名称
  - `text-embedding-v1`: 旧版，1536维
  - `text-embedding-v3`: 新版，1536维，性能更好

**调优建议**:
- 提高精确率：提高 `min_similarity`（0.6-0.7）
- 提高召回率：降低 `min_similarity`（0.3-0.4）
- 使用 `text-embedding-v3` 获得更好的语义理解

---

### 2.3 HybridRetriever 配置

**位置**: `src/retrieval/hybrid_retriever.py`

```python
class HybridRetriever:
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.reranker = RRFReranker(k=60)  # RRF参数
```

**可调参数**:
- `bm25_weight` (float): BM25权重，默认0.5
- `vector_weight` (float): 向量检索权重，默认0.5
- `rrf_k` (int): RRF算法参数，默认60

**权重调优**:
```python
# 场景1：关键词匹配更重要（招投标）
retriever.retrieve(
    question="...",
    bm25_weight=0.6,
    vector_weight=0.4
)

# 场景2：语义理解更重要（企业管理）
retriever.retrieve(
    question="...",
    bm25_weight=0.4,
    vector_weight=0.6
)

# 场景3：平衡模式
retriever.retrieve(
    question="...",
    bm25_weight=0.5,
    vector_weight=0.5
)
```

**RRF参数调优**:
- `k` 值越大，排名靠后的文档权重越小
- 推荐范围：40-80
- 默认60适用于大多数场景

---

### 2.4 RoutingAgent 配置

**位置**: `src/agents/routing_agent.py`

```python
class RoutingAgent:
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.llm_model = "qwen-turbo-latest"  # LLM模型
        self.keyword_library = {...}  # 关键词库
```

**LLM模型选择**:
```python
# 快速模式（低成本）
agent = RoutingAgent(scenario_id="tender")
agent.llm_model = "qwen-turbo-latest"

# 平衡模式（推荐）
agent.llm_model = "qwen-plus"

# 高精度模式（高成本）
agent.llm_model = "qwen-max"
```

**关键词库配置**:
```python
keyword_library = {
    "tender": {
        "budget": ["预算", "报价", "价格", "金额"],
        "deadline": ["截止", "期限", "时间", "日期"],
        "requirement": ["要求", "条件", "资格"],
        "technical": ["技术", "规格", "参数"]
    },
    "enterprise": {
        "policy": ["政策", "制度", "规定"],
        "process": ["流程", "步骤", "程序"],
        "benefit": ["福利", "待遇", "补贴"],
        "training": ["培训", "学习", "发展"]
    }
}
```

---

### 2.5 LayeredNavigator 配置

**位置**: `src/retrieval/layered_navigator.py`

```python
class LayeredNavigator:
    def navigate(
        self,
        chunks: List[Dict],
        question: str,
        max_rounds: int = 3,      # 最大导航轮数
        target_tokens: int = 2000  # 目标Token数
    ):
        ...
```

**参数调优**:
```python
# 短问题（简单查询）
navigator.navigate(
    chunks=chunks,
    question="预算是多少？",
    max_rounds=2,
    target_tokens=1000
)

# 复杂问题（需要更多上下文）
navigator.navigate(
    chunks=chunks,
    question="请详细说明项目的技术要求和实施方案",
    max_rounds=4,
    target_tokens=3000
)

# 默认配置（平衡）
navigator.navigate(
    chunks=chunks,
    question="...",
    max_rounds=3,
    target_tokens=2000
)
```

**Token估算配置**:
```python
# 简单估算（字符数 × 1.5）
def estimate_tokens_simple(text: str) -> int:
    return int(len(text) * 1.5)

# 精确估算（使用tiktoken）
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
def estimate_tokens_accurate(text: str) -> int:
    return len(enc.encode(text))
```

---

### 2.6 SmartCache 配置

**位置**: `src/cache/smart_cache.py`

```python
class SmartCache:
    def __init__(
        self,
        max_size: int = 1000,           # 最大缓存条目数
        exact_ttl_days: int = 7,        # 精确缓存TTL（天）
        semantic_ttl_days: int = 3,     # 语义缓存TTL（天）
        semantic_threshold: float = 0.95 # 语义相似度阈值
    ):
        ...
```

**配置建议**:
```python
# 小型系统（< 100 用户）
cache = SmartCache(
    max_size=500,
    exact_ttl_days=7,
    semantic_ttl_days=3,
    semantic_threshold=0.95
)

# 中型系统（100-1000 用户）
cache = SmartCache(
    max_size=2000,
    exact_ttl_days=14,
    semantic_ttl_days=7,
    semantic_threshold=0.93
)

# 大型系统（> 1000 用户）
cache = SmartCache(
    max_size=5000,
    exact_ttl_days=30,
    semantic_ttl_days=14,
    semantic_threshold=0.90
)
```

**语义阈值调优**:
- `0.95-1.0`: 非常严格，只缓存几乎相同的问题
- `0.90-0.95`: 推荐范围，平衡准确性和命中率
- `0.85-0.90`: 宽松，提高命中率但可能降低准确性
- `< 0.85`: 不推荐，可能返回不相关答案

---

### 2.7 AnswerVerifier 配置

**位置**: `src/verification/answer_verifier.py`

```python
class AnswerVerifier:
    def __init__(self):
        self.llm_model = "qwen-plus"  # LLM验证模型
        self.citation_patterns = [...]  # 引用模式
```

**引用模式配置**:
```python
citation_patterns = [
    r'第(\d+)页',           # "第3页"
    r'第(\d+)-(\d+)页',     # "第3-5页"
    r'(?:见|参见|参考)第(\d+)页',  # "参见第3页"
    r'根据第(\d+)页',       # "根据第3页"
    r'\[(\d+)\]',           # "[3]"
    r'页码[：:]\s*(\d+)',   # "页码：3"
]
```

**验证严格度配置**:
```python
# 严格模式（高准确性）
verifier.min_confidence = 0.8
verifier.require_citation = True

# 宽松模式（高召回率）
verifier.min_confidence = 0.6
verifier.require_citation = False

# 平衡模式（推荐）
verifier.min_confidence = 0.7
verifier.require_citation = True
```

---

## 3. 场景配置

### 3.1 场景定义

**位置**: `src/models/scenario_models.py`

```python
DEFAULT_SCENARIO_CONFIGS = {
    "tender": {
        "id": "tender",
        "name": "招投标",
        "description": "招投标文件分析与问答",
        "ui_config": {
            "theme_color": "#3B82F6",
            "welcome_title": "招投标智能助手",
            "welcome_message": "我可以帮您分析招投标文件..."
        },
        "preset_questions": [
            "项目预算是多少？",
            "截止日期是什么时候？",
            "有哪些技术要求？"
        ],
        "document_types": [
            "招标文件",
            "技术规范",
            "合同模板"
        ],
        "prompt_templates": {
            "system": "你是专业的招投标分析师...",
            "user": "基于以下文档回答问题..."
        }
    }
}
```

---

### 3.2 添加新场景

**步骤**:

1. **定义场景配置**:
```python
# src/models/scenario_models.py
DEFAULT_SCENARIO_CONFIGS["new_scenario"] = {
    "id": "new_scenario",
    "name": "新场景名称",
    "description": "场景描述",
    "ui_config": {
        "theme_color": "#10B981",
        "welcome_title": "新场景助手",
        "welcome_message": "欢迎使用..."
    },
    "preset_questions": [
        "问题1",
        "问题2"
    ],
    "document_types": [
        "文档类型1",
        "文档类型2"
    ],
    "prompt_templates": {
        "system": "你是专业的...",
        "user": "基于以下文档..."
    }
}
```

2. **更新前端场景列表**:
```typescript
// frontend-next/contexts/scenario-context.tsx
const defaultScenarios = [
  {
    id: 'tender',
    name: '招投标',
    // ...
  },
  {
    id: 'new_scenario',
    name: '新场景名称',
    // ...
  }
];
```

3. **更新路由代理关键词库**:
```python
# src/agents/routing_agent.py
self.keyword_library = {
    "new_scenario": {
        "category1": ["关键词1", "关键词2"],
        "category2": ["关键词3", "关键词4"]
    }
}
```

---

## 4. 性能调优参数

### 4.1 检索性能

```python
# config.py 或运行时配置
RETRIEVAL_CONFIG = {
    "bm25_top_k": 15,        # BM25初筛数量
    "vector_top_k": 15,      # 向量检索数量
    "hybrid_top_k": 10,      # 混合检索最终数量
    "min_similarity": 0.5,   # 最小相似度
    "use_cache": True,       # 启用缓存
}
```

---

### 4.2 LLM调用优化

```python
LLM_CONFIG = {
    "temperature": 0.3,      # 温度（0-1），越低越确定
    "max_tokens": 1000,      # 最大生成Token数
    "top_p": 0.9,            # 核采样参数
    "timeout": 30,           # 超时时间（秒）
    "max_retries": 3,        # 最大重试次数
}
```

**模型选择策略**:
```python
def select_model(question: str, chunks: List[Dict]) -> str:
    """根据问题复杂度选择模型"""

    # 简单问题（有明确答案）
    if len(chunks) > 0 and is_simple_question(question):
        return "qwen-turbo-latest"  # 快速、便宜

    # 复杂问题（需要推理）
    if requires_reasoning(question):
        return "qwen-max"  # 准确、昂贵

    # 默认
    return "qwen-plus"  # 平衡
```

---

### 4.3 批处理配置

```python
BATCH_CONFIG = {
    "embedding_batch_size": 10,   # 嵌入批处理大小
    "max_concurrent_requests": 5,  # 最大并发请求数
    "batch_timeout": 60,           # 批处理超时（秒）
}
```

---

### 4.4 Token控制

```python
TOKEN_CONFIG = {
    "max_context_tokens": 8000,    # 最大上下文Token
    "target_context_tokens": 2000,  # 目标上下文Token
    "max_answer_tokens": 1000,      # 最大答案Token
    "reserve_tokens": 500,          # 预留Token（用于提示词）
}
```

---

## 5. 缓存配置

### 5.1 缓存策略

```python
CACHE_CONFIG = {
    # 精确缓存
    "exact_cache": {
        "enabled": True,
        "max_size": 1000,
        "ttl_days": 7,
        "eviction_policy": "LRU"  # LRU, LFU, FIFO
    },

    # 语义缓存
    "semantic_cache": {
        "enabled": True,
        "max_size": 500,
        "ttl_days": 3,
        "threshold": 0.95,
        "use_faiss": False  # 是否使用FAISS加速
    },

    # 缓存预热
    "warmup": {
        "enabled": True,
        "questions_file": "data/common_questions.json"
    }
}
```

---

### 5.2 缓存预热

**配置文件**: `data/common_questions.json`

```json
[
  {
    "question": "项目预算是多少？",
    "answer": "...",
    "confidence": 0.9
  },
  {
    "question": "截止日期是什么时候？",
    "answer": "...",
    "confidence": 0.85
  }
]
```

**预热代码**:
```python
from src.cache.smart_cache import SmartCache
import json

cache = SmartCache()

# 加载常见问题
with open("data/common_questions.json") as f:
    common_qa = json.load(f)

# 预热缓存
for qa in common_qa:
    cache.set(
        question=qa["question"],
        answer=qa,
        use_semantic=True
    )

print(f"✅ 缓存预热完成，加载 {len(common_qa)} 个问题")
```

---

## 6. 数据库配置

### 6.1 SQLite配置

**位置**: `backend/database.py`

```python
DATABASE_URL = "sqlite:///data/stock_data/databases/stock_rag.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_timeout=30,        # 连接超时（秒）
    pool_recycle=3600       # 连接回收时间（秒）
)
```

---

### 6.2 索引优化

```sql
-- 为常用查询创建索引
CREATE INDEX IF NOT EXISTS idx_documents_scenario
ON documents(scenario_id);

CREATE INDEX IF NOT EXISTS idx_documents_status
ON documents(status);

CREATE INDEX IF NOT EXISTS idx_documents_created
ON documents(created_at);

-- 复合索引
CREATE INDEX IF NOT EXISTS idx_documents_scenario_status
ON documents(scenario_id, status);
```

---

## 📊 推荐配置

### 开发环境

```python
# 快速迭代，低成本
CONFIG = {
    "llm_model": "qwen-turbo-latest",
    "cache_enabled": True,
    "cache_max_size": 100,
    "retrieval_top_k": 5,
    "target_tokens": 1000,
    "log_level": "DEBUG"
}
```

---

### 生产环境

```python
# 高性能，高准确性
CONFIG = {
    "llm_model": "qwen-plus",
    "cache_enabled": True,
    "cache_max_size": 5000,
    "retrieval_top_k": 10,
    "target_tokens": 2000,
    "log_level": "INFO",
    "enable_monitoring": True,
    "enable_verification": True
}
```

---

## 🔧 配置文件示例

**完整配置文件**: `config/production.yaml`

```yaml
# API配置
api:
  provider: dashscope
  timeout: 30
  max_retries: 3

# LLM配置
llm:
  default_model: qwen-plus
  temperature: 0.3
  max_tokens: 1000

# 检索配置
retrieval:
  bm25_weight: 0.5
  vector_weight: 0.5
  top_k: 10
  min_similarity: 0.5

# 缓存配置
cache:
  enabled: true
  max_size: 5000
  exact_ttl_days: 7
  semantic_ttl_days: 3
  semantic_threshold: 0.95

# 性能配置
performance:
  max_concurrent_requests: 10
  batch_size: 10
  target_tokens: 2000

# 日志配置
logging:
  level: INFO
  file: logs/system.log
  max_size: 100MB
  backup_count: 10
```

---

**文档版本**: v1.0
**最后更新**: 2025-09-30
**维护团队**: Agentic RAG 开发团队

