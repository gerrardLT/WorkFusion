"""
DashScope API客户端
提供LLM和Embedding模型的统一访问接口
"""

import dashscope
from dashscope import Generation, TextEmbedding
from typing import List, Dict, Any, Optional
import logging
from config import get_settings

logger = logging.getLogger(__name__)


class DashScopeClient:
    """DashScope API客户端封装"""

    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()

        # 设置API密钥
        if api_key:
            dashscope.api_key = api_key
        else:
            dashscope.api_key = self.settings.dashscope.api_key

        self.llm_model = self.settings.dashscope.llm_model
        self.embedding_model = self.settings.dashscope.embedding_model

        logger.info(
            f"DashScope客户端初始化完成，LLM模型: {self.llm_model}, "
            f"Embedding模型: {self.embedding_model}"
        )

    def validate_api_key(self) -> bool:
        """验证API密钥是否有效"""
        try:
            # 使用简单的文本生成测试API密钥
            response = Generation.call(
                model=self.llm_model, prompt="测试", max_tokens=10
            )

            if response.status_code == 200:
                logger.info("DashScope API密钥验证成功")
                return True
            else:
                logger.error(f"DashScope API密钥验证失败: {response.message}")
                return False

        except Exception as e:
            logger.error(f"DashScope API密钥验证异常: {str(e)}")
            return False

    def generate_text(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """生成文本（支持单轮和多轮对话）

        Args:
            prompt: 单轮对话的输入提示（旧版兼容，优先使用 messages）
            messages: 多轮对话消息列表，格式: [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词（仅在使用 prompt 时有效）
            max_tokens: 最大生成长度
            temperature: 生成温度
            **kwargs: 其他参数

        Returns:
            生成结果字典: {"success": bool, "text": str, "usage": dict, "request_id": str}
        """
        try:
            # 优先使用 messages（多轮对话）
            if messages:
                response = Generation.call(
                    model=self.llm_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    result_format='message',  # 使用 message 格式
                    **kwargs,
                )
            # 兼容旧版 prompt（单轮对话）
            elif prompt:
                # 如果提供了 system_prompt，构建 messages
                if system_prompt:
                    messages = [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ]
                    response = Generation.call(
                        model=self.llm_model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        result_format='message',
                        **kwargs,
                    )
                else:
                    # 纯 prompt 模式（旧版兼容）
                    response = Generation.call(
                        model=self.llm_model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    )
            else:
                return {"success": False, "error": "必须提供 prompt 或 messages 参数"}

            if response.status_code == 200:
                # 处理不同的返回格式
                if hasattr(response.output, 'choices'):
                    # message 格式
                    text = response.output.choices[0].message.content
                else:
                    # prompt 格式
                    text = response.output.text

                return {
                    "success": True,
                    "text": text,
                    "usage": response.usage,
                    "request_id": response.request_id,
                }
            else:
                logger.error(f"文本生成失败: {response.message}")
                return {
                    "success": False,
                    "error": response.message,
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"文本生成异常: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """获取文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量结果字典
        """
        try:
            response = TextEmbedding.call(model=self.embedding_model, input=texts)

            if response.status_code == 200:
                embeddings = []
                for output in response.output["embeddings"]:
                    embeddings.append(output["embedding"])

                return {
                    "success": True,
                    "embeddings": embeddings,
                    "usage": response.usage,
                    "request_id": response.request_id,
                }
            else:
                logger.error(f"获取嵌入向量失败: {response.message}")
                return {
                    "success": False,
                    "error": response.message,
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"获取嵌入向量异常: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_single_embedding(self, text: str) -> Optional[List[float]]:
        """获取单个文本的嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量或None
        """
        result = self.get_embeddings([text])
        if result["success"] and result["embeddings"]:
            return result["embeddings"][0]
        return None

    def chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """聊天补全接口

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Returns:
            聊天结果字典
        """
        try:
            response = Generation.call(
                model=self.llm_model, messages=messages, **kwargs
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": response.output.choices[0]["message"],
                    "usage": response.usage,
                    "request_id": response.request_id,
                }
            else:
                logger.error(f"聊天补全失败: {response.message}")
                return {
                    "success": False,
                    "error": response.message,
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"聊天补全异常: {str(e)}")
            return {"success": False, "error": str(e)}


# 全局客户端实例
_client = None


def get_dashscope_client() -> DashScopeClient:
    """获取全局DashScope客户端实例"""
    global _client
    if _client is None:
        _client = DashScopeClient()
    return _client


def validate_dashscope_setup() -> bool:
    """验证DashScope设置是否正确"""
    try:
        client = get_dashscope_client()
        return client.validate_api_key()
    except Exception as e:
        logger.error(f"DashScope设置验证失败: {str(e)}")
        return False
