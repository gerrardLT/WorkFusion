"""
智能路由代理
负责问题分析、文档路由和上下文选择
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional

from api_requests import APIProcessor
from config import get_settings

logger = logging.getLogger(__name__)


class RoutingAgent:
    """智能路由代理，基于 Qwen 进行决策"""

    def __init__(self, scenario_id: str):
        """
        初始化路由代理

        Args:
            scenario_id: 场景ID (tender, enterprise)
        """
        self.scenario_id = scenario_id
        self.settings = get_settings()
        self.api_processor = APIProcessor(provider="dashscope")

        # 场景化关键词库
        self.keyword_library = {
            "tender": {
                "budget": ["预算", "报价", "价格", "金额", "资金", "费用", "成本"],
                "deadline": ["截止", "期限", "时间", "日期", "提交", "开标"],
                "requirement": ["要求", "条件", "资格", "标准", "规定", "必须"],
                "technical": ["技术", "规格", "参数", "性能", "指标", "配置"],
                "qualification": ["资质", "证书", "许可", "认证", "业绩"],
                "procedure": ["流程", "程序", "步骤", "方式", "方法"]
            },
            "enterprise": {
                "policy": ["政策", "制度", "规定", "条例", "办法"],
                "process": ["流程", "步骤", "程序", "办理", "申请"],
                "benefit": ["福利", "待遇", "补贴", "保险", "假期"],
                "training": ["培训", "学习", "发展", "晋升", "考核"],
                "hr": ["人力", "招聘", "薪酬", "绩效", "考勤"],
                "finance": ["财务", "报销", "预算", "费用", "审批"]
            }
        }

        # 路由决策提示词模板
        self._setup_routing_prompts()

        logger.info(f"RoutingAgent initialized for scenario: {scenario_id}")

    def _setup_routing_prompts(self):
        """设置路由决策提示词"""
        self.query_analysis_prompt = """你是专业的问题分析助手。请分析用户问题并提取关键信息。

**场景**: {scenario_name}

**用户问题**: {question}

**任务**: 请从以下维度分析问题：
1. **问题类型**: 事实查询(fact)、分析判断(analysis)、指导建议(guidance)
2. **关键词**: 提取3-5个核心关键词（中文）
3. **问题难度**: 简单(simple)、中等(medium)、复杂(complex)
4. **需要文档类型**: 根据场景推断需要哪类文档

**输出要求**: 严格按JSON格式输出，不要包含任何其他文本：
{{
    "question_type": "fact|analysis|guidance",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "difficulty": "simple|medium|complex",
    "document_type": "string",
    "category": "问题分类"
}}"""

        self.document_routing_prompt = """你是专业的文档路由助手。请根据问题选择最相关的文档块。

**场景**: {scenario_name}

**用户问题**: {question}

**候选文档块**:
{chunks_info}

**任务**:
1. 从候选文档块中选择最相关的3-5个
2. 说明为什么选择这些文档
3. 评估选择的置信度

**输出要求**: 严格按JSON格式输出：
{{
    "selected_indices": [0, 1, 2],
    "reasoning": "选择理由",
    "confidence": 0.85,
    "should_expand": false
}}"""

    def analyze_query(self, question: str) -> Dict[str, Any]:
        """
        分析问题，提取关键信息

        Args:
            question: 用户问题

        Returns:
            分析结果，包含问题类型、关键词、难度等
        """
        try:
            # 场景名称映射
            scenario_names = {
                "tender": "招投标",
                "enterprise": "企业管理"
            }
            scenario_name = scenario_names.get(self.scenario_id, self.scenario_id)

            # 构建提示词
            prompt = self.query_analysis_prompt.format(
                scenario_name=scenario_name,
                question=question
            )

            # 调用 Qwen 进行分析
            response = self.api_processor.send_message(
                system_content="你是专业的问题分析助手，必须严格按照JSON格式输出结果。",
                human_content=prompt,
                temperature=0.0,  # 确保稳定输出
                max_tokens=500,
                model="qwen-turbo-latest"  # 使用快速模型
            )

            # 解析 JSON 响应
            result = self._parse_json_response(response)

            if not result:
                # 降级方案：基于规则提取关键词
                logger.warning("LLM分析失败，使用规则降级方案")
                result = self._rule_based_analysis(question)

            # 增强：基于场景关键词库
            result = self._enhance_with_keywords(result, question)

            logger.info(f"问题分析完成: type={result.get('question_type')}, keywords={result.get('keywords')}")

            return result

        except Exception as e:
            logger.error(f"问题分析失败: {e}")
            return self._rule_based_analysis(question)

    def route_documents(
        self,
        chunks: List[Dict],
        question: str,
        history: str = "",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        智能选择相关文档块

        Args:
            chunks: 候选文档块列表
            question: 用户问题
            history: 对话历史（可选）
            top_k: 返回文档数量

        Returns:
            路由结果，包含选中的文档块、推理过程、置信度
        """
        if not chunks:
            logger.warning("没有候选文档块")
            return {
                "success": False,
                "chunks": [],
                "reasoning": "没有可用的文档块",
                "confidence": 0.0
            }

        try:
            # 如果候选文档少于等于top_k，直接返回全部
            if len(chunks) <= top_k:
                logger.debug(f"候选文档数({len(chunks)}) <= top_k({top_k})，返回全部")
                return {
                    "success": True,
                    "chunks": chunks,
                    "reasoning": "候选文档数量较少，全部返回",
                    "confidence": 0.9
                }

            # 构建文档块信息
            chunks_info = self._format_chunks_for_routing(chunks[:15])  # 限制最多15个候选

            # 场景名称
            scenario_names = {"tender": "招投标", "enterprise": "企业管理"}
            scenario_name = scenario_names.get(self.scenario_id, self.scenario_id)

            # 构建提示词
            prompt = self.document_routing_prompt.format(
                scenario_name=scenario_name,
                question=question,
                chunks_info=chunks_info
            )

            # 调用 Qwen 进行路由
            response = self.api_processor.send_message(
                system_content="你是专业的文档路由助手，必须严格按照JSON格式输出结果。",
                human_content=prompt,
                temperature=0.0,
                max_tokens=400,
                model="qwen-turbo-latest"
            )

            # 解析路由结果
            routing_result = self._parse_json_response(response)

            if not routing_result or "selected_indices" not in routing_result:
                logger.warning("路由失败，使用降级方案")
                # 降级：返回前top_k个
                return {
                    "success": True,
                    "chunks": chunks[:top_k],
                    "reasoning": "LLM路由失败，返回前Top-K结果",
                    "confidence": 0.7
                }

            # 提取选中的文档块
            selected_indices = routing_result["selected_indices"][:top_k]
            selected_chunks = [chunks[i] for i in selected_indices if i < len(chunks)]

            logger.info(
                f"文档路由完成: 从{len(chunks)}个候选中选择{len(selected_chunks)}个, "
                f"置信度={routing_result.get('confidence', 0.8)}"
            )

            return {
                "success": True,
                "chunks": selected_chunks,
                "reasoning": routing_result.get("reasoning", "基于LLM路由"),
                "confidence": routing_result.get("confidence", 0.8),
                "should_expand": routing_result.get("should_expand", False)
            }

        except Exception as e:
            logger.error(f"文档路由失败: {e}")
            return {
                "success": True,
                "chunks": chunks[:top_k],
                "reasoning": f"路由异常: {str(e)}，返回前Top-K",
                "confidence": 0.6
            }

    def should_expand_context(self, chunk: Dict) -> bool:
        """
        判断是否需要扩展上下文

        Args:
            chunk: 文档块

        Returns:
            是否需要扩展
        """
        text = chunk.get("text", "")

        # 检查是否有明显的截断标志
        truncation_indicators = [
            text.endswith("..."),
            text.endswith("："),
            text.endswith("，"),
            len(text) < 100,  # 文本过短
            "（续" in text,
            "接上" in text
        ]

        return any(truncation_indicators)

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析LLM的JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON
            json_pattern = r'\{[^}]+\}'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            logger.warning(f"JSON解析失败: {response[:100]}")
            return None

    def _rule_based_analysis(self, question: str) -> Dict[str, Any]:
        """基于规则的降级分析"""
        # 简单的关键词提取
        keywords = []
        for category, words in self.keyword_library.get(self.scenario_id, {}).items():
            for word in words:
                if word in question:
                    keywords.append(word)

        # 判断问题类型
        question_type = "fact"
        if any(word in question for word in ["如何", "怎么", "怎样", "建议"]):
            question_type = "guidance"
        elif any(word in question for word in ["分析", "比较", "评估", "判断"]):
            question_type = "analysis"

        return {
            "question_type": question_type,
            "keywords": keywords[:5] if keywords else [question[:10]],
            "difficulty": "medium",
            "document_type": "general",
            "category": "其他"
        }

    def _enhance_with_keywords(self, result: Dict, question: str) -> Dict:
        """基于场景关键词库增强分析结果"""
        existing_keywords = set(result.get("keywords", []))

        # 从关键词库中匹配
        for category, words in self.keyword_library.get(self.scenario_id, {}).items():
            for word in words:
                if word in question and word not in existing_keywords:
                    existing_keywords.add(word)
                    if len(existing_keywords) >= 5:
                        break

        result["keywords"] = list(existing_keywords)[:5]
        return result

    def _format_chunks_for_routing(self, chunks: List[Dict]) -> str:
        """格式化文档块用于路由决策"""
        formatted = []
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")[:150]  # 限制长度
            score = chunk.get("score", 0)
            source = chunk.get("source", "unknown")
            formatted.append(f"[{i}] (来源:{source}, 分数:{score:.3f}) {text}...")

        return "\n".join(formatted)
