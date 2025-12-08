"""
/start 命令处理器
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.inline import get_entry_keyboard
from ..services.text_manager import TextManager
from ..services.user_state import user_state_manager


def get_welcome_message() -> str:
    """获取欢迎消息（从 TextManager 加载，支持热加载）"""
    return TextManager.get("welcome_message")


# 为了向后兼容测试，保留 WELCOME_MESSAGE 变量
WELCOME_MESSAGE = get_welcome_message()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /start 命令

    发送招聘信息 + Inline入口按钮
    用户点击入口按钮后才显示底部功能键盘
    """
    user = update.effective_user

    # 清除用户之前的状态
    user_state_manager.clear_state(user.id)

    # 发送招聘信息 + Inline入口按钮（使用动态加载支持热加载）
    await update.message.reply_text(
        text=get_welcome_message(),
        reply_markup=get_entry_keyboard(),
    )

    print(f"[/start] 用户 {user.first_name} (ID: {user.id}) 启动了机器人")

