"""
Inline 键盘定义
所有 Inline Keyboard 的创建函数
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ..config import config
from ..services.text_manager import TextManager


def get_entry_keyboard() -> InlineKeyboardMarkup:
    """
    获取入口键盘 (/start 命令后显示)
    用户点击此按钮后显示底部功能键盘
    """
    keyboard = [[
        InlineKeyboardButton(
            TextManager.get("buttons.entry", "🔘 点击下方按钮，了解入职流程"),
            callback_data="menu:main"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    获取主菜单键盘 (10个按钮，2列x5行布局)
    使用 TextManager 动态加载按钮文字，支持热加载
    """
    buttons = TextManager.get_dict("buttons")
    keyboard = [
        [
            InlineKeyboardButton(buttons.get("la_zhuan", "拉专群"), callback_data="service:la_zhuan"),
            InlineKeyboardButton(buttons.get("kai_gong", "开公群"), callback_data="service:kai_gong"),
        ],
        [
            InlineKeyboardButton(buttons.get("zixun", "业务咨询"), callback_data="service:zixun"),
            InlineKeyboardButton(buttons.get("jiufen", "纠纷仲裁"), callback_data="service:jiufen"),
        ],
        [
            InlineKeyboardButton(buttons.get("guanggao", "买广告"), callback_data="service:guanggao"),
            InlineKeyboardButton(buttons.get("huiyuan", "买会员"), callback_data="service:huiyuan"),
        ],
        [
            InlineKeyboardButton(buttons.get("ziyuan", "资源对接"), callback_data="service:ziyuan"),
            InlineKeyboardButton(buttons.get("tousu", "投诉建议"), callback_data="service:tousu"),
        ],
        [
            InlineKeyboardButton(buttons.get("yanqun", "自助验群"), callback_data="service:yanqun"),
            InlineKeyboardButton(buttons.get("xiaoqhf", "销群恢复"), callback_data="service:xiaoqhf"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """
    获取返回菜单键盘
    """
    keyboard = [[
        InlineKeyboardButton(
            TextManager.get("buttons.back", "🔙 返回主菜单"),
            callback_data="menu:main"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)


def get_payment_keyboard(service_type: str) -> InlineKeyboardMarkup:
    """
    获取付款相关键盘 (复制地址 + 联系客服 + 返回)
    """
    buttons = TextManager.get_dict("buttons")
    keyboard = [
        [
            InlineKeyboardButton(
                buttons.get("copy_address", "📋 复制地址"),
                callback_data=f"copy:address"
            ),
            InlineKeyboardButton(
                buttons.get("contact_support", "👨‍💼 联系客服"),
                callback_data=f"contact:{service_type}"
            ),
        ],
        [
            InlineKeyboardButton(
                buttons.get("back", "🔙 返回主菜单"),
                callback_data="menu:main"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_contact_keyboard() -> InlineKeyboardMarkup:
    """
    获取联系客服键盘
    """
    buttons = TextManager.get_dict("buttons")
    keyboard = [
        [
            InlineKeyboardButton(
                buttons.get("contact_support", "👨‍💼 联系客服"),
                callback_data="contact:general"
            ),
        ],
        [
            InlineKeyboardButton(
                buttons.get("back", "🔙 返回主菜单"),
                callback_data="menu:main"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_verify_keyboard() -> InlineKeyboardMarkup:
    """
    获取验群结果键盘
    """
    buttons = TextManager.get_dict("buttons")
    keyboard = [
        [
            InlineKeyboardButton(
                buttons.get("continue_verify", "🔄 继续验证"),
                callback_data="service:yanqun"
            ),
            InlineKeyboardButton(
                buttons.get("back", "🔙 返回主菜单"),
                callback_data="menu:main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_service_name(callback_data: str) -> str:
    """
    根据 callback_data 获取服务名称
    使用 TextManager 动态加载，支持热加载
    """
    buttons = TextManager.get_dict("buttons")
    # 服务名称映射（使用配置中的按钮文字）
    service_name_map = {
        "la_zhuan": buttons.get("la_zhuan", "拉专群"),
        "kai_gong": buttons.get("kai_gong", "开公群"),
        "zixun": buttons.get("zixun", "业务咨询"),
        "jiufen": buttons.get("jiufen", "纠纷仲裁"),
        "guanggao": buttons.get("guanggao", "买广告"),
        "huiyuan": buttons.get("huiyuan", "买会员"),
        "ziyuan": buttons.get("ziyuan", "资源对接"),
        "tousu": buttons.get("tousu", "投诉建议"),
        "yanqun": buttons.get("yanqun", "自助验群"),
        "xiaoqhf": buttons.get("xiaoqhf", "销群恢复"),
    }
    return service_name_map.get(callback_data, "未知服务")


# 为了向后兼容测试，保留 SERVICE_NAME_MAP 变量
SERVICE_NAME_MAP = {
    "la_zhuan": "拉专群",
    "kai_gong": "开公群",
    "zixun": "业务咨询",
    "jiufen": "纠纷仲裁",
    "guanggao": "买广告",
    "huiyuan": "买会员",
    "ziyuan": "资源对接",
    "tousu": "投诉建议",
    "yanqun": "自助验群",
    "xiaoqhf": "销群恢复",
}

