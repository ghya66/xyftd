"""
管理员命令处理器
/reload - 热加载配置文件
/config - 查看当前配置
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..config import config
from ..services.text_manager import TextManager


def is_admin(user_id: int) -> bool:
    """检查用户是否是管理员"""
    admin_ids = config.get_admin_user_ids()
    return user_id in admin_ids


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /reload 命令
    热加载 config/texts.json 配置文件
    仅管理员可用
    """
    user = update.effective_user
    
    # 权限检查
    if not is_admin(user.id):
        await update.message.reply_text("⛔ 您没有权限执行此命令")
        print(f"[/reload] 非管理员 {user.first_name} (ID: {user.id}) 尝试执行 reload 命令")
        return
    
    # 执行热加载
    success = TextManager.reload()
    
    if success:
        version = TextManager.get_version()
        load_time = TextManager.get_last_load_time()
        time_str = load_time.strftime("%Y-%m-%d %H:%M:%S") if load_time else "未知"
        
        await update.message.reply_text(
            f"✅ 配置文件已重新加载\n\n"
            f"📄 版本: {version}\n"
            f"🕐 加载时间: {time_str}"
        )
        print(f"[/reload] 管理员 {user.first_name} (ID: {user.id}) 成功重新加载配置")
    else:
        await update.message.reply_text(
            "❌ 配置文件加载失败\n\n"
            "请检查:\n"
            "1. config/texts.json 文件是否存在\n"
            "2. JSON 格式是否正确"
        )
        print(f"[/reload] 管理员 {user.first_name} (ID: {user.id}) 加载配置失败")


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /config 命令
    显示当前配置信息
    仅管理员可用
    """
    user = update.effective_user
    
    # 权限检查
    if not is_admin(user.id):
        await update.message.reply_text("⛔ 您没有权限执行此命令")
        print(f"[/config] 非管理员 {user.first_name} (ID: {user.id}) 尝试执行 config 命令")
        return
    
    # 收集配置信息
    admin_ids = config.get_admin_user_ids()
    version = TextManager.get_version()
    load_time = TextManager.get_last_load_time()
    time_str = load_time.strftime("%Y-%m-%d %H:%M:%S") if load_time else "未知"
    
    # 获取按钮配置预览
    buttons = TextManager.get_dict("buttons")
    button_count = len(buttons) if buttons else 0
    
    # 获取服务配置预览
    services = TextManager.get_dict("services")
    service_count = len(services) if services else 0
    
    config_text = (
        f"⚙️ **土豆担保机器人配置**\n\n"
        f"**基础配置**\n"
        f"• 机器人名称: {config.BOT_NAME}\n"
        f"• 收款地址: `{config.PAYMENT_ADDRESS[:20]}...`\n"
        f"• 管理员数量: {len(admin_ids)} 人\n"
        f"• 日志级别: {config.LOG_LEVEL}\n\n"
        f"**文案配置**\n"
        f"• 配置版本: {version}\n"
        f"• 加载时间: {time_str}\n"
        f"• 按钮数量: {button_count} 个\n"
        f"• 服务数量: {service_count} 个\n\n"
        f"💡 使用 /reload 命令可以热加载配置文件"
    )
    
    await update.message.reply_text(config_text, parse_mode="Markdown")
    print(f"[/config] 管理员 {user.first_name} (ID: {user.id}) 查看配置信息")

