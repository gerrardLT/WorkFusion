"""
答案验证器
实现三层验证机制，防止虚假引用和幻觉
"""

import logging
import re
from typing import List, Dict, Any, Optional

from api_requests import APIProcessor
from config import get_settings

logger = logging.getLogger(__name__)


class AnswerVerifier:
    """
    答案验证器

    三层验证机制：
    1. 引用提取 - 识别答案中的引用（页码、段落）
    2. 引用存在性验证 - 确保引用在源文档中存在
    3. LLM交叉验证 - 使用 Qwen-max 验证答案准确性
    """

    def __init__(self):
        """初始化答案验证器"""
        self.settings = get_settings()
        self.api_processor = APIProcessor(provider="dashscope")

        # 引用模式（正则表达式）
        self.citation_patterns = [
            r'第\s*(\d+)\s*页',  # 第X页
            r'第\s*(\d+)\s*条',  # 第X条
            r'段落\s*(\d+)',    # 段落X
            r'第\s*(\d+)\s*章',  # 第X章
            r'附录\s*([A-Z\d]+)', # 附录X
            r'\[(\d+)\]',       # [X]
            r'（第\s*(\d+)\s*页）', # (第X页)
        ]

        logger.info("AnswerVerifier initialized")

    def verify_answer(
        self,
        answer: str,
        source_chunks: List[Dict],
        question: str = ""
    ) -> Dict[str, Any]:
        """
        验证答案的准确性

        Args:
            answer: 生成的答案
            source_chunks: 源文档块列表
            question: 原始问题（用于交叉验证）

        Returns:
            验证结果，包含 is_valid, confidence, reasoning
        """
        if not answer or not source_chunks:
            logger.warning("答案或源文档为空，跳过验证")
            return {
                "is_valid": True,
                "confidence": 0.5,
                "reasoning": "无法验证（答案或源文档为空）",
                "citation_check": "skipped",
                "llm_verification": "skipped"
            }

        try:
            # 第一层：引用提取与验证
            citations = self.extract_citations(answer)
            citation_valid = True
            invalid_citations = []

            if citations:
                logger.debug(f"提取到 {len(citations)} 个引用: {citations}")

                for citation in citations:
                    if not self.citation_exists(citation, source_chunks):
                        citation_valid = False
                        invalid_citations.append(citation)
                        logger.warning(f"虚假引用检测: {citation}")

                if not citation_valid:
                    return {
                        "is_valid": False,
                        "confidence": 0.2,
                        "reasoning": f"检测到虚假引用: {', '.join(invalid_citations)}",
                        "citation_check": "failed",
                        "invalid_citations": invalid_citations,
                        "llm_verification": "skipped"
                    }
            else:
                logger.debug("答案中未检测到明确引用")

            # 第二层：Qwen交叉验证（使用高质量模型）
            try:
                llm_verification = self.qwen_verify(answer, source_chunks, question)

                # 综合评估
                final_confidence = self._calculate_confidence(
                    citation_valid=citation_valid,
                    has_citations=len(citations) > 0,
                    llm_confidence=llm_verification.get("confidence", 0.7)
                )

                return {
                    "is_valid": llm_verification.get("is_valid", True),
                    "confidence": final_confidence,
                    "reasoning": llm_verification.get("reasoning", "验证通过"),
                    "citation_check": "passed" if citation_valid else "no_citations",
                    "citations_count": len(citations),
                    "llm_verification": "completed"
                }

            except Exception as e:
                logger.warning(f"LLM验证失败: {e}，降级为引用验证结果")
                return {
                    "is_valid": citation_valid,
                    "confidence": 0.7 if citation_valid else 0.3,
                    "reasoning": "LLM验证失败，仅基于引用验证",
                    "citation_check": "passed" if citation_valid else "failed",
                    "llm_verification": "failed"
                }

        except Exception as e:
            logger.error(f"答案验证失败: {e}")
            return {
                "is_valid": True,
                "confidence": 0.5,
                "reasoning": f"验证过程异常: {str(e)}",
                "citation_check": "error",
                "llm_verification": "error"
            }

    def extract_citations(self, answer: str) -> List[str]:
        """
        提取答案中的引用

        Args:
            answer: 答案文本

        Returns:
            引用列表
        """
        citations = []

        for pattern in self.citation_patterns:
            matches = re.findall(pattern, answer)
            citations.extend(matches)

        # 去重并保持顺序
        seen = set()
        unique_citations = []
        for cite in citations:
            if cite not in seen:
                seen.add(cite)
                unique_citations.append(cite)

        return unique_citations

    def citation_exists(self, citation: str, source_chunks: List[Dict]) -> bool:
        """
        检查引用是否存在于源文档

        Args:
            citation: 引用标识（页码、段落号等）
            source_chunks: 源文档块列表

        Returns:
            引用是否存在
        """
        try:
            # 尝试将引用转换为数字
            citation_num = int(re.sub(r'\D', '', citation))

            # 在源文档块中查找
            for chunk in source_chunks:
                page = chunk.get('page', 0)
                chunk_id = chunk.get('chunk_id', '')

                # 检查页码匹配
                if page == citation_num:
                    return True

                # 检查chunk_id中是否包含该数字
                if str(citation_num) in str(chunk_id):
                    return True

            # 如果引用数字较小（<=10），可能是段落号，较宽松验证
            if citation_num <= 10 and len(source_chunks) >= citation_num:
                return True

            return False

        except ValueError:
            # 非数字引用（如附录A），直接在文本中查找
            citation_text = citation.upper()
            for chunk in source_chunks:
                text = chunk.get('text', '').upper()
                if citation_text in text:
                    return True

            return False

    def qwen_verify(
        self,
        answer: str,
        source_chunks: List[Dict],
        question: str = ""
    ) -> Dict:
        """
        使用 Qwen 进行交叉验证

        Args:
            answer: 生成的答案
            source_chunks: 源文档块
            question: 原始问题

        Returns:
            验证结果
        """
        try:
            # 构建验证提示词
            chunks_text = "\n\n".join([
                f"【文档{i+1}】{chunk.get('text', '')[:300]}"
                for i, chunk in enumerate(source_chunks[:3])  # 最多3个文档
            ])

            verification_prompt = f"""你是专业的答案验证专家。请验证以下答案是否准确。

**原始问题**: {question if question else "（未提供）"}

**生成的答案**:
{answer}

**源文档内容**:
{chunks_text}

**验证任务**:
1. 检查答案是否基于源文档内容
2. 检查答案是否存在事实错误
3. 检查答案是否过度推理或猜测

**输出要求**: 严格按JSON格式输出：
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "验证理由（简短）"
}}"""

            # 调用 Qwen-plus 进行验证（平衡质量和成本）
            response = self.api_processor.send_message(
                system_content="你是专业的答案验证专家，必须严格按照JSON格式输出结果。",
                human_content=verification_prompt,
                temperature=0.0,
                max_tokens=400,
                model="qwen-plus"  # 使用 qwen-plus（中等质量，适合验证）
            )

            # 解析JSON响应
            result = self._parse_json_response(response)

            if result:
                logger.debug(
                    f"Qwen验证完成: valid={result.get('is_valid')}, "
                    f"confidence={result.get('confidence')}"
                )
                return result
            else:
                # 解析失败，使用宽松验证
                logger.warning("Qwen验证响应解析失败，降级为宽松验证")
                return {
                    "is_valid": True,
                    "confidence": 0.6,
                    "reasoning": "验证响应解析失败，假设答案有效"
                }

        except Exception as e:
            logger.error(f"Qwen验证失败: {e}")
            return {
                "is_valid": True,
                "confidence": 0.5,
                "reasoning": f"验证异常: {str(e)}"
            }

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析LLM的JSON响应"""
        import json

        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON
            json_pattern = r'\{[^{}]*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            logger.warning(f"JSON解析失败: {response[:100]}")
            return None

    def _calculate_confidence(
        self,
        citation_valid: bool,
        has_citations: bool,
        llm_confidence: float
    ) -> float:
        """
        综合计算置信度

        Args:
            citation_valid: 引用验证是否通过
            has_citations: 是否有引用
            llm_confidence: LLM验证置信度

        Returns:
            最终置信度 (0-1)
        """
        # 基础置信度来自LLM
        base_confidence = llm_confidence

        # 如果有引用且验证通过，提升置信度
        if has_citations and citation_valid:
            base_confidence = min(1.0, base_confidence + 0.1)

        # 如果有引用但验证失败，大幅降低置信度
        if has_citations and not citation_valid:
            base_confidence = min(base_confidence, 0.3)

        # 如果没有引用，略微降低置信度
        if not has_citations:
            base_confidence = max(0.0, base_confidence - 0.05)

        return round(base_confidence, 2)

    def batch_verify(
        self,
        answers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量验证答案

        Args:
            answers: 答案列表，每个元素包含 answer, source_chunks, question

        Returns:
            验证结果列表
        """
        results = []

        for item in answers:
            verification = self.verify_answer(
                answer=item.get("answer", ""),
                source_chunks=item.get("source_chunks", []),
                question=item.get("question", "")
            )

            results.append({
                **item,
                "verification": verification
            })

        logger.info(f"批量验证完成: {len(results)} 个答案")
        return results
