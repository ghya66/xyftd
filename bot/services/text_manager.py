"""
文案管理器
从 JSON 配置文件加载文案，支持热加载
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from ..config import config


class TextManager:
    """
    文案管理器类
    
    负责从 config/texts.json 加载文案配置
    支持热加载（通过管理员命令 /reload 触发）
    """
    
    _texts: Dict[str, Any] = {}
    _last_load_time: Optional[datetime] = None
    _config_path: str = "config/texts.json"
    
    @classmethod
    def load(cls) -> bool:
        """
        加载配置文件
        
        Returns:
            是否加载成功
        """
        try:
            # 获取配置文件的绝对路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, cls._config_path)
            
            with open(config_path, "r", encoding="utf-8") as f:
                cls._texts = json.load(f)
            
            cls._last_load_time = datetime.now()
            print(f"[TextManager] 配置文件加载成功: {config_path}")
            return True
        except FileNotFoundError:
            print(f"[TextManager] 配置文件不存在: {cls._config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"[TextManager] 配置文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"[TextManager] 加载配置失败: {e}")
            return False
    
    @classmethod
    def reload(cls) -> bool:
        """
        热加载配置文件（管理员命令触发）
        
        Returns:
            是否重新加载成功
        """
        return cls.load()
    
    @classmethod
    def get(cls, key: str, default: str = "", **kwargs) -> str:
        """
        获取文案，支持占位符替换
        
        Args:
            key: 配置键名（支持点分隔，如 "buttons.entry"）
            default: 默认值
            **kwargs: 额外的占位符替换参数
        
        Returns:
            处理后的文案字符串
        """
        # 确保配置已加载
        if not cls._texts:
            cls.load()
        
        # 支持点分隔的键名
        value = cls._texts
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        # 如果是字符串，进行占位符替换
        if isinstance(value, str):
            return cls._replace_placeholders(value, **kwargs)
        
        return str(value) if value else default
    
    @classmethod
    def get_dict(cls, key: str) -> Dict[str, Any]:
        """
        获取字典类型的配置
        
        Args:
            key: 配置键名
        
        Returns:
            配置字典，如果不存在返回空字典
        """
        if not cls._texts:
            cls.load()
        
        value = cls._texts
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return {}
        
        return value if isinstance(value, dict) else {}
    
    @classmethod
    def get_service(cls, service_code: str) -> Dict[str, Any]:
        """
        获取服务配置
        
        Args:
            service_code: 服务代码（如 "la_zhuan"）
        
        Returns:
            服务配置字典
        """
        services = cls.get_dict("services")
        service = services.get(service_code, {})
        
        # 替换文案中的占位符
        if "text" in service:
            service["text"] = cls._replace_placeholders(service["text"])
        if "follow_up" in service:
            service["follow_up"] = cls._replace_placeholders(service["follow_up"])
        
        return service
    
    @classmethod
    def _replace_placeholders(cls, text: str, **kwargs) -> str:
        """
        替换文案中的占位符
        
        Args:
            text: 原始文案
            **kwargs: 额外的替换参数
        
        Returns:
            替换后的文案
        """
        # 内置占位符
        replacements = {
            "PAYMENT_ADDRESS": config.PAYMENT_ADDRESS,
        }
        # 合并额外参数
        replacements.update(kwargs)
        
        try:
            return text.format(**replacements)
        except KeyError:
            # 如果有未知的占位符，返回原文
            return text
    
    @classmethod
    def get_version(cls) -> str:
        """获取配置文件版本"""
        return cls.get("version", "unknown")
    
    @classmethod
    def get_last_load_time(cls) -> Optional[datetime]:
        """获取最后加载时间"""
        return cls._last_load_time


# 模块加载时自动初始化
TextManager.load()

