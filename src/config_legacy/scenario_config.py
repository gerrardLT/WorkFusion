"""
多场景配置管理模块
管理场景配置的加载、缓存和验证
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 直接导入，避免相对导入问题
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.scenario_models import (
    ScenarioConfig, ScenarioConfigData, ScenarioStatus,
    DEFAULT_SCENARIO_CONFIGS
)


class ScenarioConfigManager:
    """场景配置管理器"""

    def __init__(self, database_path: str, cache_ttl: int = 300):
        """
        初始化场景配置管理器

        Args:
            database_path: 数据库文件路径
            cache_ttl: 缓存TTL（秒），默认5分钟
        """
        self.database_path = database_path
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, ScenarioConfig] = {}
        self._cache_timestamp: Optional[datetime] = None

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < timedelta(seconds=self.cache_ttl)

    def _load_from_database(self) -> Dict[str, ScenarioConfig]:
        """从数据库加载场景配置"""
        scenarios = {}

        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, name, description, config, status, created_at, updated_at
                    FROM scenarios
                    WHERE status = 'active'
                    ORDER BY created_at
                """)

                rows = cursor.fetchall()

                for row in rows:
                    try:
                        # 解析JSON配置
                        config_data = json.loads(row['config'])
                        scenario_config_data = ScenarioConfigData(**config_data)

                        # 创建场景配置对象
                        scenario = ScenarioConfig(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            config=scenario_config_data,
                            status=ScenarioStatus(row['status']),
                            created_at=datetime.fromisoformat(row['created_at']),
                            updated_at=datetime.fromisoformat(row['updated_at'])
                        )

                        scenarios[row['id']] = scenario

                    except Exception as e:
                        print(f"⚠️ 解析场景配置失败 {row['id']}: {str(e)}")
                        continue

        except Exception as e:
            print(f"❌ 从数据库加载场景配置失败: {str(e)}")
            # 如果数据库加载失败，使用默认配置
            return self._get_default_scenarios()

        return scenarios

    def _get_default_scenarios(self) -> Dict[str, ScenarioConfig]:
        """获取默认场景配置"""
        scenarios = {}

        for scenario_id, config_data in DEFAULT_SCENARIO_CONFIGS.items():
            scenario = ScenarioConfig(
                id=scenario_id,
                name=config_data.ui.welcomeTitle.replace("欢迎使用", "").replace("智能问答", "").replace("智能助手", ""),
                description=f"默认{scenario_id}场景配置",
                config=config_data,
                status=ScenarioStatus.ACTIVE
            )
            scenarios[scenario_id] = scenario

        return scenarios

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        """获取特定场景配置"""
        scenarios = self.get_all_scenarios()
        return scenarios.get(scenario_id)

    def get_all_scenarios(self) -> Dict[str, ScenarioConfig]:
        """获取所有场景配置"""
        # 检查缓存
        if self._is_cache_valid() and self._cache:
            return self._cache

        # 从数据库加载
        scenarios = self._load_from_database()

        # 更新缓存
        self._cache = scenarios
        self._cache_timestamp = datetime.now()

        return scenarios

    def get_active_scenarios(self) -> List[ScenarioConfig]:
        """获取所有活跃场景"""
        scenarios = self.get_all_scenarios()
        return [
            scenario for scenario in scenarios.values()
            if scenario.status == ScenarioStatus.ACTIVE
        ]

    def validate_scenario(self, scenario_id: str) -> bool:
        """验证场景是否存在且活跃"""
        scenario = self.get_scenario(scenario_id)
        return scenario is not None and scenario.status == ScenarioStatus.ACTIVE

    def get_scenario_theme(self, scenario_id: str) -> Optional[Dict[str, str]]:
        """获取场景主题配置"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return scenario.config.theme.dict()
        return None

    def get_scenario_ui_config(self, scenario_id: str) -> Optional[Dict[str, str]]:
        """获取场景UI配置"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return scenario.config.ui.dict()
        return None

    def get_preset_questions(self, scenario_id: str) -> List[str]:
        """获取场景预设问题"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return scenario.config.presetQuestions
        return []

    def get_document_types(self, scenario_id: str) -> List[Dict[str, Any]]:
        """获取场景支持的文档类型"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return [doc_type.dict() for doc_type in scenario.config.documentTypes]
        return []

    def get_prompt_template(self, scenario_id: str, template_type: str = "system") -> Optional[str]:
        """获取场景提示词模板"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            templates = scenario.config.prompt_templates.dict()
            return templates.get(template_type)
        return None

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        self._cache_timestamp = None

    def refresh_cache(self) -> None:
        """刷新缓存"""
        self.clear_cache()
        self.get_all_scenarios()

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_size": len(self._cache),
            "cache_timestamp": self._cache_timestamp.isoformat() if self._cache_timestamp else None,
            "cache_valid": self._is_cache_valid(),
            "cached_scenarios": list(self._cache.keys())
        }


class ScenarioConfigLoader:
    """场景配置加载器"""

    @staticmethod
    def load_from_file(config_file: Path) -> Dict[str, ScenarioConfig]:
        """从配置文件加载场景配置"""
        try:
            if not config_file.exists():
                print(f"⚠️ 配置文件不存在: {config_file}")
                return {}

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            scenarios = {}

            for scenario_id, scenario_data in config_data.get('scenarios', {}).items():
                try:
                    config_data_obj = ScenarioConfigData(**scenario_data['config'])

                    scenario = ScenarioConfig(
                        id=scenario_id,
                        name=scenario_data.get('name', scenario_id),
                        description=scenario_data.get('description', ''),
                        config=config_data_obj,
                        status=ScenarioStatus(scenario_data.get('status', 'active'))
                    )

                    scenarios[scenario_id] = scenario

                except Exception as e:
                    print(f"⚠️ 解析场景配置失败 {scenario_id}: {str(e)}")
                    continue

            return scenarios

        except Exception as e:
            print(f"❌ 从文件加载场景配置失败: {str(e)}")
            return {}

    @staticmethod
    def save_to_file(scenarios: Dict[str, ScenarioConfig], config_file: Path) -> bool:
        """保存场景配置到文件"""
        try:
            # 确保目录存在
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # 构建配置数据
            config_data = {
                "version": "1.0.0",
                "updated_at": datetime.now().isoformat(),
                "scenarios": {}
            }

            for scenario_id, scenario in scenarios.items():
                config_data["scenarios"][scenario_id] = {
                    "name": scenario.name,
                    "description": scenario.description,
                    "status": scenario.status.value,
                    "config": scenario.config.dict(),
                    "created_at": scenario.created_at.isoformat(),
                    "updated_at": scenario.updated_at.isoformat()
                }

            # 写入文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 场景配置已保存到: {config_file}")
            return True

        except Exception as e:
            print(f"❌ 保存场景配置失败: {str(e)}")
            return False


# 全局场景配置管理器实例
_scenario_config_manager: Optional[ScenarioConfigManager] = None


def get_scenario_config_manager(database_path: str) -> ScenarioConfigManager:
    """获取场景配置管理器实例"""
    global _scenario_config_manager

    if _scenario_config_manager is None:
        _scenario_config_manager = ScenarioConfigManager(database_path)

    return _scenario_config_manager


def init_scenario_config_manager(database_path: str, cache_ttl: int = 300) -> ScenarioConfigManager:
    """初始化场景配置管理器"""
    global _scenario_config_manager

    _scenario_config_manager = ScenarioConfigManager(database_path, cache_ttl)
    return _scenario_config_manager


# 便捷函数
def get_scenario(scenario_id: str) -> Optional[ScenarioConfig]:
    """获取场景配置"""
    if _scenario_config_manager:
        return _scenario_config_manager.get_scenario(scenario_id)
    return None


def get_all_scenarios() -> Dict[str, ScenarioConfig]:
    """获取所有场景配置"""
    if _scenario_config_manager:
        return _scenario_config_manager.get_all_scenarios()
    return {}


def validate_scenario(scenario_id: str) -> bool:
    """验证场景"""
    if _scenario_config_manager:
        return _scenario_config_manager.validate_scenario(scenario_id)
    return False


def get_preset_questions(scenario_id: str) -> List[str]:
    """获取预设问题"""
    if _scenario_config_manager:
        return _scenario_config_manager.get_preset_questions(scenario_id)
    return []


def get_prompt_template(scenario_id: str, template_type: str = "system") -> Optional[str]:
    """获取提示词模板"""
    if _scenario_config_manager:
        return _scenario_config_manager.get_prompt_template(scenario_id, template_type)
    return None

