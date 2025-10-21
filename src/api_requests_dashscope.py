"""
DashScope API适配器
提供与原项目兼容的API接口，替换OpenAI API调用
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union, Literal
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

import dashscope
from dashscope import Generation, TextEmbedding
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

from config import get_settings
from dashscope_client import DashScopeClient

logger = logging.getLogger(__name__)


class DashScopeAPIAdapter:
    """DashScope API适配器，兼容原项目接口"""

    def __init__(self):
        self.settings = get_settings()
        self.client = DashScopeClient()
        self.default_model = self.settings.dashscope.llm_model
        self.embedding_model = self.settings.dashscope.embedding_model

        # 设置API密钥
        dashscope.api_key = self.settings.dashscope.api_key

        logger.info("DashScope API适配器初始化完成")

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=3, max=60)
    )
    def send_message(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        seed: Optional[int] = None,
        system_content: str = "You are a helpful assistant.",
        human_content: str = "Hello!",
        is_structured: bool = False,
        response_format: Optional[BaseModel] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Union[str, Dict[str, Any]]:
        """发送消息到DashScope

        Args:
            model: 模型名称
            temperature: 生成温度
            seed: 随机种子（兼容参数，DashScope可能不支持）
            system_content: 系统消息
            human_content: 用户消息
            is_structured: 是否结构化输出
            response_format: 响应格式（Pydantic模型）
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            文本内容或结构化数据
        """
        if model is None:
            model = self.default_model

        try:
            # 构建消息列表
            messages = []
            if system_content:
                messages.append({"role": "system", "content": system_content})
            if human_content:
                messages.append({"role": "user", "content": human_content})

            # DashScope API调用参数
            call_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "result_format": "message",
            }

            if max_tokens:
                call_params["max_tokens"] = max_tokens

            logger.debug(
                f"发送DashScope请求: model={model}, messages数量={len(messages)}"
            )

            # 调用DashScope API
            response = Generation.call(**call_params)

            # 处理响应
            if response.status_code == 200:
                content = response.output.choices[0]["message"]["content"]

                # 记录响应统计信息
                usage = response.usage
                self.response_data = {
                    "model": model,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "request_id": response.request_id,
                }
                logger.debug(f"DashScope响应统计: {self.response_data}")

                # 处理结构化输出
                if is_structured and response_format:
                    try:
                        # 尝试解析JSON格式的结构化输出
                        parsed_content = json.loads(content)
                        if isinstance(response_format, type) and issubclass(
                            response_format, BaseModel
                        ):
                            # 验证并转换为Pydantic模型
                            validated_data = response_format(**parsed_content)
                            return validated_data.dict()
                        else:
                            return parsed_content
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"结构化输出解析失败，返回原始文本: {e}")
                        return content

                return content

            else:
                error_msg = (
                    f"DashScope API调用失败: {response.code} - {response.message}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"DashScope API调用异常: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=3, min=5, max=120)
    )
    def get_embeddings(
        self,
        texts: Union[str, List[str]],
        model: Optional[str] = None,
        batch_size: int = 10,
    ) -> List[List[float]]:
        """获取文本嵌入向量

        Args:
            texts: 单个文本或文本列表
            model: 嵌入模型名称
            batch_size: 批处理大小

        Returns:
            嵌入向量列表
        """
        if model is None:
            model = self.embedding_model

        # 确保输入是列表格式
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        try:
            all_embeddings = []

            # 分批处理以避免API限制
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                logger.debug(
                    f"处理嵌入向量批次 {i // batch_size + 1}, 文本数量: {len(batch)}"
                )

                # 调用DashScope API
                response = TextEmbedding.call(
                    model=model, input=batch, text_type="document"  # 文档类型嵌入
                )

                if response.status_code == 200:
                    # 提取嵌入向量
                    batch_embeddings = []
                    for embedding_data in response.output["embeddings"]:
                        embedding = embedding_data["embedding"]
                        if not embedding:
                            raise RuntimeError("DashScope返回空的嵌入向量")
                        batch_embeddings.append(embedding)

                    all_embeddings.extend(batch_embeddings)

                    # 记录使用情况
                    usage = response.usage
                    logger.debug(
                        f"嵌入向量批次完成: tokens={usage.get('total_tokens', 0)}"
                    )

                    # 智能延迟策略，避免API限制
                    if i + batch_size < len(texts):
                        # 根据批次大小和位置动态调整延迟
                        batch_number = i // batch_size + 1
                        delay = min(0.5 + (batch_number * 0.2), 3.0)
                        logger.debug(f"批次{batch_number}完成，延迟{delay:.2f}秒")
                        time.sleep(delay)

                else:
                    error_msg = (
                        f"DashScope嵌入API调用失败: {response.code} - "
                        f"{response.message}"
                    )
                    logger.error(error_msg)

                    # 检查是否是API限制错误，如果是则增加延迟
                    if "Throttling" in response.message or "Rate" in response.message:
                        logger.warning("检测到API限制，增加延迟时间")
                        time.sleep(10)  # 等待更长时间

                    raise RuntimeError(error_msg)

            logger.info(f"成功获取 {len(all_embeddings)} 个嵌入向量")
            return all_embeddings

        except Exception as e:
            logger.error(f"获取嵌入向量失败: {str(e)}")
            raise

    def get_single_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """获取单个文本的嵌入向量

        Args:
            text: 输入文本
            model: 嵌入模型名称

        Returns:
            嵌入向量
        """
        embeddings = self.get_embeddings([text], model)
        return embeddings[0] if embeddings else []

    async def send_message_async(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        system_content: str = "You are a helpful assistant.",
        human_content: str = "Hello!",
        **kwargs,
    ) -> str:
        """异步发送消息

        Args:
            model: 模型名称
            temperature: 生成温度
            system_content: 系统消息
            human_content: 用户消息
            **kwargs: 其他参数

        Returns:
            响应内容
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.send_message,
                model=model,
                temperature=temperature,
                system_content=system_content,
                human_content=human_content,
                **kwargs,
            )
            return await loop.run_in_executor(None, lambda: future.result())

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """估算文本的token数量

        Args:
            text: 输入文本
            model: 模型名称（兼容参数）

        Returns:
            估算的token数量
        """
        # 中文文本的粗略估算：约1.3个字符=1个token
        chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        english_chars = len(text) - chinese_chars

        # 中文按1.3:1计算，英文按4:1计算
        estimated_tokens = int(chinese_chars / 1.3 + english_chars / 4)
        return max(1, estimated_tokens)  # 至少1个token

    def check_api_status(self) -> Dict[str, Any]:
        """检查API状态和配置

        Returns:
            状态信息字典
        """
        try:
            # 发送简单测试消息
            test_result = self.send_message(
                system_content="你是一个测试助手",
                human_content="请回复：测试成功",
                temperature=0.1,
            )

            api_status = {
                "status": "ok",
                "model": self.default_model,
                "embedding_model": self.embedding_model,
                "test_response": (
                    test_result[:50] + "..." if len(test_result) > 50 else test_result
                ),
                "api_key_configured": bool(self.settings.dashscope.api_key),
                "response_data": getattr(self, "response_data", {}),
            }

            logger.info("DashScope API状态检查完成")
            return api_status

        except Exception as e:
            error_status = {
                "status": "error",
                "error": str(e),
                "model": self.default_model,
                "embedding_model": self.embedding_model,
                "api_key_configured": bool(self.settings.dashscope.api_key),
            }
            logger.error(f"DashScope API状态检查失败: {e}")
            return error_status

    def batch_process_texts(
        self,
        texts: List[str],
        system_content: str = "You are a helpful assistant.",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_workers: int = 1,  # DashScope建议串行调用避免QPS超限
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """批量处理文本

        Args:
            texts: 文本列表
            system_content: 系统消息
            model: 模型名称
            temperature: 生成温度
            max_workers: 最大并发数
            **kwargs: 其他参数

        Returns:
            处理结果列表
        """
        results = []

        def process_single_text(text: str) -> Dict[str, Any]:
            try:
                response = self.send_message(
                    model=model,
                    temperature=temperature,
                    system_content=system_content,
                    human_content=text,
                    **kwargs,
                )
                return {
                    "success": True,
                    "input": text,
                    "output": response,
                    "error": None,
                }
            except Exception as e:
                return {
                    "success": False,
                    "input": text,
                    "output": None,
                    "error": str(e),
                }

        logger.info(f"开始批量处理 {len(texts)} 个文本")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_text = {
                executor.submit(process_single_text, text): text for text in texts
            }

            # 收集结果
            for future in future_to_text:
                result = future.result()
                results.append(result)

        successful = sum(1 for r in results if r["success"])
        logger.info(f"批量处理完成: {successful}/{len(texts)} 成功")

        return results


# 兼容性包装类，保持与原项目相同的接口
class BaseDashscopeProcessor(DashScopeAPIAdapter):
    """兼容原项目的DashScope处理器"""

    def __init__(self):
        super().__init__()
        # 保持与原项目相同的属性名
        self.response_data = {}


# 统一API处理器工厂
class UnifiedAPIProcessor:
    """统一的API处理器，支持多种provider"""

    def __init__(
        self, provider: Literal["dashscope", "openai", "gemini"] = "dashscope"
    ):
        self.provider = provider

        if provider == "dashscope":
            self.processor = DashScopeAPIAdapter()
        else:
            # 为了完整性，可以在这里添加其他provider的支持
            raise NotImplementedError(f"Provider {provider} not implemented yet")

        logger.info(f"统一API处理器初始化完成，provider: {provider}")

    def send_message(self, **kwargs):
        """统一的消息发送接口"""
        return self.processor.send_message(**kwargs)

    def get_embeddings(self, **kwargs):
        """统一的嵌入向量获取接口"""
        return self.processor.get_embeddings(**kwargs)

    def check_status(self):
        """检查API状态"""
        if hasattr(self.processor, "check_api_status"):
            return self.processor.check_api_status()
        return {"status": "unknown", "provider": self.provider}


# 便捷函数
def get_default_processor() -> DashScopeAPIAdapter:
    """获取默认的DashScope处理器"""
    return DashScopeAPIAdapter()


def create_processor(provider: str = "dashscope") -> UnifiedAPIProcessor:
    """创建指定的API处理器"""
    return UnifiedAPIProcessor(provider=provider)
