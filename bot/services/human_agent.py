"""
人工客服通知服务
用于在需要人工介入时通知管理员
"""

from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes

from ..config import config


class HumanAgentService:
    """人工客服通知服务"""
    
    # 立即转人工的服务类型
    IMMEDIATE_HUMAN_SERVICES = [
        "业务咨询",
        "纠纷仲裁", 
        "资源对接",
        "投诉建议",
        "销群恢复",
    ]
    
    # 条件转人工的服务类型 (用户发送截图后触发)
    CONDITIONAL_HUMAN_SERVICES = [
        "拉专群",
        "开公群",
        "买广告",
        "买会员",
    ]
    
    @classmethod
    async def notify_admins(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        username: str,
        first_name: str,
        service_type: str,
        message: str = "",
        has_photo: bool = False,
    ) -> bool:
        """
        通知所有管理员有新的客服请求
        
        Args:
            context: Telegram context
            user_id: 用户 ID
            username: 用户名
            first_name: 用户名字
            service_type: 服务类型
            message: 用户消息内容
            has_photo: 是否包含图片
        
        Returns:
            是否成功通知至少一个管理员
        """
        if not config.ENABLE_HUMAN_NOTIFICATION:
            return False
        
        admin_ids = config.get_admin_user_ids()
        if not admin_ids:
            print("警告: 没有配置管理员，无法发送人工客服通知")
            return False
        
        # 构建通知消息
        photo_tag = "📷 [含图片]" if has_photo else ""
        user_link = f"@{username}" if username else f"用户ID: {user_id}"
        
        notification = f"""🔔 新客服请求

👤 用户: {first_name} ({user_link})
📋 服务类型: {service_type}
{photo_tag}

💬 消息内容:
{message if message else "[无文字消息]"}

---
点击用户链接可直接回复"""
        
        success_count = 0
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification,
                )
                success_count += 1
            except Exception as e:
                print(f"发送通知给管理员 {admin_id} 失败: {e}")
        
        return success_count > 0
    
    @classmethod
    def is_immediate_human_service(cls, service_type: str) -> bool:
        """检查是否为立即转人工的服务"""
        return service_type in cls.IMMEDIATE_HUMAN_SERVICES
    
    @classmethod
    def is_conditional_human_service(cls, service_type: str) -> bool:
        """检查是否为条件转人工的服务"""
        return service_type in cls.CONDITIONAL_HUMAN_SERVICES
    
    @classmethod
    def get_human_response(cls, service_type: str) -> str:
        """获取转人工后的自动回复消息"""
        responses = {
            "业务咨询": "你好，土豆担保人工客服，请问有什么可以帮助您？",
            "纠纷仲裁": "你好，土豆担保人工客服，请问有什么可以帮助您？",
            "资源对接": "您好，这里是资源对接板块，请问你是主做什么业务，需要找什么类型的资源。",
            "投诉建议": "您好，这里是土豆担保工作人员投诉通道，投诉哪位工作人员，请将您需要投诉的问题描述清楚。",
            "销群恢复": "您是负责人或者公群老板吗？请准备好原上押地址，并且提供群编号哦。",
        }
        return responses.get(service_type, "人工客服正在接入，请稍候...")

