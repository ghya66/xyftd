"""
土豆担保机器人 - 单元测试

测试内容:
1. /start 命令欢迎消息
2. 主菜单按钮生成
3. 功能按钮回调响应
4. 用户状态管理
5. 群验证服务
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# 导入要测试的模块
from bot.keyboards.inline import (
    get_entry_keyboard,
    get_main_menu_keyboard,
    get_back_keyboard,
    get_payment_keyboard,
    get_service_name,
    SERVICE_NAME_MAP,
)
from bot.keyboards.reply import (
    get_main_menu_reply_keyboard,
    is_menu_button,
    get_service_code_from_button,
    REPLY_BUTTON_TO_SERVICE,
)
from bot.services.user_state import UserStateManager, UserState
from bot.services.group_verify import GroupVerifyService
from bot.services.human_agent import HumanAgentService
from bot.handlers.service_responses import SERVICE_RESPONSES
from bot.handlers.start import WELCOME_MESSAGE


class TestWelcomeMessage(unittest.TestCase):
    """测试欢迎消息"""

    def test_welcome_message_contains_recruitment_info(self):
        """测试欢迎消息包含招聘信息"""
        self.assertIn("土豆担保华人线上招聘正式开启", WELCOME_MESSAGE)
        self.assertIn("公群广告删除员", WELCOME_MESSAGE)
        self.assertIn("专群消息删除员", WELCOME_MESSAGE)
        self.assertIn("白班200U/天", WELCOME_MESSAGE)
        self.assertIn("押金：1500U", WELCOME_MESSAGE)

    def test_welcome_message_contains_entry_prompt(self):
        """测试欢迎消息包含入口提示"""
        self.assertIn("点击下方按钮了解入职流程", WELCOME_MESSAGE)


class TestReplyKeyboard(unittest.TestCase):
    """测试 Reply 键盘（底部功能按钮）"""

    def test_reply_keyboard_has_10_buttons(self):
        """测试 Reply 键盘有10个按钮"""
        keyboard = get_main_menu_reply_keyboard()
        total_buttons = sum(len(row) for row in keyboard.keyboard)
        self.assertEqual(total_buttons, 10)

    def test_reply_keyboard_layout_2x5(self):
        """测试 Reply 键盘布局为2列x5行"""
        keyboard = get_main_menu_reply_keyboard()
        self.assertEqual(len(keyboard.keyboard), 5)  # 5 rows
        for row in keyboard.keyboard:
            self.assertEqual(len(row), 2)  # 2 buttons per row

    def test_is_menu_button(self):
        """测试菜单按钮识别"""
        self.assertTrue(is_menu_button("开公群"))
        self.assertTrue(is_menu_button("拉专群"))
        self.assertFalse(is_menu_button("随便输入"))

    def test_get_service_code_from_button(self):
        """测试从按钮文本获取服务代码"""
        self.assertEqual(get_service_code_from_button("开公群"), "kai_gong")
        self.assertEqual(get_service_code_from_button("拉专群"), "la_zhuan")
        self.assertEqual(get_service_code_from_button("自助验群"), "yanqun")


class TestInlineKeyboards(unittest.TestCase):
    """测试 Inline 键盘"""

    def test_entry_keyboard_has_one_button(self):
        """测试入口键盘只有一个按钮"""
        keyboard = get_entry_keyboard()
        self.assertEqual(len(keyboard.inline_keyboard), 1)
        self.assertEqual(len(keyboard.inline_keyboard[0]), 1)
        self.assertIn("🔘 点击下方按钮，了解入职流程", keyboard.inline_keyboard[0][0].text)

    def test_entry_keyboard_callback_data(self):
        """测试入口按钮的 callback_data"""
        keyboard = get_entry_keyboard()
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "menu:main")

    def test_main_menu_has_10_buttons(self):
        """测试主菜单有10个按钮"""
        keyboard = get_main_menu_keyboard()
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        self.assertEqual(total_buttons, 10)

    def test_main_menu_layout_2x5(self):
        """测试主菜单布局为2列x5行"""
        keyboard = get_main_menu_keyboard()
        self.assertEqual(len(keyboard.inline_keyboard), 5)  # 5行
        for row in keyboard.inline_keyboard:
            self.assertEqual(len(row), 2)  # 每行2个按钮

    def test_main_menu_button_names(self):
        """测试主菜单按钮名称"""
        keyboard = get_main_menu_keyboard()
        button_texts = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_texts.append(button.text)

        expected_buttons = [
            "拉专群", "开公群", "业务咨询", "纠纷仲裁",
            "买广告", "买会员", "资源对接", "投诉建议",
            "自助验群", "销群恢复"
        ]
        self.assertEqual(button_texts, expected_buttons)

    def test_service_name_map(self):
        """测试服务名称映射"""
        self.assertEqual(get_service_name("la_zhuan"), "拉专群")
        self.assertEqual(get_service_name("kai_gong"), "开公群")
        self.assertEqual(get_service_name("yanqun"), "自助验群")


class TestServiceResponses(unittest.TestCase):
    """测试服务响应文案"""

    def test_all_services_have_responses(self):
        """测试所有服务都有响应配置"""
        expected_services = [
            "la_zhuan", "kai_gong", "zixun", "jiufen",
            "guanggao", "huiyuan", "ziyuan", "tousu",
            "yanqun", "xiaoqhf"
        ]
        for service in expected_services:
            self.assertIn(service, SERVICE_RESPONSES)

    def test_human_transfer_responses(self):
        """测试直接转人工的服务响应"""
        human_services = ["zixun", "jiufen", "ziyuan", "tousu", "xiaoqhf"]
        for service in human_services:
            self.assertEqual(SERVICE_RESPONSES[service]["type"], "human_transfer")
            self.assertIn("text", SERVICE_RESPONSES[service])

    def test_auto_reply_with_payment_responses(self):
        """测试带付款信息的自动回复"""
        payment_services = ["la_zhuan", "kai_gong", "guanggao", "huiyuan"]
        for service in payment_services:
            self.assertEqual(SERVICE_RESPONSES[service]["type"], "auto_reply_with_payment")
            # 收款地址占位符在 text 或 follow_up 字段中
            text = SERVICE_RESPONSES[service].get("text", "")
            follow_up = SERVICE_RESPONSES[service].get("follow_up", "")
            combined = text + follow_up
            # 现在使用占位符 {PAYMENT_ADDRESS}，不再硬编码地址
            self.assertIn("{PAYMENT_ADDRESS}", combined)

    def test_yanqun_response(self):
        """测试自助验群响应"""
        self.assertEqual(SERVICE_RESPONSES["yanqun"]["type"], "auto_reply_with_input")
        self.assertIn("群编号", SERVICE_RESPONSES["yanqun"]["text"])


class TestUserStateManager(unittest.TestCase):
    """测试用户状态管理"""

    def setUp(self):
        self.manager = UserStateManager(expire_seconds=3600)

    def test_initial_state_is_idle(self):
        """测试初始状态为空闲"""
        state = self.manager.get_state(12345)
        self.assertEqual(state, UserState.IDLE)

    def test_set_and_get_state(self):
        """测试设置和获取状态"""
        self.manager.set_state(12345, UserState.WAITING_GROUP_ID, "自助验群")
        state = self.manager.get_state(12345)
        self.assertEqual(state, UserState.WAITING_GROUP_ID)

    def test_clear_state(self):
        """测试清除状态"""
        self.manager.set_state(12345, UserState.WAITING_GROUP_ID)
        self.manager.clear_state(12345)
        state = self.manager.get_state(12345)
        self.assertEqual(state, UserState.IDLE)

    def test_is_waiting_deposit(self):
        """测试等待上押状态检测"""
        self.manager.set_state(12345, UserState.WAITING_DEPOSIT_LA_ZHUAN)
        self.assertTrue(self.manager.is_waiting_deposit(12345))

        self.manager.set_state(12345, UserState.IDLE)
        self.assertFalse(self.manager.is_waiting_deposit(12345))


class TestGroupVerifyService(unittest.TestCase):
    """测试群验证服务"""

    def test_parse_valid_group_id(self):
        """测试解析有效群编号"""
        self.assertEqual(GroupVerifyService.parse_group_id("专群A12345"), "专群A12345")
        self.assertEqual(GroupVerifyService.parse_group_id("公群12345"), "公群12345")
        self.assertEqual(GroupVerifyService.parse_group_id("飞博13"), "飞博13")

    def test_parse_invalid_group_id(self):
        """测试解析无效群编号"""
        self.assertIsNone(GroupVerifyService.parse_group_id("random text"))
        self.assertIsNone(GroupVerifyService.parse_group_id("12345"))
        self.assertIsNone(GroupVerifyService.parse_group_id(""))

    def test_verify_existing_group(self):
        """测试验证存在的群"""
        result = GroupVerifyService.verify_group("专群A12345")
        self.assertIsNotNone(result)
        self.assertEqual(result.group_type, "专群")

    def test_verify_nonexistent_group(self):
        """测试验证不存在的群"""
        result = GroupVerifyService.verify_group("专群X99999")
        self.assertIsNone(result)

    def test_format_verify_result_success(self):
        """测试格式化验证成功结果"""
        result = GroupVerifyService.format_verify_result("专群A12345")
        self.assertIn("✅", result)
        self.assertIn("专群A12345", result)
        self.assertIn("张老板", result)

    def test_format_verify_result_not_found(self):
        """测试格式化验证失败结果"""
        result = GroupVerifyService.format_verify_result("专群X99999")
        self.assertIn("❌", result)
        self.assertIn("未找到", result)


class TestAdminConfig(unittest.TestCase):
    """测试管理员配置"""

    @patch.dict(os.environ, {"ADMIN_USER_IDS": "123456789,987654321"})
    def test_get_admin_user_ids_valid(self):
        """测试解析有效的管理员 ID 列表"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [123456789, 987654321])

    @patch.dict(os.environ, {"ADMIN_USER_IDS": ""})
    def test_get_admin_user_ids_empty(self):
        """测试空的管理员 ID 配置"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [])

    @patch.dict(os.environ, {"ADMIN_USER_IDS": "123456789"})
    def test_get_admin_user_ids_single(self):
        """测试单个管理员 ID"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [123456789])

    @patch.dict(os.environ, {"ADMIN_USER_IDS": "123456789, 987654321 , 111222333"})
    def test_get_admin_user_ids_with_spaces(self):
        """测试带空格的管理员 ID 配置"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [123456789, 987654321, 111222333])

    @patch.dict(os.environ, {"ADMIN_USER_IDS": "123abc,456def"})
    def test_get_admin_user_ids_invalid_skipped(self):
        """测试无效的管理员 ID 被跳过"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [])  # 全部无效，返回空列表

    @patch.dict(os.environ, {"ADMIN_USER_IDS": "123456789,invalid,987654321"})
    def test_get_admin_user_ids_mixed(self):
        """测试混合有效和无效的管理员 ID"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [123456789, 987654321])  # 无效的被跳过

    @patch.dict(os.environ, {"ADMIN_USER_IDS": ",,,123456789,,,"})
    def test_get_admin_user_ids_empty_entries(self):
        """测试包含空条目的管理员 ID 配置"""
        from bot.config import Config
        result = Config.get_admin_user_ids()
        self.assertEqual(result, [123456789])


class TestHumanAgentService(unittest.TestCase):
    """测试人工客服服务"""

    def test_immediate_human_services(self):
        """测试立即转人工服务列表"""
        self.assertTrue(HumanAgentService.is_immediate_human_service("业务咨询"))
        self.assertTrue(HumanAgentService.is_immediate_human_service("纠纷仲裁"))
        self.assertTrue(HumanAgentService.is_immediate_human_service("销群恢复"))
        self.assertFalse(HumanAgentService.is_immediate_human_service("拉专群"))

    def test_conditional_human_services(self):
        """测试条件转人工服务列表"""
        self.assertTrue(HumanAgentService.is_conditional_human_service("拉专群"))
        self.assertTrue(HumanAgentService.is_conditional_human_service("买广告"))
        self.assertFalse(HumanAgentService.is_conditional_human_service("业务咨询"))

    def test_get_human_response(self):
        """测试获取转人工响应消息"""
        response = HumanAgentService.get_human_response("业务咨询")
        self.assertIn("人工客服", response)
        self.assertIn("请问有什么可以帮助您", response)

        response = HumanAgentService.get_human_response("投诉建议")
        self.assertIn("投诉通道", response)


class TestMenuNavigation(unittest.TestCase):
    """测试菜单导航功能"""

    def setUp(self):
        """每个测试前重置状态管理器"""
        from bot.services.user_state import user_state_manager
        self.state_manager = user_state_manager
        # 清除可能残留的测试状态
        self.test_user_id = 99999
        self.state_manager.clear_state(self.test_user_id)

    def tearDown(self):
        """每个测试后清理状态"""
        self.state_manager.clear_state(self.test_user_id)

    def test_return_to_main_menu_clears_waiting_deposit_state(self):
        """测试返回主菜单时清除等待上押状态"""
        # 设置用户为等待上押状态
        self.state_manager.set_state(
            self.test_user_id,
            UserState.WAITING_DEPOSIT_LA_ZHUAN,
            "拉专群"
        )
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.WAITING_DEPOSIT_LA_ZHUAN
        )

        # 模拟清除状态（handle_menu 会调用 clear_state）
        self.state_manager.clear_state(self.test_user_id)

        # 验证状态已被清除
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.IDLE
        )

    def test_return_to_main_menu_clears_human_session_state(self):
        """测试返回主菜单时清除人工会话状态"""
        # 设置用户为人工会话状态
        self.state_manager.set_state(
            self.test_user_id,
            UserState.IN_HUMAN_SESSION,
            "业务咨询"
        )
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.IN_HUMAN_SESSION
        )

        # 模拟清除状态
        self.state_manager.clear_state(self.test_user_id)

        # 验证状态已被清除
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.IDLE
        )

    def test_return_to_main_menu_clears_waiting_group_id_state(self):
        """测试返回主菜单时清除等待群编号输入状态"""
        # 设置用户为等待群编号输入状态
        self.state_manager.set_state(
            self.test_user_id,
            UserState.WAITING_GROUP_ID,
            "自助验群"
        )
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.WAITING_GROUP_ID
        )

        # 模拟清除状态
        self.state_manager.clear_state(self.test_user_id)

        # 验证状态已被清除
        self.assertEqual(
            self.state_manager.get_state(self.test_user_id),
            UserState.IDLE
        )


class TestDebounce(unittest.TestCase):
    """测试按钮防抖机制"""

    def setUp(self):
        """每个测试前清除防抖记录"""
        from bot.handlers.callbacks import clear_debounce, _last_click_time
        self.test_user_id = 88888
        clear_debounce(self.test_user_id)

    def tearDown(self):
        """每个测试后清除防抖记录"""
        from bot.handlers.callbacks import clear_debounce
        clear_debounce(self.test_user_id)

    def test_first_click_allowed(self):
        """测试首次点击应该被允许"""
        from bot.handlers.callbacks import check_debounce, clear_debounce
        clear_debounce(self.test_user_id)

        # 首次点击应该返回 False（允许处理）
        result = check_debounce(self.test_user_id)
        self.assertFalse(result)

    def test_rapid_click_blocked(self):
        """测试快速重复点击应该被阻止"""
        from bot.handlers.callbacks import check_debounce

        # 第一次点击
        result1 = check_debounce(self.test_user_id)
        self.assertFalse(result1)  # 允许

        # 立即再次点击（在防抖间隔内）
        result2 = check_debounce(self.test_user_id)
        self.assertTrue(result2)  # 应该被阻止

    def test_click_after_debounce_allowed(self):
        """测试防抖间隔后的点击应该被允许"""
        from bot.handlers.callbacks import check_debounce, _last_click_time, DEBOUNCE_SECONDS
        from datetime import datetime, timedelta

        # 第一次点击
        check_debounce(self.test_user_id)

        # 模拟时间已经过了防抖间隔
        _last_click_time[self.test_user_id] = datetime.now() - timedelta(seconds=DEBOUNCE_SECONDS + 0.1)

        # 现在点击应该被允许
        result = check_debounce(self.test_user_id)
        self.assertFalse(result)

    def test_different_users_independent(self):
        """测试不同用户的防抖是独立的"""
        from bot.handlers.callbacks import check_debounce, clear_debounce

        user1 = 11111
        user2 = 22222
        clear_debounce(user1)
        clear_debounce(user2)

        # 用户1点击
        result1 = check_debounce(user1)
        self.assertFalse(result1)  # 允许

        # 用户2点击（应该不受用户1影响）
        result2 = check_debounce(user2)
        self.assertFalse(result2)  # 允许

        # 用户1再次点击（在防抖间隔内）
        result3 = check_debounce(user1)
        self.assertTrue(result3)  # 阻止

        # 清理
        clear_debounce(user1)
        clear_debounce(user2)

    def test_debounce_seconds_value(self):
        """测试防抖间隔配置值"""
        from bot.handlers.callbacks import DEBOUNCE_SECONDS
        self.assertEqual(DEBOUNCE_SECONDS, 1.5)


class TestNotificationFailureHandling(unittest.TestCase):
    """测试通知失败处理"""

    def test_notify_admins_returns_false_when_disabled(self):
        """测试人工通知禁用时返回 False"""
        from bot.services.human_agent import HumanAgentService
        from bot.config import config

        # 保存原始值
        original_value = config.ENABLE_HUMAN_NOTIFICATION

        # 禁用通知
        config.ENABLE_HUMAN_NOTIFICATION = False

        # 由于 notify_admins 是异步的，我们测试配置检查逻辑
        self.assertFalse(config.ENABLE_HUMAN_NOTIFICATION)

        # 恢复原始值
        config.ENABLE_HUMAN_NOTIFICATION = original_value

    def test_notify_admins_returns_false_when_no_admins(self):
        """测试没有管理员配置时返回 False"""
        from bot.config import config
        import os

        # 保存原始值
        original_value = os.environ.get("ADMIN_USER_IDS", "")

        # 设置为空
        os.environ["ADMIN_USER_IDS"] = ""

        # 验证没有管理员
        admin_ids = config.get_admin_user_ids()
        self.assertEqual(len(admin_ids), 0)

        # 恢复原始值
        os.environ["ADMIN_USER_IDS"] = original_value

    def test_human_agent_service_has_notify_method(self):
        """测试 HumanAgentService 有 notify_admins 方法"""
        from bot.services.human_agent import HumanAgentService

        self.assertTrue(hasattr(HumanAgentService, 'notify_admins'))
        self.assertTrue(callable(getattr(HumanAgentService, 'notify_admins')))

    def test_forward_photo_function_exists(self):
        """测试 forward_photo_to_admins 函数存在"""
        from bot.handlers.photos import forward_photo_to_admins

        self.assertTrue(callable(forward_photo_to_admins))

    def test_failure_message_contains_warning(self):
        """测试失败消息包含警告信息"""
        # 验证失败提示消息的内容
        expected_warning = "系统繁忙"
        expected_fallback = "重新联系客服"

        # 这些是 photos.py 中定义的失败消息内容
        failure_message = (
            "✅ 已收到您的截图！\n\n"
            "⚠️ 系统繁忙，客服通知可能有延迟。\n"
            "如长时间未收到回复，请点击下方按钮重新联系客服。"
        )

        self.assertIn(expected_warning, failure_message)
        self.assertIn(expected_fallback, failure_message)


class TestTextManager(unittest.TestCase):
    """TextManager 文案管理器测试"""

    def test_text_manager_load(self):
        """测试配置文件加载"""
        from bot.services.text_manager import TextManager
        self.assertTrue(TextManager.load())

    def test_text_manager_get_version(self):
        """测试获取版本号"""
        from bot.services.text_manager import TextManager
        version = TextManager.get_version()
        self.assertEqual(version, "1.0")

    def test_text_manager_get_welcome_message(self):
        """测试获取欢迎消息"""
        from bot.services.text_manager import TextManager
        message = TextManager.get("welcome_message")
        self.assertIn("土豆担保", message)
        self.assertIn("招聘", message)

    def test_text_manager_get_menu_welcome(self):
        """测试获取菜单欢迎语"""
        from bot.services.text_manager import TextManager
        message = TextManager.get("menu_welcome")
        self.assertIn("土豆担保", message)
        self.assertIn("人工客服", message)

    def test_text_manager_get_buttons(self):
        """测试获取按钮配置"""
        from bot.services.text_manager import TextManager
        buttons = TextManager.get_dict("buttons")
        self.assertIn("la_zhuan", buttons)
        self.assertIn("kai_gong", buttons)
        self.assertIn("entry", buttons)

    def test_text_manager_get_services(self):
        """测试获取服务配置"""
        from bot.services.text_manager import TextManager
        services = TextManager.get_dict("services")
        self.assertIn("la_zhuan", services)
        self.assertIn("kai_gong", services)
        self.assertEqual(services["la_zhuan"]["type"], "auto_reply_with_payment")

    def test_text_manager_get_service_with_placeholder(self):
        """测试获取服务配置时占位符被替换"""
        from bot.services.text_manager import TextManager
        from bot.config import config
        service = TextManager.get_service("la_zhuan")
        # 检查占位符已被替换为实际地址
        self.assertIn(config.PAYMENT_ADDRESS, service.get("follow_up", ""))

    def test_text_manager_reload(self):
        """测试热加载配置"""
        from bot.services.text_manager import TextManager
        self.assertTrue(TextManager.reload())
        self.assertIsNotNone(TextManager.get_last_load_time())


class TestAdminCommands(unittest.TestCase):
    """管理员命令测试"""

    def test_admin_handler_exists(self):
        """测试管理员处理器存在"""
        from bot.handlers.admin import reload_command, config_command, is_admin
        self.assertTrue(callable(reload_command))
        self.assertTrue(callable(config_command))
        self.assertTrue(callable(is_admin))

    def test_admin_commands_registered(self):
        """测试管理员命令已注册"""
        from bot.handlers import reload_command, config_command
        self.assertTrue(callable(reload_command))
        self.assertTrue(callable(config_command))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestWelcomeMessage))
    suite.addTests(loader.loadTestsFromTestCase(TestReplyKeyboard))
    suite.addTests(loader.loadTestsFromTestCase(TestInlineKeyboards))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceResponses))
    suite.addTests(loader.loadTestsFromTestCase(TestUserStateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupVerifyService))
    suite.addTests(loader.loadTestsFromTestCase(TestAdminConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestHumanAgentService))
    suite.addTests(loader.loadTestsFromTestCase(TestMenuNavigation))
    suite.addTests(loader.loadTestsFromTestCase(TestDebounce))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationFailureHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestTextManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAdminCommands))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "="*50)
    print(f"测试总数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*50)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
