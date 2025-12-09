"""
文本消息处理器
处理用户发送的文本消息
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..config import config
from ..keyboards.inline import get_back_keyboard, get_payment_keyboard, get_service_name
from ..keyboards.reply import get_main_menu_reply_keyboard, is_menu_button, get_service_code_from_button
from ..services.user_state import user_state_manager, UserState
from ..services.group_verify import GroupVerifyService
from ..services.human_agent import HumanAgentService
from .service_responses import get_service_response


def replace_placeholders(text: str) -> str:
    """替换文案中的占位符"""
    return text.format(PAYMENT_ADDRESS=config.PAYMENT_ADDRESS)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理用户发送的文本消息
    """
    user = update.effective_user
    text = update.message.text.strip()

    # 获取用户当前状态
    state = user_state_manager.get_state(user.id)

    print(f"[Message] 用户 {user.first_name} (ID: {user.id}) 状态: {state.value}, 消息: {text[:50]}...")

    # 优先检查是否是底部菜单按钮点击
    if is_menu_button(text):
        await handle_menu_button(update, context, text)
        return

    if state == UserState.WAITING_GROUP_ID:
        # 自助验群 - 处理群编号输入
        await handle_group_verify(update, context, text)

    elif state == UserState.IN_HUMAN_SESSION:
        # 人工客服会话 - 转发消息给管理员
        await forward_to_human(update, context, text)

    elif user_state_manager.is_waiting_deposit(user.id):
        # 等待上押截图状态 - 提示用户发送截图
        await update.message.reply_text(
            "请发送上押/付款截图，我们会优先分配客服接待您。\n\n"
            "如需取消操作，请点击返回主菜单。",
            reply_markup=get_back_keyboard(),
        )

    else:
        # 默认状态 - 显示底部菜单
        await update.message.reply_text(
            "请选择您需要的服务，或发送 /start 重新开始：",
            reply_markup=get_main_menu_reply_keyboard(),
        )


async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str) -> None:
    """
    处理底部菜单按钮点击
    """
    user = update.effective_user
    service_code = get_service_code_from_button(button_text)
    service_name = button_text

    print(f"[MenuButton] 用户 {user.first_name} (ID: {user.id}) 点击了: {button_text} -> {service_code}")

    # 获取服务响应内容（使用动态加载，支持热加载）
    response_data = get_service_response(service_code)
    if not response_data:
        await update.message.reply_text("服务暂不可用，请联系客服。")
        return

    response_type = response_data.get("type")
    response_text = response_data.get("text", "")
    follow_up_text = response_data.get("follow_up", "")

    # 替换文案中的占位符（如收款地址）
    response_text = replace_placeholders(response_text)
    follow_up_text = replace_placeholders(follow_up_text)

    if response_type == "auto_reply_with_payment":
        # 自动回复 + 付款信息 (拉专群、开公群、买广告、买会员)
        await update.message.reply_text(text=response_text)

        if follow_up_text:
            await update.message.reply_text(
                text=follow_up_text,
                reply_markup=get_payment_keyboard(service_code),
            )

        # 设置用户状态为等待上押截图
        state_map = {
            "la_zhuan": UserState.WAITING_DEPOSIT_LA_ZHUAN,
            "kai_gong": UserState.WAITING_DEPOSIT_KAI_GONG,
            "guanggao": UserState.WAITING_DEPOSIT_GUANGGAO,
            "huiyuan": UserState.WAITING_DEPOSIT_HUIYUAN,
        }
        if service_code in state_map:
            user_state_manager.set_state(user.id, state_map[service_code], service_name)

    elif response_type == "human_transfer":
        # 直接转人工 (业务咨询、纠纷仲裁、资源对接、投诉建议、销群恢复)
        await update.message.reply_text(
            text=response_text,
            reply_markup=get_back_keyboard(),
        )

        # 设置用户状态
        user_state_manager.set_state(user.id, UserState.IN_HUMAN_SESSION, service_name)

        # 通知管理员
        await HumanAgentService.notify_admins(
            context=context,
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            service_type=service_name,
            message=f"[点击了 {service_name} 按钮]",
        )

    elif response_type == "auto_reply_with_input":
        # 自动回复 + 等待用户输入 (自助验群)
        await update.message.reply_text(
            text=response_text,
            reply_markup=get_back_keyboard(),
        )
        user_state_manager.set_state(user.id, UserState.WAITING_GROUP_ID, service_name)


async def handle_group_verify(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """
    处理自助验群
    """
    user = update.effective_user
    
    # 解析群编号
    group_id = GroupVerifyService.parse_group_id(text)
    
    if group_id is None:
        await update.message.reply_text(
            "❌ 群编号格式不正确\n\n"
            "请输入正确的群编号格式，如:\n"
            "• 专群A12345\n"
            "• 公群12345\n"
            "• 飞博13",
            reply_markup=get_back_keyboard(),
        )
        return
    
    # 查询验证结果
    result = GroupVerifyService.format_verify_result(group_id)
    
    await update.message.reply_text(
        result,
        reply_markup=get_back_keyboard(),
    )
    
    # 清除等待状态
    user_state_manager.clear_state(user.id)


async def forward_to_human(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """
    转发消息给人工客服
    """
    user = update.effective_user
    state_data = user_state_manager.get_state_data(user.id)
    service_type = state_data.service_type if state_data else "未知服务"
    
    # 通知管理员
    await HumanAgentService.notify_admins(
        context=context,
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        service_type=service_type,
        message=text,
    )
    
    await update.message.reply_text(
        "已收到您的消息，客服会尽快回复您。",
    )

