"""
/start 命令处理器
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.inline import get_entry_keyboard
from ..keyboards.reply import get_main_menu_reply_keyboard
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

    方案 A：发送两条消息
    - 第一条：招聘信息 + Inline 入口按钮
    - 第二条：提示文本 + 底部功能键盘（Reply Keyboard）
    """
    user = update.effective_user

    # 清除用户之前的状态
    user_state_manager.clear_state(user.id)

    # 第一条消息：招聘信息 + Inline 入口按钮
    await update.message.reply_text(
        text=get_welcome_message(),
        reply_markup=get_entry_keyboard(),
    )

    # 第二条消息：提示文本 + 底部 Reply Keyboard（10个功能按钮）
    await update.message.reply_text(
        text="请选择您需要的服务：",
        reply_markup=get_main_menu_reply_keyboard(),
    )

    print(f"[/start] 用户 {user.first_name} (ID: {user.id}) 启动了机器人")

