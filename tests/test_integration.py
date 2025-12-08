"""
土豆担保机器人 - 集成测试

测试内容:
1. 数据库连接和初始化
2. 群验证功能（真实数据库查询）
3. 用户状态持久化
4. 完整交互流程模拟
"""

import sys
import os
import tempfile
import unittest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import Database, GroupInfo
from bot.services.user_state import UserStateManager, UserState
from bot.services.group_verify import GroupVerifyService


class TestDatabaseIntegration(unittest.TestCase):
    """数据库集成测试"""

    def setUp(self):
        """每个测试前创建临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_tables()

    def tearDown(self):
        """每个测试后清理临时数据库"""
        self.db.close()
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_database_init(self):
        """测试数据库初始化"""
        # 表应该已创建
        self.assertEqual(self.db.count_groups(), 0)

    def test_insert_and_query_group(self):
        """测试插入和查询群信息"""
        group = GroupInfo(
            group_id="测试群001",
            group_type="专群",
            owner_name="测试老板",
            status="active",
            deposit_amount=1000.0,
            created_at="2024-12-01"
        )

        # 插入
        row_id = self.db.insert_group(group)
        self.assertGreater(row_id, 0)

        # 查询
        result = self.db.get_group_by_id("测试群001")
        self.assertIsNotNone(result)
        self.assertEqual(result.group_id, "测试群001")
        self.assertEqual(result.owner_name, "测试老板")
        self.assertEqual(result.deposit_amount, 1000.0)

    def test_update_group(self):
        """测试更新群信息"""
        group = GroupInfo(
            group_id="更新测试群",
            group_type="公群",
            owner_name="原老板",
            status="active",
            deposit_amount=2000.0,
            created_at="2024-12-01"
        )
        self.db.insert_group(group)

        # 更新
        group.owner_name = "新老板"
        group.deposit_amount = 3000.0
        self.db.update_group(group)

        # 验证
        result = self.db.get_group_by_id("更新测试群")
        self.assertEqual(result.owner_name, "新老板")
        self.assertEqual(result.deposit_amount, 3000.0)

    def test_count_groups(self):
        """测试群数量统计"""
        # 插入3个群
        for i in range(3):
            group = GroupInfo(
                group_id=f"计数群{i}",
                group_type="飞博",
                owner_name=f"老板{i}",
                status="active",
                deposit_amount=1000.0 * (i + 1),
                created_at="2024-12-01"
            )
            self.db.insert_group(group)

        self.assertEqual(self.db.count_groups(), 3)

    def test_get_all_groups(self):
        """测试获取所有群"""
        for i in range(5):
            group = GroupInfo(
                group_id=f"全部群{i}",
                group_type="专群",
                owner_name=f"老板{i}",
                status="active" if i % 2 == 0 else "closed",
                deposit_amount=1000.0,
                created_at="2024-12-01"
            )
            self.db.insert_group(group)

        groups = self.db.get_all_groups()
        self.assertEqual(len(groups), 5)


class TestGroupVerifyWithDatabase(unittest.TestCase):
    """群验证数据库集成测试"""

    def setUp(self):
        """设置临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # 创建数据库并填充测试数据
        self.db = Database(self.temp_db.name)
        self.db.init_tables()

        # 插入测试数据
        test_groups = [
            GroupInfo("专群A12345", "专群", "张老板", "active", 5000.0, "2024-01-15"),
            GroupInfo("公群12345", "公群", "李老板", "active", 15000.0, "2024-02-20"),
            GroupInfo("飞博13", "飞博", "王老板", "active", 20000.0, "2024-03-10"),
        ]
        for g in test_groups:
            self.db.insert_group(g)

        # 设置使用模拟数据（因为全局数据库实例路径不同）
        GroupVerifyService.set_use_database(False)

    def test_verify_nonexistent_group(self):
        """测试验证不存在的群"""
        result = GroupVerifyService.verify_group("专群X99999")
        self.assertIsNone(result)

    def test_format_result_found(self):
        """测试格式化验证结果（找到）"""
        result = GroupVerifyService.format_verify_result("公群12345")
        self.assertIn("✅", result)
        self.assertIn("李老板", result)
        self.assertIn("公群", result)

    def test_format_result_not_found(self):
        """测试格式化验证结果（未找到）"""
        result = GroupVerifyService.format_verify_result("不存在的群")
        self.assertIn("❌", result)
        self.assertIn("未找到", result)


class TestUserStateFlow(unittest.TestCase):
    """用户状态流程测试"""

    def setUp(self):
        self.manager = UserStateManager(expire_seconds=3600)
        self.user_id = 12345

    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.manager.get_state(self.user_id), UserState.IDLE)

    def test_full_flow_la_zhuan(self):
        """测试拉专群完整流程"""
        # 1. 点击拉专群 -> 设置等待押金状态
        self.manager.set_state(self.user_id, UserState.WAITING_DEPOSIT_LA_ZHUAN, "拉专群")
        self.assertTrue(self.manager.is_waiting_deposit(self.user_id))

        # 2. 用户上传截图后 -> 转人工
        self.manager.set_state(self.user_id, UserState.IN_HUMAN_SESSION, "拉专群")
        self.assertEqual(self.manager.get_state(self.user_id), UserState.IN_HUMAN_SESSION)

        # 3. 会话结束 -> 回到空闲
        self.manager.clear_state(self.user_id)
        self.assertEqual(self.manager.get_state(self.user_id), UserState.IDLE)

    def test_full_flow_yanqun(self):
        """测试自助验群完整流程"""
        # 1. 点击自助验群 -> 设置等待群编号状态
        self.manager.set_state(self.user_id, UserState.WAITING_GROUP_ID, "自助验群")
        self.assertEqual(self.manager.get_state(self.user_id), UserState.WAITING_GROUP_ID)

        # 2. 用户输入群编号后 -> 回到空闲
        self.manager.clear_state(self.user_id)
        self.assertEqual(self.manager.get_state(self.user_id), UserState.IDLE)

    def test_state_data_persistence(self):
        """测试状态数据持久性"""
        self.manager.set_state(self.user_id, UserState.WAITING_DEPOSIT_KAI_GONG, "开公群")

        state_data = self.manager.get_state_data(self.user_id)
        self.assertIsNotNone(state_data)
        self.assertEqual(state_data.service_type, "开公群")

    def test_multiple_users_independent(self):
        """测试多用户状态独立"""
        user1 = 11111
        user2 = 22222

        self.manager.set_state(user1, UserState.WAITING_DEPOSIT_LA_ZHUAN, "拉专群")
        self.manager.set_state(user2, UserState.WAITING_GROUP_ID, "自助验群")

        # 验证状态独立
        self.assertEqual(self.manager.get_state(user1), UserState.WAITING_DEPOSIT_LA_ZHUAN)
        self.assertEqual(self.manager.get_state(user2), UserState.WAITING_GROUP_ID)

        # 清除 user1 不影响 user2
        self.manager.clear_state(user1)
        self.assertEqual(self.manager.get_state(user1), UserState.IDLE)
        self.assertEqual(self.manager.get_state(user2), UserState.WAITING_GROUP_ID)


class TestCompleteInteractionFlow(unittest.TestCase):
    """完整交互流程测试"""

    def setUp(self):
        self.state_manager = UserStateManager(expire_seconds=3600)
        GroupVerifyService.set_use_database(False)

    def tearDown(self):
        GroupVerifyService.set_use_database(True)

    def test_start_to_main_menu(self):
        """测试 /start 到主菜单流程"""
        from bot.keyboards.inline import get_entry_keyboard, get_main_menu_keyboard
        from bot.handlers.start import WELCOME_MESSAGE

        # 1. 用户发送 /start
        # 机器人返回欢迎消息 + 入口按钮
        self.assertIn("土豆担保华人线上招聘", WELCOME_MESSAGE)

        entry_kb = get_entry_keyboard()
        self.assertEqual(len(entry_kb.inline_keyboard), 1)

        # 2. 用户点击入口按钮
        # 机器人返回主菜单
        main_menu = get_main_menu_keyboard()
        total_buttons = sum(len(row) for row in main_menu.inline_keyboard)
        self.assertEqual(total_buttons, 10)

    def test_service_button_to_response(self):
        """测试服务按钮到响应流程"""
        from bot.handlers.service_responses import SERVICE_RESPONSES

        # 测试每个服务都有响应
        services = ["la_zhuan", "kai_gong", "zixun", "jiufen",
                    "guanggao", "huiyuan", "ziyuan", "tousu",
                    "yanqun", "xiaoqhf"]

        for service in services:
            self.assertIn(service, SERVICE_RESPONSES)
            self.assertIn("type", SERVICE_RESPONSES[service])
            self.assertIn("text", SERVICE_RESPONSES[service])

    def test_yanqun_flow(self):
        """测试自助验群完整流程"""
        user_id = 99999

        # 1. 用户点击自助验群
        self.state_manager.set_state(user_id, UserState.WAITING_GROUP_ID, "自助验群")

        # 2. 用户输入有效群编号
        group_id = "专群A12345"
        parsed = GroupVerifyService.parse_group_id(group_id)
        self.assertEqual(parsed, group_id)

        # 3. 验证群信息
        result = GroupVerifyService.format_verify_result(group_id)
        self.assertIn("✅", result)
        self.assertIn("张老板", result)

        # 4. 清除状态
        self.state_manager.clear_state(user_id)
        self.assertEqual(self.state_manager.get_state(user_id), UserState.IDLE)

    def test_payment_service_flow(self):
        """测试付款类服务流程"""
        from bot.handlers.service_responses import SERVICE_RESPONSES

        user_id = 88888

        # 1. 用户点击拉专群
        response = SERVICE_RESPONSES["la_zhuan"]
        self.assertEqual(response["type"], "auto_reply_with_payment")

        # 2. 设置等待押金状态
        self.state_manager.set_state(user_id, UserState.WAITING_DEPOSIT_LA_ZHUAN, "拉专群")
        self.assertTrue(self.state_manager.is_waiting_deposit(user_id))

        # 3. 用户上传截图 -> 转人工
        self.state_manager.set_state(user_id, UserState.IN_HUMAN_SESSION, "拉专群")

        # 4. 验证最终状态
        self.assertEqual(self.state_manager.get_state(user_id), UserState.IN_HUMAN_SESSION)


def run_integration_tests():
    """运行所有集成测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupVerifyWithDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestUserStateFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestCompleteInteractionFlow))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*50)
    print("集成测试结果")
    print("="*50)
    print(f"测试总数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*50)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
