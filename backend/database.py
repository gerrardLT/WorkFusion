"""
数据库连接和会话管理
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 使用环境变量或默认数据库URL，避免循环导入
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/stock_data/databases/stock_rag.db")

# 创建数据库引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        echo=False  # 设置为True可以看到SQL语句
    )

    # 启用SQLite外键约束
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
else:
    # PostgreSQL或其他数据库配置
    engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """获取数据库会话（同步版本）"""
    return SessionLocal()


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)


def get_engine():
    """获取数据库引擎"""
    return engine


def check_database_connection() -> bool:
    """检查数据库连接"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False


def init_database():
    """初始化数据库"""
    try:
        # 检查连接
        if not check_database_connection():
            print("[ERROR] 数据库连接失败")
            return False

        # 创建表（如果不存在）
        create_tables()
        print("[OK] 数据库初始化完成")
        return True

    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        return False

