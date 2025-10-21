"""
配置管理模块
管理DashScope API密钥、模型配置和系统参数
"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DashScopeConfig(BaseSettings):
    """DashScope API配置"""

    api_key: str = Field(..., env="DASHSCOPE_API_KEY")
    llm_model: str = Field("qwen-turbo-latest", env="LLM_MODEL")
    embedding_model: str = Field("text-embedding-v3", env="EMBEDDING_MODEL")

    class Config:
        env_prefix = "DASHSCOPE_"


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    url: str = Field(
        "sqlite:///./data/stock_data/databases/stock_rag.db", env="DATABASE_URL"
    )

    class Config:
        env_prefix = "DATABASE_"


class APIConfig(BaseSettings):
    """API服务配置"""

    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="DEBUG")

    class Config:
        env_prefix = "API_"


class RetrievalConfig(BaseSettings):
    """检索配置"""

    max_retrieved_docs: int = Field(20, env="MAX_RETRIEVED_DOCS")
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")

    class Config:
        env_prefix = "RETRIEVAL_"


class RerankConfig(BaseSettings):
    """重排序配置"""

    rerank_top_k: int = Field(10, env="RERANK_TOP_K")
    enable_llm_rerank: bool = Field(True, env="ENABLE_LLM_RERANK")

    class Config:
        env_prefix = "RERANK_"


class PerformanceConfig(BaseSettings):
    """性能配置"""

    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    enable_cache: bool = Field(True, env="ENABLE_CACHE")
    cache_ttl: int = Field(3600, env="CACHE_TTL")

    class Config:
        env_prefix = "PERFORMANCE_"


class LogConfig(BaseSettings):
    """日志配置"""

    level: str = Field("INFO", env="LOG_LEVEL")
    file: str = Field("logs/app.log", env="LOG_FILE")

    class Config:
        env_prefix = "LOG_"


class FrontendConfig(BaseSettings):
    """前端配置"""

    url: str = Field("http://localhost:3000", env="FRONTEND_URL")
    cors_origins: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")

    class Config:
        env_prefix = "FRONTEND_"


class MultiScenarioConfig(BaseSettings):
    """多场景系统配置"""

    default_scenario: str = Field("investment", env="DEFAULT_SCENARIO")
    enable_scenario_switching: bool = Field(True, env="ENABLE_SCENARIO_SWITCHING")
    scenario_cache_ttl: int = Field(300, env="SCENARIO_CACHE_TTL")  # 5分钟

    class Config:
        env_prefix = "MULTI_SCENARIO_"


class Settings:
    """全局配置管理"""

    def __init__(self):
        self.dashscope = DashScopeConfig()
        self.database = DatabaseConfig()
        self.api = APIConfig()
        self.retrieval = RetrievalConfig()
        self.rerank = RerankConfig()
        self.performance = PerformanceConfig()
        self.log = LogConfig()
        self.frontend = FrontendConfig()
        self.multi_scenario = MultiScenarioConfig()

        # 项目路径
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "stock_data"
        self.pdf_dir = self.data_dir / "pdf_reports"
        self.db_dir = self.data_dir / "databases"
        self.debug_dir = self.data_dir / "debug_data"

        # 确保目录存在
        self._ensure_directories()

        # 初始化场景配置管理器
        self._init_scenario_manager()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.pdf_dir,
            self.db_dir,
            self.debug_dir,
            self.project_root / "logs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _init_scenario_manager(self):
        """初始化场景配置管理器"""
        try:
            from src.scenario_config_dir.scenario_config import init_scenario_config_manager

            # 获取数据库路径
            db_url = self.database.url
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
                if not db_path.startswith('/'):
                    # 相对路径，转换为绝对路径
                    db_path = str(self.project_root / db_path)
            else:
                # 默认SQLite路径
                db_path = str(self.db_dir / "stock_rag.db")

            # 初始化场景配置管理器
            self.scenario_manager = init_scenario_config_manager(
                database_path=db_path,
                cache_ttl=self.multi_scenario.scenario_cache_ttl
            )

        except Exception as e:
            print(f"⚠️ 初始化场景配置管理器失败: {str(e)}")
            self.scenario_manager = None

    def validate_dashscope_config(self) -> bool:
        """验证DashScope配置是否有效"""
        try:
            import dashscope

            dashscope.api_key = self.dashscope.api_key
            # 这里可以添加简单的API测试
            return True
        except Exception as e:
            print(f"DashScope配置验证失败: {e}")
            return False

    def get_model_config(self) -> dict:
        """获取模型配置字典"""
        return {
            "llm_model": self.dashscope.llm_model,
            "embedding_model": self.dashscope.embedding_model,
            "api_key": self.dashscope.api_key,
        }

    def get_retrieval_config(self) -> dict:
        """获取检索配置字典"""
        return {
            "max_retrieved_docs": self.retrieval.max_retrieved_docs,
            "chunk_size": self.retrieval.chunk_size,
            "chunk_overlap": self.retrieval.chunk_overlap,
            "rerank_top_k": self.rerank.rerank_top_k,
            "enable_llm_rerank": self.rerank.enable_llm_rerank,
        }

    def get_scenario_config(self, scenario_id: str = None):
        """获取场景配置"""
        if not scenario_id:
            scenario_id = self.multi_scenario.default_scenario

        if self.scenario_manager:
            return self.scenario_manager.get_scenario(scenario_id)
        return None

    def validate_scenario(self, scenario_id: str) -> bool:
        """验证场景是否有效"""
        if self.scenario_manager:
            return self.scenario_manager.validate_scenario(scenario_id)
        return scenario_id == self.multi_scenario.default_scenario


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取全局配置实例"""
    return settings
