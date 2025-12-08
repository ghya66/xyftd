"""
土豆担保机器人 - 主入口文件

100% 复刻 @tddbo4bot 的功能和交互流程
"""

import html
import logging
import traceback
from telegram import Update, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.error import NetworkError, TimedOut, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .config import config, Config
from .handlers import (
    start_command,
    button_callback,
    message_handler,
    photo_handler,
    reload_command,
    config_command,
)


# Bot Commands 配置
# 普通用户可见的命令
BOT_COMMANDS_DEFAULT = [
    BotCommand("start", "开始使用机器人"),
]

# 管理员可见的完整命令
BOT_COMMANDS_ADMIN = [
    BotCommand("start", "开始使用机器人"),
    BotCommand("reload", "重新加载配置"),
    BotCommand("config", "查看当前配置"),
]


async def post_init(application: Application) -> None:
    """
    应用初始化后的回调
    用于设置 Bot Commands 菜单

    命令可见性策略：
    - 普通用户：只能看到 /start 命令
    - 管理员：可以看到所有命令（/start, /reload, /config）
    """
    logger = logging.getLogger(__name__)

    try:
        # 1. 设置默认命令（对所有普通用户可见）
        await application.bot.set_my_commands(
            commands=BOT_COMMANDS_DEFAULT,
            scope=BotCommandScopeDefault()
        )
        logger.info(f"✅ 默认命令已注册: {[cmd.command for cmd in BOT_COMMANDS_DEFAULT]}")

        # 2. 为每个管理员设置完整命令菜单
        admin_ids = Config.get_admin_user_ids()
        for admin_id in admin_ids:
            try:
                await application.bot.set_my_commands(
                    commands=BOT_COMMANDS_ADMIN,
                    scope=BotCommandScopeChat(chat_id=admin_id)
                )
                logger.info(f"✅ 管理员 {admin_id} 命令已注册: {[cmd.command for cmd in BOT_COMMANDS_ADMIN]}")
            except Exception as e:
                logger.warning(f"⚠️ 为管理员 {admin_id} 注册命令失败: {e}")

        if admin_ids:
            logger.info(f"✅ 已为 {len(admin_ids)} 位管理员设置专属命令菜单")
        else:
            logger.warning("⚠️ 未配置管理员 ID，管理员命令菜单未设置")

    except Exception as e:
        logger.error(f"❌ 注册 Bot Commands 失败: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    全局错误处理器

    记录详细错误日志，并向管理员发送错误通知
    """
    logger = logging.getLogger(__name__)

    # 获取异常信息
    error = context.error

    # 网络相关错误 - 只记录警告，不通知管理员
    if isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"网络错误 (可自动恢复): {error}")
        return

    # 记录完整错误日志
    logger.error(f"处理更新时发生异常: {error}")

    # 构建详细的错误追踪信息
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)

    # 记录完整堆栈到日志
    logger.error(f"异常堆栈:\n{tb_string}")

    # 构建更新信息
    update_str = ""
    if isinstance(update, Update):
        update_str = f"Update ID: {update.update_id}\n"
        if update.effective_user:
            user = update.effective_user
            update_str += f"用户: {user.first_name} (ID: {user.id})\n"
        if update.effective_message:
            msg = update.effective_message
            update_str += f"消息: {msg.text[:50] if msg.text else '[非文本消息]'}...\n"

    # 向管理员发送错误通知
    admin_ids = config.get_admin_user_ids()
    if admin_ids:
        # 构建错误通知消息（限制长度）
        error_message = f"""⚠️ <b>Bot 发生错误</b>

<b>错误类型:</b> {html.escape(type(error).__name__)}
<b>错误信息:</b> {html.escape(str(error)[:200])}

<b>更新信息:</b>
<pre>{html.escape(update_str)}</pre>

<b>堆栈信息:</b>
<pre>{html.escape(tb_string[-1000:])}</pre>
"""

        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=error_message,
                    parse_mode="HTML",
                )
            except TelegramError as e:
                logger.error(f"发送错误通知给管理员 {admin_id} 失败: {e}")


def setup_logging() -> None:
    """配置日志"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler()]
    
    if config.LOG_FILE:
        handlers.append(logging.FileHandler(config.LOG_FILE, encoding="utf-8"))
    
    logging.basicConfig(
        format=log_format,
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        handlers=handlers,
    )
    
    # 减少第三方库的日志输出
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


def main() -> None:
    """
    启动机器人
    """
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 验证配置
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        print(f"\n❌ 错误: {e}")
        print("\n请按以下步骤配置:")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 中填入 BOT_TOKEN")
        print("3. 重新运行机器人")
        return
    
    logger.info(f"正在启动 {config.BOT_NAME} 机器人...")
    
    # 创建应用 (包含 post_init 回调用于注册 Bot Commands)
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # 注册处理器

    # 1. /start 命令
    application.add_handler(CommandHandler("start", start_command))

    # 2. 管理员命令
    application.add_handler(CommandHandler("reload", reload_command))
    application.add_handler(CommandHandler("config", config_command))

    # 3. Callback Query (按钮点击)
    application.add_handler(CallbackQueryHandler(button_callback))

    # 4. 图片消息 (优先级高于文本)
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # 5. 文本消息
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # 6. 全局错误处理器
    application.add_error_handler(error_handler)

    # 启动信息
    admin_ids = config.get_admin_user_ids()
    logger.info(f"机器人名称: {config.BOT_NAME}")
    logger.info(f"管理员数量: {len(admin_ids)}")
    logger.info(f"收款地址: {config.PAYMENT_ADDRESS}")
    logger.info(f"日志级别: {config.LOG_LEVEL}")
    
    print(f"""
╔══════════════════════════════════════════════════╗
║       🥔 土豆担保机器人 已启动                    ║
╠══════════════════════════════════════════════════╣
║  名称: {config.BOT_NAME:<40} ║
║  管理员: {len(admin_ids)} 人                                    ║
║  日志级别: {config.LOG_LEVEL:<36} ║
╠══════════════════════════════════════════════════╣
║  按 Ctrl+C 停止机器人                             ║
╚══════════════════════════════════════════════════╝
    """)
    
    # 开始轮询
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

