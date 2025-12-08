"""
服务响应文案
从 TextManager 获取服务响应配置
"""

from typing import Any, Dict

from ..services.text_manager import TextManager


def get_service_responses() -> Dict[str, Any]:
    """
    获取所有服务响应配置

    从 TextManager 动态加载，支持热加载
    """
    return TextManager.get_dict("services")


def get_service_response(service_code: str) -> Dict[str, Any]:
    """
    获取指定服务的响应配置

    Args:
        service_code: 服务代码（如 "la_zhuan"）

    Returns:
        服务配置字典，包含 type, text, follow_up 等字段
    """
    return TextManager.get_service(service_code)


# 为了向后兼容，保留 SERVICE_RESPONSES 变量
# 注意：这个变量在模块加载时初始化，如需热加载请使用 get_service_responses() 函数
SERVICE_RESPONSES = get_service_responses()

