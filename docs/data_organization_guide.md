# 📂 数据组织规范指南

## 🎯 目录结构说明

```
data/stock_data/
├── pdf_reports/           # 原始PDF投研报告存储
├── databases/            # 数据库文件存储
│   ├── chunked_reports/  # 分块后的JSON文件
│   └── vector_dbs/       # FAISS向量数据库文件
├── debug_data/           # 调试和中间数据
│   ├── parsed_reports/   # PDF解析后的JSON文件
│   ├── merged_reports/   # 合并处理后的文件
│   └── reports_markdown/ # Markdown格式的报告
├── questions.json        # 问题清单文件
└── subset.csv           # 报告元数据文件
```

## 📝 文件命名规范

### PDF报告命名规范
```
{公司名称}_{机构名称}_{报告类型}_{发布日期}.pdf

示例：
- 中芯国际_华泰证券_深度研究_20240315.pdf
- 中芯国际_中原证券_季报点评_20240120.pdf
- 半导体行业_光大证券_行业分析_20240210.pdf
```

### JSON文件命名规范
```
{文件ID}_{处理步骤}.json

示例：
- smic_20240315_parsed.json      # 解析后文件
- smic_20240315_merged.json      # 合并后文件
- smic_20240315_chunked.json     # 分块后文件
```

### 向量数据库命名规范
```
{数据集名称}_{模型名称}_{日期}.faiss

示例：
- stock_reports_text_embedding_v1_20240322.faiss
- company_docs_dashscope_embedding_20240322.faiss
```

## 🏷️ 文件ID生成规则

### 基本格式
```
{公司代码}_{报告类型缩写}_{发布日期}_{序号}

公司代码映射：
- 中芯国际: smic
- 台积电: tsmc
- 长电科技: jcet

报告类型缩写：
- 深度研究: dr (depth_research)
- 季报点评: qr (quarterly_review)
- 年报点评: ar (annual_review)
- 行业分析: ia (industry_analysis)
- 公司调研: cv (company_visit)

示例：
- smic_dr_20240315_001
- smic_qr_20240120_001
- semiconductor_ia_20240210_001
```

## 📊 元数据字段说明

### subset.csv 字段定义

| 字段名 | 数据类型 | 必填 | 说明 |
|--------|----------|------|------|
| file_id | string | ✓ | 文件唯一标识符 |
| company_name | string | ✓ | 公司名称 |
| company_code | string | ○ | 股票代码 |
| report_type | string | ✓ | 报告类型 |
| publish_date | date | ✓ | 发布日期(YYYY-MM-DD) |
| analyst | string | ✓ | 分析师姓名 |
| institution | string | ✓ | 研究机构 |
| title | string | ✓ | 报告标题 |
| file_path | string | ✓ | 文件相对路径 |
| file_size | integer | ✓ | 文件大小(字节) |
| pages | integer | ✓ | 页数 |
| language | string | ✓ | 语言(中文/英文) |

### questions.json 字段定义

| 字段名 | 数据类型 | 必填 | 说明 |
|--------|----------|------|------|
| question_id | string | ✓ | 问题唯一标识符 |
| question_text | string | ✓ | 问题内容 |
| question_type | string | ✓ | 问题类型(string/multiple_choice等) |
| category | string | ○ | 问题分类 |
| difficulty | string | ○ | 难度等级(easy/medium/hard) |
| target_companies | array | ○ | 目标公司列表 |
| target_industries | array | ○ | 目标行业列表 |
| expected_answer_format | string | ○ | 预期答案格式 |

## 🔄 数据处理流程

### 1. 数据摄入阶段
```
PDF文件 → pdf_reports/
├── 文件重命名(按规范)
├── 元数据提取
└── subset.csv更新
```

### 2. 解析阶段
```
pdf_reports/ → debug_data/parsed_reports/
├── MinerU PDF解析
├── 结构化数据提取
└── JSON格式存储
```

### 3. 预处理阶段
```
parsed_reports/ → debug_data/merged_reports/
├── 多文档合并
├── 数据清洗
└── 格式标准化
```

### 4. 分块阶段
```
merged_reports/ → databases/chunked_reports/
├── 智能文本分块
├── 元数据保留
└── 索引构建
```

### 5. 向量化阶段
```
chunked_reports/ → databases/vector_dbs/
├── DashScope嵌入生成
├── FAISS索引构建
└── 检索准备
```

## 🔍 质量控制标准

### 文件质量检查
- ✅ PDF文件可正常打开
- ✅ 文件大小 > 100KB
- ✅ 页数 > 3页
- ✅ 包含有效文本内容
- ✅ 文件命名符合规范

### 元数据质量检查
- ✅ 所有必填字段完整
- ✅ 日期格式正确
- ✅ 公司名称标准化
- ✅ 报告类型规范化
- ✅ 文件路径有效

### 内容质量检查
- ✅ 文本提取完整性 > 90%
- ✅ 表格识别准确性 > 80%
- ✅ 格式保持一致性
- ✅ 特殊字符正确处理
- ✅ 分块长度适中(500-1500字符)

## 📈 版本控制策略

### 数据版本管理
```
v1.0.0: 初始数据集
v1.1.0: 新增数据批次
v1.1.1: 数据质量修复
v2.0.0: 重大结构变更
```

### 备份策略
- 🗄️ 每日增量备份
- 📦 每周完整备份
- 🔄 多副本存储
- ⚡ 快速恢复机制

### 数据安全
- 🔐 敏感信息脱敏
- 🛡️ 访问权限控制
- 📝 操作日志记录
- 🔍 定期完整性检查

---

## 📋 检查清单

在数据处理前，请确认：

- [ ] PDF文件命名符合规范
- [ ] subset.csv字段完整准确
- [ ] 目录结构正确创建
- [ ] 处理脚本配置正确
- [ ] 备份机制已启用
- [ ] 质量检查标准明确

在数据处理后，请验证：

- [ ] 所有步骤成功完成
- [ ] 输出文件格式正确
- [ ] 数据质量满足标准
- [ ] 索引构建成功
- [ ] 检索功能正常
- [ ] 错误日志为空
