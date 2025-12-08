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


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /reply 命令
    管理员通过机器人回复用户
    仅管理员可用

    支持发送：纯文本、图片、视频、文件

    用法:
      /reply <user_id> <消息内容>           - 发送纯文本
      /reply <user_id> [可选说明] + 图片    - 发送图片
      /reply <user_id> [可选说明] + 视频    - 发送视频
      /reply <user_id> [可选说明] + 文件    - 发送文件

    示例:
      /reply 123456789 您好，您的业务已处理完成
      /reply 123456789 这是付款凭证 + [附带图片]
    """
    user = update.effective_user
    message = update.message

    # 权限检查
    if not is_admin(user.id):
        await message.reply_text("⛔ 您没有权限执行此命令")
        print(f"[/reply] 非管理员 {user.first_name} (ID: {user.id}) 尝试执行 reply 命令")
        return

    # 检测消息是否包含媒体文件
    has_photo = message.photo and len(message.photo) > 0
    has_video = message.video is not None
    has_document = message.document is not None
    has_media = has_photo or has_video or has_document

    # 解析命令参数
    # 如果有媒体文件，只需要 user_id（文字说明可选）
    # 如果没有媒体文件，需要 user_id 和消息内容
    if not context.args or len(context.args) < 1:
        await message.reply_text(
            "❌ 命令格式错误\n\n"
            "**用法:**\n"
            "📝 纯文本: `/reply <用户ID> <消息内容>`\n"
            "🖼️ 图片: `/reply <用户ID> [可选说明]` \\+ 附带图片\n"
            "🎬 视频: `/reply <用户ID> [可选说明]` \\+ 附带视频\n"
            "📎 文件: `/reply <用户ID> [可选说明]` \\+ 附带文件\n\n"
            "**示例:**\n"
            "`/reply 123456789 您好，您的业务已处理完成`\n"
            "`/reply 123456789 这是付款凭证` \\+ 附带图片\n\n"
            "**提示:** 用户 ID 可以从客服通知消息中获取",
            parse_mode="Markdown"
        )
        return

    # 解析用户 ID
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await message.reply_text(
            "❌ 用户 ID 格式错误\n\n"
            "用户 ID 必须是纯数字，例如: `123456789`",
            parse_mode="Markdown"
        )
        return

    # 提取文字说明（跳过 user_id 参数，合并剩余所有参数）
    caption_text = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    # 如果没有媒体文件，文字内容必填
    if not has_media and not caption_text.strip():
        await message.reply_text(
            "❌ 消息内容不能为空\n\n"
            "发送纯文本时，消息内容为必填项。\n"
            "如需发送图片/视频/文件，请附带媒体文件。"
        )
        return

    try:
        # 构建回复前缀
        reply_prefix = "💬 客服回复"

        if has_photo:
            # 发送图片（获取最大尺寸的图片）
            photo_file_id = message.photo[-1].file_id
            full_caption = f"{reply_prefix}:\n\n{caption_text}" if caption_text else reply_prefix

            await context.bot.send_photo(
                chat_id=target_user_id,
                photo=photo_file_id,
                caption=full_caption
            )
            media_type = "图片"

        elif has_video:
            # 发送视频
            video_file_id = message.video.file_id
            full_caption = f"{reply_prefix}:\n\n{caption_text}" if caption_text else reply_prefix

            await context.bot.send_video(
                chat_id=target_user_id,
                video=video_file_id,
                caption=full_caption
            )
            media_type = "视频"

        elif has_document:
            # 发送文件
            document_file_id = message.document.file_id
            full_caption = f"{reply_prefix}:\n\n{caption_text}" if caption_text else reply_prefix

            await context.bot.send_document(
                chat_id=target_user_id,
                document=document_file_id,
                caption=full_caption
            )
            media_type = "文件"

        else:
            # 发送纯文本消息
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"{reply_prefix}:\n\n{caption_text}"
            )
            media_type = "文本"

        # 通知管理员发送成功
        content_preview = caption_text[:100] if caption_text else "[无文字说明]"
        content_suffix = "..." if len(caption_text) > 100 else ""
        await message.reply_text(
            f"✅ 消息已发送\n\n"
            f"👤 目标用户 ID: `{target_user_id}`\n"
            f"📦 消息类型: {media_type}\n"
            f"💬 内容: {content_preview}{content_suffix}",
            parse_mode="Markdown"
        )

        log_content = caption_text[:50] if caption_text else "[无文字]"
        print(f"[/reply] 管理员 {user.first_name} (ID: {user.id}) 向用户 {target_user_id} 发送{media_type}: {log_content}...")

    except Exception as e:
        error_msg = str(e)
        await message.reply_text(
            f"❌ 发送失败\n\n"
            f"**错误:** {error_msg}\n\n"
            f"**可能原因:**\n"
            f"1\\. 用户 ID 不存在\n"
            f"2\\. 用户已阻止/删除机器人\n"
            f"3\\. 用户从未与机器人对话过",
            parse_mode="Markdown"
        )
        print(f"[/reply] 管理员 {user.first_name} 向用户 {target_user_id} 发送消息失败: {e}")

