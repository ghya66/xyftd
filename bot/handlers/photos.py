"""
图片消息处理器
处理用户发送的图片（主要用于检测付款截图）
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.inline import get_back_keyboard, get_service_name
from ..services.user_state import user_state_manager, UserState
from ..services.human_agent import HumanAgentService


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理用户发送的图片
    
    如果用户在等待上押截图状态，自动触发人工客服通知
    """
    user = update.effective_user
    state = user_state_manager.get_state(user.id)
    state_data = user_state_manager.get_state_data(user.id)
    
    # 获取图片描述文字（如果有）
    caption = update.message.caption or ""
    
    print(f"[Photo] 用户 {user.first_name} (ID: {user.id}) 发送了图片, 状态: {state.value}")
    
    if user_state_manager.is_waiting_deposit(user.id):
        # 用户在等待上押截图状态 - 触发条件转人工
        service_type = state_data.service_type if state_data else "未知服务"

        # 通知管理员
        notify_success = await HumanAgentService.notify_admins(
            context=context,
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            service_type=service_type,
            message=caption if caption else "[发送了付款截图]",
            has_photo=True,
        )

        # 转发图片给管理员
        photo_success = await forward_photo_to_admins(update, context, service_type)

        # 根据通知结果发送不同的确认消息
        if notify_success and photo_success:
            await update.message.reply_text(
                "✅ 已收到您的截图！\n\n"
                "人工客服会优先接待您，请稍候...\n"
                "如有紧急需求请点击下方按钮联系客服。",
                reply_markup=get_back_keyboard(),
            )
        else:
            # 通知失败时，向用户发送友好提示
            await update.message.reply_text(
                "✅ 已收到您的截图！\n\n"
                "⚠️ 系统繁忙，客服通知可能有延迟。\n"
                "如长时间未收到回复，请点击下方按钮重新联系客服。",
                reply_markup=get_back_keyboard(),
            )

        # 更新用户状态为人工会话
        user_state_manager.set_state(user.id, UserState.IN_HUMAN_SESSION, service_type)

    elif state == UserState.IN_HUMAN_SESSION:
        # 已在人工会话中 - 转发图片
        service_type = state_data.service_type if state_data else "未知服务"

        photo_success = await forward_photo_to_admins(update, context, service_type)

        if photo_success:
            await update.message.reply_text("已收到图片，客服会尽快处理。")
        else:
            await update.message.reply_text(
                "已收到图片。\n\n"
                "⚠️ 系统繁忙，转发可能有延迟，请稍候。"
            )
    
    else:
        # 其他状态 - 提示用户先选择服务
        await update.message.reply_text(
            "请先选择您需要的服务，再发送相关截图。\n\n"
            "发送 /start 开始使用机器人。"
        )


async def forward_photo_to_admins(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service_type: str
) -> bool:
    """
    将用户发送的图片转发给所有管理员

    Returns:
        是否成功转发给至少一个管理员
    """
    from ..config import config

    user = update.effective_user
    admin_ids = config.get_admin_user_ids()

    if not admin_ids:
        print("警告: 没有配置管理员，无法转发图片")
        return False

    # 获取图片
    photo = update.message.photo[-1]  # 获取最高清晰度的图片
    caption = update.message.caption or ""

    user_link = f"@{user.username}" if user.username else f"用户ID: {user.id}"
    forward_caption = f"📷 来自 {user.first_name} ({user_link})\n服务: {service_type}\n\n{caption}"

    success_count = 0
    for admin_id in admin_ids:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=forward_caption[:1024],  # Telegram 限制
            )
            success_count += 1
        except Exception as e:
            print(f"转发图片给管理员 {admin_id} 失败: {e}")

    return success_count > 0

