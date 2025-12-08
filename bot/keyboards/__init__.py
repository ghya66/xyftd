"""
键盘定义模块
"""

from .inline import (
    get_entry_keyboard,
    get_main_menu_keyboard,
    get_back_keyboard,
    get_payment_keyboard,
    get_contact_keyboard,
)

from .reply import (
    get_main_menu_reply_keyboard,
    is_menu_button,
    get_service_code_from_button,
    REPLY_BUTTON_TO_SERVICE,
)

__all__ = [
    "get_entry_keyboard",
    "get_main_menu_keyboard",
    "get_back_keyboard",
    "get_payment_keyboard",
    "get_contact_keyboard",
    "get_main_menu_reply_keyboard",
    "is_menu_button",
    "get_service_code_from_button",
    "REPLY_BUTTON_TO_SERVICE",
]

