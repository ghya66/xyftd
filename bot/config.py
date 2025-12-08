"""
配置管理模块
从环境变量加载所有配置
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """机器人配置类"""
    
    # Telegram Bot 配置
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_NAME: str = os.getenv("BOT_NAME", "土豆担保")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    
    # 管理员配置
    @staticmethod
    def get_admin_user_ids() -> List[int]:
        """获取管理员用户 ID 列表"""
        admin_ids = os.getenv("ADMIN_USER_IDS", "")
        if not admin_ids:
            return []

        result = []
        for uid in admin_ids.split(","):
            uid = uid.strip()
            if uid:
                try:
                    result.append(int(uid))
                except ValueError:
                    print(f"警告: 无效的管理员 ID '{uid}'，已跳过")
        return result
    
    # 支付配置
    # 注意：收款地址无默认值，必须在 .env 中配置
    PAYMENT_ADDRESS: str = os.getenv("PAYMENT_ADDRESS", "")
    PAYMENT_NETWORK: str = os.getenv("PAYMENT_NETWORK", "TRC20")
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./bot_data.db")
    
    # Redis 配置
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    USER_STATE_EXPIRE: int = int(os.getenv("USER_STATE_EXPIRE", "3600"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # 人工客服配置
    SUPPORT_GROUP_ID: str = os.getenv("SUPPORT_GROUP_ID", "")
    ENABLE_HUMAN_NOTIFICATION: bool = os.getenv("ENABLE_HUMAN_NOTIFICATION", "true").lower() == "true"
    
    # 群验证配置
    GROUP_PREFIXES: List[str] = os.getenv("GROUP_PREFIXES", "专群,公群,飞博").split(",")
    
    @classmethod
    def validate(cls) -> bool:
        """
        验证必填配置

        生产环境必须配置以下环境变量:
        - BOT_TOKEN: Telegram Bot Token
        - PAYMENT_ADDRESS: TRC20 收款地址

        Raises:
            ValueError: 必填配置缺失时抛出

        Returns:
            True 表示验证通过
        """
        errors = []

        # 验证 Bot Token
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN 环境变量未设置")

        # 验证收款地址（生产环境必填）
        if not cls.PAYMENT_ADDRESS:
            errors.append("PAYMENT_ADDRESS 环境变量未设置")
        elif len(cls.PAYMENT_ADDRESS) < 30:
            # TRC20 地址通常是 34 个字符
            errors.append(f"PAYMENT_ADDRESS 格式可能不正确 (长度: {len(cls.PAYMENT_ADDRESS)})")

        # 如果有错误，抛出异常
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

        # 警告信息（不阻止启动）
        if not cls.get_admin_user_ids():
            print("⚠️ 警告: ADMIN_USER_IDS 未设置，人工客服通知功能将无法使用。")

        return True


# 创建全局配置实例
config = Config()

