"""
Reply 键盘定义
底部常驻菜单键盘 (10个功能按钮)
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from ..services.text_manager import TextManager


def get_main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    获取主菜单 Reply Keyboard (10个按钮，2列x5行布局)

    这是显示在输入框下方的底部常驻键盘
    使用 TextManager 动态加载按钮文字，支持热加载
    """
    buttons = TextManager.get_dict("buttons")
    keyboard = [
        [
            KeyboardButton(buttons.get("kai_gong", "开公群")),
            KeyboardButton(buttons.get("la_zhuan", "拉专群")),
        ],
        [
            KeyboardButton(buttons.get("zixun", "业务咨询")),
            KeyboardButton(buttons.get("jiufen", "纠纷仲裁")),
        ],
        [
            KeyboardButton(buttons.get("guanggao", "买广告")),
            KeyboardButton(buttons.get("huiyuan", "买会员")),
        ],
        [
            KeyboardButton(buttons.get("ziyuan", "资源对接")),
            KeyboardButton(buttons.get("tousu", "投诉建议")),
        ],
        [
            KeyboardButton(buttons.get("yanqun", "自助验群")),
            KeyboardButton(buttons.get("xiaoqhf", "销群恢复")),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # 自适应按钮大小
        is_persistent=True,    # 键盘持久显示
    )


def get_button_to_service_map():
    """
    获取按钮文本到服务代码的映射
    使用 TextManager 动态加载，支持热加载
    """
    buttons = TextManager.get_dict("buttons")
    return {
        buttons.get("kai_gong", "开公群"): "kai_gong",
        buttons.get("la_zhuan", "拉专群"): "la_zhuan",
        buttons.get("zixun", "业务咨询"): "zixun",
        buttons.get("jiufen", "纠纷仲裁"): "jiufen",
        buttons.get("guanggao", "买广告"): "guanggao",
        buttons.get("huiyuan", "买会员"): "huiyuan",
        buttons.get("ziyuan", "资源对接"): "ziyuan",
        buttons.get("tousu", "投诉建议"): "tousu",
        buttons.get("yanqun", "自助验群"): "yanqun",
        buttons.get("xiaoqhf", "销群恢复"): "xiaoqhf",
    }


# 为了向后兼容测试，保留静态映射
REPLY_BUTTON_TO_SERVICE = {
    "开公群": "kai_gong",
    "拉专群": "la_zhuan",
    "业务咨询": "zixun",
    "纠纷仲裁": "jiufen",
    "买广告": "guanggao",
    "买会员": "huiyuan",
    "资源对接": "ziyuan",
    "投诉建议": "tousu",
    "自助验群": "yanqun",
    "销群恢复": "xiaoqhf",
}


def is_menu_button(text: str) -> bool:
    """检查文本是否是菜单按钮"""
    button_map = get_button_to_service_map()
    return text in button_map


def get_service_code_from_button(text: str) -> str:
    """从按钮文本获取服务代码"""
    button_map = get_button_to_service_map()
    return button_map.get(text, "")

