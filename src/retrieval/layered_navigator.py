"""
分层导航器
实现多轮文档分块与筛选，保证上下文完整性
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LayeredNavigator:
    """
    分层导航器

    通过多轮迭代，从粗粒度到细粒度逐步缩小检索范围，
    同时保证文档块的完整性和上下文连贯性
    """

    def __init__(self, routing_agent: Any):
        """
        初始化分层导航器

        Args:
            routing_agent: 路由代理实例（用于文档块选择）
        """
        self.routing_agent = routing_agent
        logger.info("LayeredNavigator initialized")

    def navigate(
        self,
        chunks: List[Dict],
        question: str,
        max_rounds: int = 3,
        target_tokens: int = 2000
    ) -> List[Dict]:
        """
        多轮分层导航

        Args:
            chunks: 初始检索得到的文档块列表
            question: 用户问题
            max_rounds: 最大导航轮数
            target_tokens: 目标Token数量

        Returns:
            筛选后的文档块列表
        """
        if not chunks:
            logger.warning("输入文档块为空")
            return []

        try:
            # 初始化推理历史
            scratchpad = f"开始分层导航: {question}"
            current_chunks = chunks

            logger.info(f"分层导航开始: {len(chunks)} 个初始块")

            for round_num in range(max_rounds):
                # 计算当前Token总数（粗略估计：1字符≈1.5tokens）
                total_tokens = sum(len(c.get('text', '')) * 1.5 for c in current_chunks)

                logger.debug(
                    f"第{round_num + 1}轮: {len(current_chunks)} 个块, "
                    f"约 {total_tokens:.0f} tokens"
                )

                # 如果已经满足目标，停止导航
                # 优先控制token数量，其次考虑块数
                if total_tokens <= target_tokens and len(current_chunks) <= 10:
                    logger.info(
                        f"导航终止: tokens({total_tokens:.0f}) <= 目标({target_tokens}) "
                        f"且块数({len(current_chunks)}) <= 10"
                    )
                    break
                elif len(current_chunks) <= 3:
                    # 块数太少也要停止，避免过度裁剪
                    logger.info(f"导航终止: 块数太少({len(current_chunks)})")
                    break

                # 使用路由代理选择最相关的块
                routing_result = self.routing_agent.route_documents(
                    chunks=current_chunks,
                    question=question,
                    history=scratchpad,
                    top_k=max(5, len(current_chunks) // 2)  # 每轮缩减一半
                )

                if not routing_result.get("success"):
                    logger.warning(f"第{round_num + 1}轮路由失败")
                    break

                # 更新当前块
                selected_chunks = routing_result["chunks"]

                if len(selected_chunks) >= len(current_chunks):
                    # 没有缩减，停止导航
                    logger.info(f"第{round_num + 1}轮未缩减块数，导航停止")
                    break

                current_chunks = selected_chunks

                # 更新推理历史
                scratchpad += (
                    f"\n第{round_num + 1}轮: 选中 {len(current_chunks)} 个块 "
                    f"(置信度: {routing_result.get('confidence', 0):.2f}), "
                    f"理由: {routing_result.get('reasoning', '')[:50]}"
                )

            # 扩展上下文以保证完整性
            final_chunks = self._expand_for_completeness(current_chunks)

            logger.info(
                f"分层导航完成: {len(chunks)} → {len(current_chunks)} → {len(final_chunks)} 个块"
            )

            return final_chunks

        except Exception as e:
            logger.error(f"分层导航失败: {e}")
            # 降级方案：返回前5个块
            return chunks[:5]

    def _expand_for_completeness(self, chunks: List[Dict]) -> List[Dict]:
        """
        扩展上下文以保证完整性

        检查文档块是否被截断，如果是，尝试合并相邻块

        Args:
            chunks: 文档块列表

        Returns:
            扩展后的文档块列表
        """
        if not chunks:
            return chunks

        expanded_chunks = []

        for chunk in chunks:
            # 检查是否需要扩展
            if self.routing_agent.should_expand_context(chunk):
                logger.debug(f"文档块需要扩展: {chunk.get('chunk_id', 'unknown')}")
                # 标记需要扩展（实际扩展需要访问完整文档，这里仅标记）
                chunk['needs_expansion'] = True
            else:
                chunk['needs_expansion'] = False

            expanded_chunks.append(chunk)

        return expanded_chunks

    def refine_chunks(
        self,
        chunks: List[Dict],
        n_sub: int = 3
    ) -> List[Dict]:
        """
        细化文档块（将大块拆分为小块）

        Args:
            chunks: 文档块列表
            n_sub: 每个块拆分的子块数量

        Returns:
            细化后的文档块列表
        """
        refined = []

        for chunk in chunks:
            text = chunk.get('text', '')

            # 如果文本较短，不拆分
            if len(text) < 300:
                refined.append(chunk)
                continue

            # 按句子拆分
            sentences = self._split_sentences(text)

            # 分组为n_sub个子块
            chunk_size = max(1, len(sentences) // n_sub)

            for i in range(0, len(sentences), chunk_size):
                sub_sentences = sentences[i:i + chunk_size]
                sub_text = "".join(sub_sentences)

                if sub_text.strip():
                    sub_chunk = chunk.copy()
                    sub_chunk['text'] = sub_text
                    sub_chunk['chunk_id'] = f"{chunk.get('chunk_id', 'unknown')}_sub_{i//chunk_size}"
                    refined.append(sub_chunk)

        logger.debug(f"文档块细化: {len(chunks)} → {len(refined)}")
        return refined

    def _split_sentences(self, text: str) -> List[str]:
        """
        按句子拆分文本

        Args:
            text: 输入文本

        Returns:
            句子列表
        """
        import re

        # 中文句子分隔符
        sentence_delimiters = r'[。！？；\n]+'
        sentences = re.split(sentence_delimiters, text)

        # 保留分隔符
        result = []
        for sent in sentences:
            if sent.strip():
                result.append(sent + "。")

        return result

    def estimate_tokens(self, chunks: List[Dict]) -> int:
        """
        估算文档块的Token总数

        Args:
            chunks: 文档块列表

        Returns:
            估算的Token总数
        """
        # 粗略估计：1个中文字符≈1.5个token
        total_chars = sum(len(c.get('text', '')) for c in chunks)
        return int(total_chars * 1.5)
