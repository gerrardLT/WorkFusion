# Agentic RAG 系统故障排查手册

## 📋 目录

- [1. 系统启动问题](#1-系统启动问题)
- [2. 文档处理问题](#2-文档处理问题)
- [3. 检索问题](#3-检索问题)
- [4. API调用问题](#4-api调用问题)
- [5. 缓存问题](#5-缓存问题)
- [6. 性能问题](#6-性能问题)
- [7. 数据库问题](#7-数据库问题)
- [8. 前端问题](#8-前端问题)
- [9. 常见错误码](#9-常见错误码)
- [10. 调试技巧](#10-调试技巧)

---

## 1. 系统启动问题

### 1.1 后端启动失败

**症状**:
```
ERROR: ModuleNotFoundError: No module named 'xxx'
```

**原因**: 依赖包未安装

**解决方案**:
```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import faiss; print('FAISS OK')"
python -c "import dashscope; print('DashScope OK')"
```

---

### 1.2 API密钥错误

**症状**:
```
ERROR: Invalid API key
```

**原因**: DashScope API密钥未配置或无效

**解决方案**:
```bash
# 1. 检查 .env 文件
cat .env | grep DASHSCOPE_API_KEY

# 2. 设置环境变量
export DASHSCOPE_API_KEY=your_api_key_here  # Linux/Mac
$env:DASHSCOPE_API_KEY="your_api_key_here"  # Windows PowerShell

# 3. 验证API密钥
python -c "from config import get_settings; print(get_settings().dashscope_api_key)"
```

---

### 1.3 数据库连接失败

**症状**:
```
ERROR: Unable to open database file
```

**原因**: 数据库文件不存在或权限不足

**解决方案**:
```bash
# 1. 检查数据库文件
ls -la data/stock_data/databases/stock_rag.db

# 2. 创建数据库目录
mkdir -p data/stock_data/databases

# 3. 初始化数据库
python -c "from backend.database import init_db; init_db()"

# 4. 检查权限
chmod 644 data/stock_data/databases/stock_rag.db  # Linux/Mac
```

---

### 1.4 端口被占用

**症状**:
```
ERROR: [Errno 48] Address already in use
```

**原因**: 端口8000或3005已被占用

**解决方案**:
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# 或者使用其他端口
uvicorn backend.main_multi_scenario:app --port 8001
```

---

## 2. 文档处理问题

### 2.1 PDF解析失败

**症状**:
```
WARNING: MinerU (magic-pdf) not available, using fallback PDF parsing
```

**原因**: MinerU未正确安装

**解决方案**:
```bash
# 1. 检查MinerU命令
which magic-pdf  # Linux/Mac
where magic-pdf  # Windows

# 2. 安装MinerU
pip install mineru[core]

# 3. 验证安装
magic-pdf --version

# 4. 如果仍然失败，检查备用解析器
python -c "import fitz; print('PyMuPDF OK')"
python -c "import pdfplumber; print('pdfplumber OK')"
```

---

### 2.2 FAISS向量化失败（中文路径）

**症状**:
```
ERROR: Error in faiss::FileIOWriter: Illegal byte sequence
```

**原因**: FAISS无法处理包含中文的文件名或路径

**解决方案**:
```python
# 已在 src/ingestion.py 中实现
# 使用MD5 hash生成安全的临时文件名

import hashlib
import tempfile
from pathlib import Path

# 生成安全文件名
safe_filename = hashlib.md5(file_id.encode()).hexdigest()
temp_dir = Path(tempfile.mkdtemp(prefix="faiss_temp_"))
temp_faiss_file = temp_dir / f"{safe_filename}_vector.faiss"

# 写入临时文件
faiss.write_index(index, str(temp_faiss_file))

# 复制到最终位置
shutil.copy2(temp_faiss_file, final_path)
```

**验证**:
```bash
# 检查向量文件是否生成
ls -la data/stock_data/databases/vector_dbs/
```

---

### 2.3 文档分块失败

**症状**:
```
ERROR: 'pages' key not found in parsed report
```

**原因**: PDF解析结果格式不正确

**解决方案**:
```python
# 检查解析结果格式
import json
with open("data/debug_data/parsed_reports/xxx_parsed.json") as f:
    data = json.load(f)
    print(data.keys())  # 应该包含 'pages'

# 正确的格式
{
    "file_id": "...",
    "pages": [
        {
            "page_number": 1,
            "text": "页面内容...",
            "metadata": {...}
        }
    ]
}
```

---

### 2.4 BM25索引构建失败

**症状**:
```
ERROR: BM25 index creation failed
```

**原因**: 文本块为空或分词失败

**解决方案**:
```python
# 1. 检查文本块
from src.ingestion import IngestionPipeline

pipeline = IngestionPipeline()
chunks = ["测试文本1", "测试文本2"]

# 2. 测试分词
bm25_index = pipeline.create_bm25_index(chunks)
print(f"索引创建成功: {bm25_index is not None}")

# 3. 检查索引文件
import os
bm25_files = os.listdir("data/stock_data/databases/bm25/")
print(f"BM25索引文件: {bm25_files}")
```

---

## 3. 检索问题

### 3.1 检索无结果

**症状**:
```
WARNING: No documents found for query
```

**原因**: 索引文件不存在或为空

**解决方案**:
```python
# 1. 检查索引文件
import os
from pathlib import Path

bm25_dir = Path("data/stock_data/databases/bm25/")
vector_dir = Path("data/stock_data/databases/vector_dbs/")

print(f"BM25索引: {list(bm25_dir.glob('*.pkl'))}")
print(f"FAISS索引: {list(vector_dir.glob('*.faiss'))}")

# 2. 重建索引
from src.pipeline import Pipeline, RunConfig

pipeline = Pipeline(
    root_path=Path("data/stock_data"),
    scenario_id="tender",
    run_config=RunConfig()
)

result = pipeline.prepare_documents(force_rebuild=True)
print(f"文档准备结果: {result}")
```

---

### 3.2 检索速度慢

**症状**: 检索耗时 > 5秒

**原因**: 索引未预加载或文档数量过多

**解决方案**:
```python
# 1. 启用缓存
from src.cache.smart_cache import SmartCache

cache = SmartCache(max_size=1000)
cached_result = cache.get("查询问题")

# 2. 减少检索数量
from src.retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(scenario_id="tender")
results = retriever.retrieve(
    question="...",
    top_k=5  # 减少到5个
)

# 3. 使用查询向量缓存
query_vector_cache = {}

def get_cached_embedding(query: str):
    if query in query_vector_cache:
        return query_vector_cache[query]

    embedding = api_processor.get_embeddings([query])[0]
    query_vector_cache[query] = embedding
    return embedding
```

---

### 3.3 检索结果不相关

**症状**: 返回的文档与问题无关

**原因**: 权重配置不合理或阈值过低

**解决方案**:
```python
# 1. 调整权重
retriever.retrieve(
    question="...",
    bm25_weight=0.6,  # 提高关键词权重
    vector_weight=0.4
)

# 2. 提高相似度阈值
vector_retriever.search(
    query="...",
    min_similarity=0.6  # 提高到0.6
)

# 3. 使用智能路由
from src.agents.routing_agent import RoutingAgent

agent = RoutingAgent(scenario_id="tender")
result = agent.route_documents(
    chunks=candidates,
    question="...",
    top_k=5
)
```

---

## 4. API调用问题

### 4.1 API调用超时

**症状**:
```
ERROR: Request timeout after 30 seconds
```

**原因**: 网络问题或API服务繁忙

**解决方案**:
```python
# 1. 增加超时时间
from api_requests import APIProcessor

api_processor = APIProcessor(
    provider="dashscope",
    timeout=60  # 增加到60秒
)

# 2. 启用重试机制
import time

def api_call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            print(f"重试 {i+1}/{max_retries}...")
            time.sleep(2 ** i)  # 指数退避

# 3. 检查网络连接
import requests
response = requests.get("https://dashscope.aliyuncs.com")
print(f"API服务状态: {response.status_code}")
```

---

### 4.2 API配额超限

**症状**:
```
ERROR: Rate limit exceeded
```

**原因**: API调用频率过高

**解决方案**:
```python
# 1. 启用智能延迟
import time

def rate_limited_call(func, delay=0.5):
    result = func()
    time.sleep(delay)
    return result

# 2. 使用批处理
texts = ["文本1", "文本2", "文本3"]
embeddings = api_processor.get_embeddings(texts)  # 批量调用

# 3. 启用缓存减少调用
from src.cache.smart_cache import SmartCache
cache = SmartCache()

# 先检查缓存
result = cache.get(question)
if not result:
    # 缓存未命中，调用API
    result = process_question(question)
    cache.set(question, result)
```

---

### 4.3 嵌入向量生成失败

**症状**:
```
ERROR: Failed to generate embeddings
```

**原因**: 文本过长或格式错误

**解决方案**:
```python
# 1. 检查文本长度
def check_text_length(text: str, max_length: int = 8000):
    if len(text) > max_length:
        print(f"警告: 文本过长 ({len(text)} 字符)")
        return text[:max_length]
    return text

# 2. 清理文本
def clean_text(text: str) -> str:
    # 移除特殊字符
    text = text.replace('\x00', '')
    # 移除过多空白
    text = ' '.join(text.split())
    return text

# 3. 分批处理
def batch_embed(texts: List[str], batch_size: int = 10):
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = api_processor.get_embeddings(batch)
        results.extend(embeddings)
    return results
```

---

## 5. 缓存问题

### 5.1 缓存未命中

**症状**: 缓存命中率 < 10%

**原因**: 缓存配置不合理或问题变化大

**解决方案**:
```python
# 1. 降低语义阈值
cache = SmartCache(
    semantic_threshold=0.90  # 从0.95降低到0.90
)

# 2. 增加缓存大小
cache = SmartCache(
    max_size=5000  # 增加到5000
)

# 3. 延长TTL
cache = SmartCache(
    exact_ttl_days=14,    # 增加到14天
    semantic_ttl_days=7   # 增加到7天
)

# 4. 缓存预热
common_questions = [
    "项目预算是多少？",
    "截止日期是什么时候？"
]

for q in common_questions:
    result = process_question(q)
    cache.set(q, result, use_semantic=True)
```

---

### 5.2 缓存占用内存过大

**症状**: 系统内存占用 > 2GB

**原因**: 缓存条目过多或单条目过大

**解决方案**:
```python
# 1. 减小缓存大小
cache = SmartCache(max_size=500)

# 2. 只缓存必要字段
def cache_answer(question: str, result: Dict):
    # 只缓存核心字段
    cached_data = {
        "answer": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"][:3]  # 只缓存前3个来源
    }
    cache.set(question, cached_data)

# 3. 定期清理
def cleanup_cache():
    stats = cache.get_stats()
    if stats["total_cache_size"] > 1000:
        # 清空缓存
        cache = SmartCache()
```

---

### 5.3 语义缓存速度慢

**症状**: 语义缓存查询 > 1秒

**原因**: 遍历所有缓存项计算相似度

**解决方案**:
```python
# 使用FAISS加速语义缓存
import faiss
import numpy as np

class FastSemanticCache:
    def __init__(self):
        self.dimension = 1536
        self.index = faiss.IndexFlatIP(self.dimension)
        self.cache_data = []

    def add(self, question: str, answer: Dict):
        # 获取问题向量
        embedding = get_embedding(question)

        # 添加到FAISS索引
        self.index.add(np.array([embedding]))
        self.cache_data.append({
            "question": question,
            "answer": answer
        })

    def search(self, question: str, threshold: float = 0.95):
        embedding = get_embedding(question)

        # FAISS快速搜索
        D, I = self.index.search(np.array([embedding]), k=1)

        if D[0][0] > threshold:
            return self.cache_data[I[0][0]]["answer"]
        return None
```

---

## 6. 性能问题

### 6.1 响应时间过长

**症状**: 平均响应时间 > 10秒

**原因**: 检索、LLM调用或验证环节耗时过长

**诊断**:
```python
import time

def profile_pipeline(question: str):
    start = time.time()

    # 1. 检索
    t1 = time.time()
    chunks = retriever.retrieve(question)
    retrieval_time = time.time() - t1

    # 2. 路由
    t2 = time.time()
    routed = agent.route_documents(chunks, question)
    routing_time = time.time() - t2

    # 3. 生成答案
    t3 = time.time()
    answer = generate_answer(question, routed)
    generation_time = time.time() - t3

    # 4. 验证
    t4 = time.time()
    verified = verifier.verify_answer(answer, routed, question)
    verification_time = time.time() - t4

    total_time = time.time() - start

    print(f"总耗时: {total_time:.2f}秒")
    print(f"  检索: {retrieval_time:.2f}秒 ({retrieval_time/total_time*100:.1f}%)")
    print(f"  路由: {routing_time:.2f}秒 ({routing_time/total_time*100:.1f}%)")
    print(f"  生成: {generation_time:.2f}秒 ({generation_time/total_time*100:.1f}%)")
    print(f"  验证: {verification_time:.2f}秒 ({verification_time/total_time*100:.1f}%)")
```

**优化方案**:
```python
# 1. 启用缓存
cache = SmartCache(max_size=1000)

# 2. 减少检索数量
retriever.retrieve(question, top_k=5)

# 3. 使用更快的模型
api_processor.llm_model = "qwen-turbo-latest"

# 4. 跳过验证（如果可接受）
skip_verification = True
```

---

### 6.2 并发性能差

**症状**: 并发请求 > 10 时响应变慢

**原因**: 单线程处理，无并发优化

**解决方案**:
```python
# 1. 使用异步处理
import asyncio

async def process_question_async(question: str):
    # 异步检索
    chunks = await retriever.retrieve_async(question)

    # 异步生成答案
    answer = await generate_answer_async(question, chunks)

    return answer

# 2. 使用线程池
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

def process_batch(questions: List[str]):
    futures = [
        executor.submit(process_question, q)
        for q in questions
    ]

    results = [f.result() for f in futures]
    return results

# 3. 使用进程池（CPU密集型）
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(process_question, questions)
```

---

### 6.3 内存占用过高

**症状**: 系统内存 > 4GB

**原因**: 索引未释放或缓存过大

**解决方案**:
```python
# 1. 定期释放内存
import gc

def cleanup_memory():
    gc.collect()

# 2. 使用内存映射（FAISS）
index = faiss.read_index("index.faiss", faiss.IO_FLAG_MMAP)

# 3. 限制缓存大小
cache = SmartCache(max_size=500)

# 4. 监控内存使用
import psutil

def check_memory():
    process = psutil.Process()
    mem_info = process.memory_info()
    print(f"内存使用: {mem_info.rss / 1024 / 1024:.2f} MB")
```

---

## 7. 数据库问题

### 7.1 数据库锁定

**症状**:
```
ERROR: database is locked
```

**原因**: 多个进程同时写入SQLite

**解决方案**:
```python
# 1. 增加超时时间
from sqlalchemy import create_engine

engine = create_engine(
    "sqlite:///data/stock_rag.db",
    connect_args={"timeout": 30}
)

# 2. 使用WAL模式
import sqlite3
conn = sqlite3.connect("data/stock_rag.db")
conn.execute("PRAGMA journal_mode=WAL")

# 3. 使用连接池
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "sqlite:///data/stock_rag.db",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

---

### 7.2 数据库损坏

**症状**:
```
ERROR: database disk image is malformed
```

**原因**: 数据库文件损坏

**解决方案**:
```bash
# 1. 备份数据库
cp data/stock_rag.db data/stock_rag.db.backup

# 2. 尝试修复
sqlite3 data/stock_rag.db "PRAGMA integrity_check;"

# 3. 导出数据
sqlite3 data/stock_rag.db ".dump" > backup.sql

# 4. 重建数据库
rm data/stock_rag.db
sqlite3 data/stock_rag.db < backup.sql

# 5. 如果无法修复，从备份恢复
cp data/stock_rag.db.backup data/stock_rag.db
```

---

## 8. 前端问题

### 8.1 场景切换不生效

**症状**: 切换场景后UI未更新

**原因**: 前端状态未同步

**解决方案**:
```typescript
// 1. 清除浏览器缓存
// Chrome: Ctrl+Shift+Delete

// 2. 重启前端服务
npm run dev

// 3. 检查场景配置
const { currentScenario } = useScenario();
console.log('当前场景:', currentScenario);

// 4. 强制刷新
window.location.reload();
```

---

### 8.2 文件上传失败

**症状**: 上传按钮无响应或报错

**原因**: 文件大小超限或格式不支持

**解决方案**:
```typescript
// 1. 检查文件大小
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

if (file.size > MAX_FILE_SIZE) {
  alert('文件过大，请选择小于10MB的文件');
  return;
}

// 2. 检查文件类型
const ALLOWED_TYPES = ['.pdf', '.txt', '.md'];
const fileExt = file.name.substring(file.name.lastIndexOf('.'));

if (!ALLOWED_TYPES.includes(fileExt)) {
  alert('不支持的文件类型');
  return;
}

// 3. 检查后端接口
fetch('http://localhost:8000/api/v2/upload', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error('上传失败:', err));
```

---

## 9. 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `PIPELINE_NOT_READY` | Pipeline未就绪 | 调用 `prepare_documents()` |
| `NO_DOCUMENTS_FOUND` | 未找到文档 | 检查索引文件 |
| `API_CALL_FAILED` | API调用失败 | 检查网络和密钥 |
| `CACHE_ERROR` | 缓存错误 | 清空缓存 |
| `VERIFICATION_FAILED` | 验证失败 | 检查源文档 |
| `DATABASE_LOCKED` | 数据库锁定 | 增加超时时间 |
| `INVALID_SCENARIO` | 无效场景ID | 检查场景配置 |
| `EMBEDDING_FAILED` | 向量生成失败 | 检查文本格式 |

---

## 10. 调试技巧

### 10.1 启用详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 针对特定模块
logging.getLogger('src.retrieval').setLevel(logging.DEBUG)
logging.getLogger('src.agents').setLevel(logging.DEBUG)
```

---

### 10.2 使用调试断点

```python
# 在关键位置添加断点
import pdb

def process_question(question: str):
    # 检索
    chunks = retriever.retrieve(question)

    # 调试点
    pdb.set_trace()  # 程序会在这里暂停

    # 继续执行
    answer = generate_answer(question, chunks)
    return answer
```

---

### 10.3 性能分析

```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 执行代码
result = process_question("测试问题")

profiler.disable()

# 查看结果
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 打印前20个最耗时的函数
```

---

### 10.4 内存分析

```python
from memory_profiler import profile

@profile
def process_question(question: str):
    # 函数代码
    pass

# 运行时会显示每行代码的内存使用
```

---

## 📞 获取帮助

如果以上方法无法解决问题：

1. **查看日志**: `logs/system.log`
2. **检查文档**: `docs/` 目录下的所有文档
3. **运行测试**: `python tests/test_agentic_rag_integration.py`
4. **联系团队**: 提供详细的错误信息和日志

---

**文档版本**: v1.0
**最后更新**: 2025-09-30
**维护团队**: Agentic RAG 开发团队

