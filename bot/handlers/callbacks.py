"""
Callback Query 处理器
处理所有 Inline Keyboard 按钮点击事件
"""

from datetime import datetime
from typing import Dict

from telegram import Update
from telegram.ext import ContextTypes

from ..config import config
from ..keyboards.inline import (
    get_main_menu_keyboard,
    get_back_keyboard,
    get_payment_keyboard,
    get_service_name,
    get_job_selection_keyboard,
)
from ..keyboards.reply import get_main_menu_reply_keyboard
from ..services.text_manager import TextManager
from ..services.user_state import user_state_manager, UserState
from ..services.human_agent import HumanAgentService
from .service_responses import get_service_response


# 防抖机制：记录用户最后点击时间
_last_click_time: Dict[int, datetime] = {}
DEBOUNCE_SECONDS = 1.5  # 防抖间隔（秒）


def check_debounce(user_id: int) -> bool:
    """
    检查用户是否在防抖间隔内重复点击

    Args:
        user_id: 用户 ID

    Returns:
        True 表示应该忽略本次点击（在防抖间隔内）
        False 表示可以处理本次点击
    """
    now = datetime.now()
    last_click = _last_click_time.get(user_id)

    if last_click and (now - last_click).total_seconds() < DEBOUNCE_SECONDS:
        return True  # 在防抖间隔内，应该忽略

    _last_click_time[user_id] = now
    return False  # 可以处理


def clear_debounce(user_id: int) -> None:
    """清除用户的防抖记录（用于测试）"""
    if user_id in _last_click_time:
        del _last_click_time[user_id]


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理所有按钮回调
    """
    query = update.callback_query
    user = query.from_user

    # 防抖检查：防止用户快速重复点击
    if check_debounce(user.id):
        await query.answer("请稍后再点击", show_alert=False)
        return

    await query.answer()  # 必须应答，否则按钮会一直 loading

    data = query.data

    # 解析 callback_data
    if ":" not in data:
        return

    action, param = data.split(":", 1)

    print(f"[Callback] 用户 {user.first_name} (ID: {user.id}) 点击了: {action}:{param}")

    if action == "menu":
        await handle_menu(query, param)
    elif action == "service":
        await handle_service(query, param, context)
    elif action == "copy":
        await handle_copy(query, param)
    elif action == "contact":
        await handle_contact(query, param, context)
    elif action == "job":
        await handle_job(query, param)


async def handle_menu(query, param: str) -> None:
    """处理菜单导航"""
    user = query.from_user

    if param == "main":
        # 清除用户当前状态，避免状态残留导致的异常行为
        user_state_manager.clear_state(user.id)

        # 发送欢迎消息并显示底部 Reply Keyboard（10个功能按钮）
        # 使用 TextManager 动态加载，支持热加载
        welcome_text = TextManager.get("menu_welcome")
        await query.message.reply_text(
            text=welcome_text,
            reply_markup=get_main_menu_reply_keyboard(),
        )

        # 发送入职流程介绍 + 岗位选择按钮
        job_intro = TextManager.get("job_intro", "")
        if job_intro:
            await query.message.reply_text(
                text=job_intro,
                reply_markup=get_job_selection_keyboard(),
            )


async def handle_job(query, param: str) -> None:
    """处理岗位选择按钮"""
    user = query.from_user

    # 从配置中获取岗位详情
    jobs = TextManager.get_dict("jobs")
    job_data = jobs.get(param)

    if not job_data:
        await query.message.reply_text("岗位信息暂不可用，请联系客服。")
        return

    job_text = job_data.get("text", "")
    job_title = job_data.get("title", "未知岗位")

    # 替换占位符（收款地址等）
    job_text = job_text.replace("{PAYMENT_ADDRESS}", config.PAYMENT_ADDRESS)

    print(f"[Job] 用户 {user.first_name} (ID: {user.id}) 查看岗位: {job_title}")

    # 发送岗位详情 + 返回主菜单按钮
    await query.message.reply_text(
        text=job_text,
        reply_markup=get_back_keyboard(),
    )


async def handle_service(query, param: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理服务按钮"""
    user = query.from_user
    service_name = get_service_name(param)

    # 获取服务响应内容（使用动态加载，支持热加载）
    response_data = get_service_response(param)
    if not response_data:
        await query.message.reply_text("服务暂不可用，请联系客服。")
        return
    
    response_type = response_data.get("type")
    response_text = response_data.get("text", "")
    follow_up_text = response_data.get("follow_up", "")
    
    if response_type == "auto_reply_with_payment":
        # 自动回复 + 付款信息 (拉专群、开公群、买广告、买会员)
        await query.message.reply_text(text=response_text)
        
        if follow_up_text:
            await query.message.reply_text(
                text=follow_up_text,
                reply_markup=get_payment_keyboard(param),
            )
        
        # 设置用户状态为等待上押截图
        state_map = {
            "la_zhuan": UserState.WAITING_DEPOSIT_LA_ZHUAN,
            "kai_gong": UserState.WAITING_DEPOSIT_KAI_GONG,
            "guanggao": UserState.WAITING_DEPOSIT_GUANGGAO,
            "huiyuan": UserState.WAITING_DEPOSIT_HUIYUAN,
        }
        if param in state_map:
            user_state_manager.set_state(user.id, state_map[param], service_name)
    
    elif response_type == "human_transfer":
        # 直接转人工 (业务咨询、纠纷仲裁、资源对接、投诉建议、销群恢复)
        await query.message.reply_text(
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
        await query.message.reply_text(
            text=response_text,
            reply_markup=get_back_keyboard(),
        )
        user_state_manager.set_state(user.id, UserState.WAITING_GROUP_ID, service_name)


async def handle_copy(query, param: str) -> None:
    """处理复制地址"""
    if param == "address":
        address = config.PAYMENT_ADDRESS
        await query.message.reply_text(
            f"📋 收款地址已复制\n\n`{address}`\n\n网络: {config.PAYMENT_NETWORK}",
            parse_mode="Markdown",
        )


async def handle_contact(query, param: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理联系客服"""
    user = query.from_user
    service_name = get_service_name(param) if param != "general" else "通用咨询"
    
    await query.message.reply_text(
        "已收到您的请求，人工客服会优先接待您，请稍候...",
        reply_markup=get_back_keyboard(),
    )
    
    # 通知管理员
    await HumanAgentService.notify_admins(
        context=context,
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        service_type=service_name,
        message="[主动联系客服]",
    )

