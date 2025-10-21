-- ============================================
-- 多场景AI知识问答系统数据库表结构
-- 支持投研、招投标场景的通用数据库设计
-- ============================================

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- ============================================
-- 场景管理表
-- ============================================

-- 场景配置表
CREATE TABLE IF NOT EXISTS scenarios (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    config JSON NOT NULL,
    status TEXT CHECK(status IN ('active', 'inactive')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建场景更新触发器
CREATE TRIGGER IF NOT EXISTS scenarios_update_timestamp
    AFTER UPDATE ON scenarios
BEGIN
    UPDATE scenarios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 文档类型表
CREATE TABLE IF NOT EXISTS document_types (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    file_extensions JSON, -- [".pdf", ".docx", ".txt"]
    processing_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

-- ============================================
-- 通用文档管理表
-- ============================================

-- 文档元数据表 (通用化改造)
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    document_type_id VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    pages INTEGER,
    language VARCHAR(10) DEFAULT 'zh',

    -- 通用元数据 (JSON格式，支持各场景自定义字段)
    metadata JSON,

    -- 处理状态
    status TEXT CHECK(status IN ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',
    processed_at TIMESTAMP NULL,

    -- 质量评分
    quality_score DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (document_type_id) REFERENCES document_types(id) ON DELETE SET NULL
);

-- 创建文档表索引
CREATE INDEX IF NOT EXISTS idx_documents_scenario_status ON documents(scenario_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- 创建文档更新触发器
CREATE TRIGGER IF NOT EXISTS documents_update_timestamp
    AFTER UPDATE ON documents
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- 会话管理表
-- ============================================

-- 会话表 (增加场景支持)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50), -- 为未来用户系统预留
    title VARCHAR(255) NOT NULL,

    -- 会话配置
    config JSON, -- 场景特定配置

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

-- 创建会话表索引
CREATE INDEX IF NOT EXISTS idx_chat_sessions_scenario_user ON chat_sessions(scenario_id, user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- 创建会话更新触发器
CREATE TRIGGER IF NOT EXISTS chat_sessions_update_timestamp
    AFTER UPDATE ON chat_sessions
BEGIN
    UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,

    -- 消息元数据
    metadata JSON, -- 置信度、来源、处理时间等

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- 创建消息表索引
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- ============================================
-- 文档块和向量存储表
-- ============================================

-- 文档分块表
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- 位置信息
    page_number INTEGER,
    start_position INTEGER,
    end_position INTEGER,

    -- 语义信息
    semantic_tags JSON,
    importance_score DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 创建文档块表索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_chunk ON document_chunks(document_id, chunk_index);

-- 向量索引表
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id VARCHAR(50) PRIMARY KEY,
    chunk_id VARCHAR(50) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    vector_index_path VARCHAR(500), -- FAISS索引文件路径

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE,
    UNIQUE(chunk_id, embedding_model)
);

-- ============================================
-- 初始化默认场景数据
-- ============================================

-- 插入投研场景
INSERT OR REPLACE INTO scenarios (id, name, description, config, status) VALUES (
    'investment',
    '投资研究',
    '专业的投资分析和财务研究',
    json('{
        "theme": {
            "primaryColor": "blue",
            "gradientFrom": "from-blue-600",
            "gradientTo": "to-purple-600",
            "iconColor": "text-blue-600"
        },
        "ui": {
            "welcomeTitle": "欢迎使用投研RAG智能问答",
            "welcomeMessage": "我是您的专业AI投研分析师，擅长解读财务数据、市场趋势和投资机会",
            "placeholderText": "请输入您的投资研究问题...",
            "uploadAreaTitle": "上传投研文档",
            "uploadAreaDescription": "支持上传研究报告、财务报表等文档"
        },
        "presetQuestions": [
            "中芯国际的最新财务状况如何？",
            "比亚迪和宁德时代在电池技术上的差异",
            "新能源汽车行业的发展趋势",
            "分析一下最新的财务报表"
        ],
        "documentTypes": [
            {
                "id": "research_report",
                "name": "研究报告",
                "extensions": [".pdf", ".docx"],
                "maxSize": 52428800
            }
        ],
        "prompt_templates": {
            "system": "你是一位专业的投资分析师，擅长分析财务数据、市场趋势和投资机会。请基于提供的文档内容，用专业、客观的语言回答用户的投资研究问题。",
            "welcome": "我是您的专业AI投研分析师，可以帮助您分析投资研究报告。"
        }
    }'),
    'active'
);

-- 插入招投标场景
INSERT OR REPLACE INTO scenarios (id, name, description, config, status) VALUES (
    'tender',
    '招投标',
    '招标文件分析和投标方案优化',
    json('{
        "theme": {
            "primaryColor": "green",
            "gradientFrom": "from-green-600",
            "gradientTo": "to-teal-600",
            "iconColor": "text-green-600"
        },
        "ui": {
            "welcomeTitle": "欢迎使用招投标智能助手",
            "welcomeMessage": "我是您的专业招投标分析师，帮助您解读招标文件、分析投标要求",
            "placeholderText": "请输入您的招投标相关问题...",
            "uploadAreaTitle": "上传招投标文档",
            "uploadAreaDescription": "支持上传招标文件、投标书、技术方案等文档"
        },
        "presetQuestions": [
            "这个招标项目的主要技术要求是什么？",
            "投标截止时间和开标时间是什么时候？",
            "参与投标需要哪些资质证书？",
            "项目预算范围是多少？"
        ],
        "documentTypes": [
            {
                "id": "tender_document",
                "name": "招标文件",
                "extensions": [".pdf", ".doc", ".docx"],
                "maxSize": 104857600
            }
        ],
        "prompt_templates": {
            "system": "你是一位专业的招投标顾问，擅长解读招标文件、分析投标要求和合规性检查。请基于提供的文档内容，用专业、准确的语言回答用户的招投标相关问题。",
            "welcome": "我是您的专业招投标分析师，可以帮助您解读招标文件和分析投标要求。"
        }
    }'),
    'active'
);

-- 插入投研场景的文档类型
INSERT OR REPLACE INTO document_types (id, scenario_id, name, description, file_extensions, processing_config) VALUES (
    'investment_research_report',
    'investment',
    '投研报告',
    '包括深度研究、季报点评、年报分析等投资研究报告',
    json('[".pdf", ".docx"]'),
    json('{
        "maxFileSize": 52428800,
        "allowedFormats": ["pdf", "docx"],
        "extractionRules": {
            "company_name": "extract_company_name",
            "analyst": "extract_analyst",
            "report_type": "classify_report_type",
            "publish_date": "extract_publish_date",
            "investment_rating": "extract_investment_rating",
            "target_price": "extract_target_price"
        }
    }')
);

-- 插入招投标场景的文档类型
INSERT OR REPLACE INTO document_types (id, scenario_id, name, description, file_extensions, processing_config) VALUES (
    'tender_document',
    'tender',
    '招标文件',
    '包括招标公告、技术规范、投标须知等招投标相关文档',
    json('[".pdf", ".doc", ".docx"]'),
    json('{
        "maxFileSize": 104857600,
        "allowedFormats": ["pdf", "doc", "docx"],
        "extractionRules": {
            "tender_number": "extract_tender_number",
            "tender_title": "extract_tender_title",
            "submission_deadline": "extract_deadline",
            "budget_range": "extract_budget",
            "qualification_requirements": "extract_qualifications"
        }
    }')
);

-- ============================================
-- 创建视图和查询优化
-- ============================================

-- 场景统计视图
CREATE VIEW IF NOT EXISTS scenario_stats AS
SELECT
    s.id,
    s.name,
    s.status,
    COUNT(DISTINCT d.id) as document_count,
    COUNT(DISTINCT cs.id) as session_count,
    COUNT(DISTINCT cm.id) as message_count,
    s.created_at,
    s.updated_at
FROM scenarios s
LEFT JOIN documents d ON s.id = d.scenario_id
LEFT JOIN chat_sessions cs ON s.id = cs.scenario_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY s.id, s.name, s.status, s.created_at, s.updated_at;

-- 会话消息统计视图
CREATE VIEW IF NOT EXISTS session_message_stats AS
SELECT
    cs.id as session_id,
    cs.title,
    cs.scenario_id,
    COUNT(cm.id) as message_count,
    MAX(cm.created_at) as last_message_at,
    cs.created_at,
    cs.updated_at
FROM chat_sessions cs
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY cs.id, cs.title, cs.scenario_id, cs.created_at, cs.updated_at;

-- ============================================
-- 数据完整性检查
-- ============================================

-- 检查场景配置的JSON格式是否有效
CREATE TRIGGER IF NOT EXISTS validate_scenario_config
    BEFORE INSERT ON scenarios
BEGIN
    SELECT
        CASE
            WHEN json_valid(NEW.config) = 0 THEN
                RAISE(ABORT, 'Invalid JSON in scenario config')
        END;
END;

-- 检查文档元数据的JSON格式是否有效
CREATE TRIGGER IF NOT EXISTS validate_document_metadata
    BEFORE INSERT ON documents
BEGIN
    SELECT
        CASE
            WHEN NEW.metadata IS NOT NULL AND json_valid(NEW.metadata) = 0 THEN
                RAISE(ABORT, 'Invalid JSON in document metadata')
        END;
END;

-- ============================================
-- 数据库版本信息
-- ============================================

-- 创建版本表
CREATE TABLE IF NOT EXISTS db_version (
    version VARCHAR(10) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入当前版本信息
INSERT OR REPLACE INTO db_version (version, description) VALUES (
    '1.0.0',
    'Initial multi-scenario database schema with investment and tender scenarios'
);

-- 输出创建完成信息
-- SELECT 'Multi-scenario database schema created successfully!' as result;

