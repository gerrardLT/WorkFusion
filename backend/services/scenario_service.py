"""
场景管理服务
提供场景的CRUD操作和相关业务逻辑
"""

import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..database import get_db_session
from ..models import Scenario, DocumentType
try:
    from src.models.scenario_models import ScenarioConfig, ScenarioConfigData, DEFAULT_SCENARIO_CONFIGS
except ImportError:
    # 如果导入失败，使用简化的配置
    DEFAULT_SCENARIO_CONFIGS = {
        'tender': {
            'ui': {'welcomeTitle': '招投标', 'presetQuestions': []},
            'theme': {'primaryColor': 'green'}
        },
        'enterprise': {
            'ui': {'welcomeTitle': '企业管理', 'presetQuestions': []},
            'theme': {'primaryColor': 'purple'}
        }
    }


class ScenarioService:
    """场景管理服务"""

    def __init__(self):
        self.db = get_db_session

    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """获取所有场景（排除投资研究场景）"""
        try:
            with self.db() as db:
                # 过滤掉投资研究场景，只返回招投标和企业管理场景
                scenarios = db.query(Scenario).filter(
                    Scenario.status == "active",
                    Scenario.id.in_(["tender", "enterprise"])
                ).all()

                result = []
                for scenario in scenarios:
                    # 获取文档类型数量
                    doc_type_count = db.query(DocumentType).filter(
                        DocumentType.scenario_id == scenario.id
                    ).count()

                    # 扁平化配置数据以匹配前端期望的结构
                    config = scenario.config or {}
                    scenario_data = {
                        "id": scenario.id,
                        "name": scenario.name,
                        "description": scenario.description,
                        "status": scenario.status,
                        "document_type_count": doc_type_count,
                        "created_at": scenario.created_at.isoformat(),
                        "updated_at": scenario.updated_at.isoformat(),
                        # 扁平化配置字段
                        "theme": config.get("theme", {}),
                        "ui": config.get("ui", {}),
                        "presetQuestions": config.get("preset_questions", []),
                        "documentTypes": config.get("document_types", [])
                    }
                    result.append(scenario_data)

                return result

        except Exception as e:
            print(f"❌ 获取场景列表失败: {str(e)}")
            return []

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """获取特定场景"""
        try:
            with self.db() as db:
                scenario = db.query(Scenario).filter(
                    Scenario.id == scenario_id,
                    Scenario.status == "active"
                ).first()

                if not scenario:
                    return None

                # 扁平化配置数据以匹配前端期望的结构
                config = scenario.config or {}
                return {
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "status": scenario.status,
                    "created_at": scenario.created_at.isoformat(),
                    "updated_at": scenario.updated_at.isoformat(),
                    # 扁平化配置字段
                    "theme": config.get("theme", {}),
                    "ui": config.get("ui", {}),
                    "presetQuestions": config.get("presetQuestions", []),
                    "documentTypes": config.get("documentTypes", [])
                }

        except Exception as e:
            print(f"❌ 获取场景失败 {scenario_id}: {str(e)}")
            return None

    def validate_scenario(self, scenario_id: str) -> bool:
        """验证场景是否存在且活跃"""
        try:
            with self.db() as db:
                scenario = db.query(Scenario).filter(
                    Scenario.id == scenario_id,
                    Scenario.status == "active"
                ).first()

                return scenario is not None

        except Exception as e:
            print(f"❌ 验证场景失败 {scenario_id}: {str(e)}")
            return False

    def get_scenario_config(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """获取场景配置

        返回场景的完整信息，包括 name, description, theme, ui, presetQuestions, documentTypes 等
        """
        scenario = self.get_scenario(scenario_id)
        # 直接返回扁平化后的场景数据（包含所有配置字段）
        return scenario

    def get_preset_questions(self, scenario_id: str) -> List[str]:
        """获取场景预设问题"""
        config = self.get_scenario_config(scenario_id)
        if config:
            return config.get("presetQuestions", [])
        return []

    def get_document_types(self, scenario_id: str) -> List[Dict[str, Any]]:
        """获取场景支持的文档类型"""
        try:
            with self.db() as db:
                doc_types = db.query(DocumentType).filter(
                    DocumentType.scenario_id == scenario_id
                ).all()

                result = []
                for doc_type in doc_types:
                    result.append({
                        "id": doc_type.id,
                        "name": doc_type.name,
                        "description": doc_type.description,
                        "file_extensions": doc_type.file_extensions,
                        "processing_config": doc_type.processing_config
                    })

                return result

        except Exception as e:
            # 获取文档类型失败
            return []

    def get_prompt_template(self, scenario_id: str, template_type: str = "system") -> Optional[str]:
        """获取场景提示词模板"""
        config = self.get_scenario_config(scenario_id)
        if config and "prompt_templates" in config:
            return config["prompt_templates"].get(template_type)
        return None

    def get_ui_config(self, scenario_id: str) -> Optional[Dict[str, str]]:
        """获取场景UI配置"""
        config = self.get_scenario_config(scenario_id)
        if config:
            return config.get("ui", {})
        return None

    def get_theme_config(self, scenario_id: str) -> Optional[Dict[str, str]]:
        """获取场景主题配置"""
        config = self.get_scenario_config(scenario_id)
        if config:
            return config.get("theme", {})
        return None

    def create_scenario(self, scenario_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建新场景"""
        try:
            with self.db() as db:
                # 检查ID是否已存在
                existing = db.query(Scenario).filter(Scenario.id == scenario_data["id"]).first()
                if existing:
                    raise ValueError(f"场景ID {scenario_data['id']} 已存在")

                # 创建场景
                scenario = Scenario(
                    id=scenario_data["id"],
                    name=scenario_data["name"],
                    description=scenario_data.get("description", ""),
                    config=scenario_data["config"],
                    status="active"
                )

                db.add(scenario)
                db.commit()
                db.refresh(scenario)

                return self.get_scenario(scenario.id)

        except Exception as e:
            print(f"❌ 创建场景失败: {str(e)}")
            return None

    def update_scenario(self, scenario_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新场景"""
        try:
            with self.db() as db:
                scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
                if not scenario:
                    return None

                # 更新字段
                if "name" in update_data:
                    scenario.name = update_data["name"]
                if "description" in update_data:
                    scenario.description = update_data["description"]
                if "config" in update_data:
                    scenario.config = update_data["config"]
                if "status" in update_data:
                    scenario.status = update_data["status"]

                scenario.updated_at = datetime.now()

                db.commit()
                db.refresh(scenario)

                return self.get_scenario(scenario.id)

        except Exception as e:
            print(f"❌ 更新场景失败 {scenario_id}: {str(e)}")
            return None

    def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景（软删除）"""
        try:
            with self.db() as db:
                scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
                if not scenario:
                    return False

                # 软删除
                scenario.status = "inactive"
                scenario.updated_at = datetime.now()

                db.commit()
                return True

        except Exception as e:
            print(f"❌ 删除场景失败 {scenario_id}: {str(e)}")
            return False

    def get_scenario_stats(self) -> List[Dict[str, Any]]:
        """获取场景统计信息"""
        try:
            with self.db() as db:
                # 使用原生SQL查询统计视图
                result = db.execute(text("""
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
                    WHERE s.status = 'active'
                    GROUP BY s.id, s.name, s.status, s.created_at, s.updated_at
                    ORDER BY s.created_at
                """)).fetchall()

                stats = []
                for row in result:
                    stats.append({
                        "id": row[0],
                        "name": row[1],
                        "status": row[2],
                        "document_count": row[3],
                        "session_count": row[4],
                        "message_count": row[5],
                        "created_at": row[6],
                        "updated_at": row[7]
                    })

                return stats

        except Exception as e:
            print(f"❌ 获取场景统计失败: {str(e)}")
            return []

    def ensure_default_scenarios(self) -> bool:
        """确保默认场景存在"""
        try:
            with self.db() as db:
                for scenario_id, config_data in DEFAULT_SCENARIO_CONFIGS.items():
                    # 检查是否已存在
                    existing = db.query(Scenario).filter(Scenario.id == scenario_id).first()

                    if not existing:
                        # 创建默认场景
                        scenario = Scenario(
                            id=scenario_id,
                            name=config_data.ui.welcomeTitle.replace("欢迎使用", "").replace("智能问答", "").replace("智能助手", ""),
                            description=f"默认{scenario_id}场景配置",
                            config=config_data.dict(),
                            status="active"
                        )

                        db.add(scenario)
                        print(f"✅ 创建默认场景: {scenario_id}")

                db.commit()
                return True

        except Exception as e:
            print(f"❌ 确保默认场景失败: {str(e)}")
            return False


# 全局服务实例
_scenario_service: Optional[ScenarioService] = None


def get_scenario_service() -> ScenarioService:
    """获取场景服务实例"""
    global _scenario_service

    if _scenario_service is None:
        _scenario_service = ScenarioService()

    return _scenario_service

