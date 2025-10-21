"""
统一API请求处理模块
提供统一的接口来处理不同的API提供商
"""

import logging
from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel

from config import get_settings
from api_requests_dashscope import BaseDashscopeProcessor

logger = logging.getLogger(__name__)


class APIProcessor:
    """统一的API处理器，支持多种提供商"""

    def __init__(
        self, provider: Literal["dashscope", "openai", "gemini"] = "dashscope"
    ):
        """初始化API处理器

        Args:
            provider: API提供商名称
        """
        self.provider = provider.lower()
        self.settings = get_settings()

        # 根据provider初始化对应的处理器
        if self.provider == "dashscope":
            self.processor = BaseDashscopeProcessor()
        else:
            # 为未来扩展保留
            raise NotImplementedError(f"Provider {provider} not implemented yet")

        logger.info(f"API处理器初始化完成，provider: {self.provider}")

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
        """发送消息到LLM

        Args:
            model: 模型名称
            temperature: 生成温度
            seed: 随机种子
            system_content: 系统消息
            human_content: 用户消息
            is_structured: 是否结构化输出
            response_format: 响应格式
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            LLM响应内容
        """
        return self.processor.send_message(
            model=model,
            temperature=temperature,
            seed=seed,
            system_content=system_content,
            human_content=human_content,
            is_structured=is_structured,
            response_format=response_format,
            max_tokens=max_tokens,
            **kwargs,
        )

    def get_embeddings(
        self, texts: Union[str, List[str]], model: Optional[str] = None, **kwargs
    ) -> List[List[float]]:
        """获取文本嵌入向量

        Args:
            texts: 输入文本或文本列表
            model: 嵌入模型名称
            **kwargs: 其他参数

        Returns:
            嵌入向量列表
        """
        return self.processor.get_embeddings(texts, model, **kwargs)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """计算文本的token数量

        Args:
            text: 输入文本
            model: 模型名称

        Returns:
            token数量
        """
        return self.processor.count_tokens(text, model)

    def check_status(self) -> Dict[str, Any]:
        """检查API状态

        Returns:
            状态信息字典
        """
        if hasattr(self.processor, "check_api_status"):
            return self.processor.check_api_status()
        return {"status": "unknown", "provider": self.provider}

    def batch_process_texts(
        self,
        texts: List[str],
        system_content: str = "You are a helpful assistant.",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """批量处理文本

        Args:
            texts: 文本列表
            system_content: 系统消息
            **kwargs: 其他参数

        Returns:
            处理结果列表
        """
        if hasattr(self.processor, "batch_process_texts"):
            return self.processor.batch_process_texts(
                texts=texts, system_content=system_content, **kwargs
            )
        else:
            # 逐个处理的备用方案
            results = []
            for text in texts:
                try:
                    response = self.send_message(
                        system_content=system_content, human_content=text, **kwargs
                    )
                    results.append(
                        {
                            "success": True,
                            "input": text,
                            "output": response,
                            "error": None,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "success": False,
                            "input": text,
                            "output": None,
                            "error": str(e),
                        }
                    )
            return results

    @property
    def response_data(self) -> Dict[str, Any]:
        """获取最近一次响应的统计数据

        Returns:
            响应统计信息
        """
        return getattr(self.processor, "response_data", {})


# 向后兼容的基础处理器类
class BaseOpenaiProcessor:
    """OpenAI API处理器（占位符，未实现）"""

    def __init__(self):
        raise NotImplementedError("OpenAI processor not implemented in this version")

    def send_message(self, **kwargs):
        raise NotImplementedError("OpenAI processor not implemented in this version")


class BaseIBMAPIProcessor:
    """IBM API处理器（占位符，未实现）"""

    def __init__(self):
        raise NotImplementedError("IBM API processor not implemented in this version")

    def send_message(self, **kwargs):
        raise NotImplementedError("IBM API processor not implemented in this version")


class BaseGeminiProcessor:
    """Gemini API处理器（占位符，未实现）"""

    def __init__(self):
        raise NotImplementedError("Gemini processor not implemented in this version")

    def send_message(self, **kwargs):
        raise NotImplementedError("Gemini processor not implemented in this version")


# 便捷函数
def get_default_api_processor() -> APIProcessor:
    """获取默认的API处理器（DashScope）

    Returns:
        默认的API处理器实例
    """
    return APIProcessor(provider="dashscope")


def create_api_processor(provider: str = "dashscope") -> APIProcessor:
    """创建指定的API处理器

    Args:
        provider: API提供商名称

    Returns:
        API处理器实例
    """
    return APIProcessor(provider=provider)


# 导出便捷函数
def send_message(
    system_content: str = "You are a helpful assistant.",
    human_content: str = "Hello!",
    **kwargs,
) -> str:
    """快速发送消息的便捷函数

    Args:
        system_content: 系统消息
        human_content: 用户消息
        **kwargs: 其他参数

    Returns:
        LLM响应内容
    """
    processor = get_default_api_processor()
    return processor.send_message(
        system_content=system_content, human_content=human_content, **kwargs
    )


def get_embeddings(texts: Union[str, List[str]], **kwargs) -> List[List[float]]:
    """快速获取嵌入向量的便捷函数

    Args:
        texts: 输入文本或文本列表
        **kwargs: 其他参数

    Returns:
        嵌入向量列表
    """
    processor = get_default_api_processor()
    return processor.get_embeddings(texts, **kwargs)


def count_tokens(text: str, **kwargs) -> int:
    """快速计算token的便捷函数

    Args:
        text: 输入文本
        **kwargs: 其他参数

    Returns:
        token数量
    """
    processor = get_default_api_processor()
    return processor.count_tokens(text, **kwargs)


# 保持与原项目兼容的全局变量
_default_processor = None


def get_processor(provider: str = "dashscope") -> APIProcessor:
    """获取API处理器实例（兼容原项目接口）

    Args:
        provider: API提供商名称

    Returns:
        API处理器实例
    """
    global _default_processor
    if _default_processor is None or _default_processor.provider != provider:
        _default_processor = APIProcessor(provider=provider)
    return _default_processor
