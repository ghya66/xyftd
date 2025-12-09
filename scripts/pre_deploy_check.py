#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生产环境部署前检查脚本

运行方式:
    python scripts/pre_deploy_check.py

检查项目:
    1. Python 版本检查
    2. 依赖包检查
    3. 语法检查
    4. 配置文件检查
    5. 环境变量检查
    6. 模块导入检查
    7. 数据库连接检查
    8. 单元测试
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str) -> None:
    """打印检查项标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")

def print_result(name: str, passed: bool, message: str = "") -> None:
    """打印检查结果"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"  {status}  {name}")
    if message and not passed:
        print(f"         {Colors.YELLOW}└─ {message}{Colors.RESET}")

def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"  {Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str) -> None:
    """打印信息"""
    print(f"  {Colors.BLUE}ℹ️  {message}{Colors.RESET}")

# ============================================================
# 检查函数
# ============================================================

def check_python_version() -> Tuple[bool, str]:
    """检查 Python 版本 (要求 >= 3.9)"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"需要 Python >= 3.9，当前: {version.major}.{version.minor}"

def check_dependencies() -> Tuple[bool, str]:
    """检查依赖包是否安装"""
    # 包名 -> 实际导入名 映射
    required_packages = {
        "python-telegram-bot": "telegram",
        "python-dotenv": "dotenv",
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        return False, f"缺少依赖: {', '.join(missing)}"
    return True, "所有依赖已安装"

def check_syntax() -> Tuple[bool, str]:
    """检查所有 Python 文件语法"""
    bot_dir = Path("bot")
    errors = []
    
    for py_file in bot_dir.rglob("*.py"):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                errors.append(f"{py_file}: {result.stderr}")
        except Exception as e:
            errors.append(f"{py_file}: {str(e)}")
    
    if errors:
        return False, f"语法错误: {len(errors)} 个文件"
    return True, "所有文件语法正确"

def check_config_file() -> Tuple[bool, str]:
    """检查配置文件"""
    config_path = Path("config/texts.json")
    
    if not config_path.exists():
        return False, "config/texts.json 不存在"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 检查必要字段
        required_fields = ["version", "welcome_message", "buttons", "services"]
        missing = [f for f in required_fields if f not in config]
        
        if missing:
            return False, f"配置缺少字段: {', '.join(missing)}"
        
        # 检查服务配置
        services = config.get("services", {})
        required_services = ["la_zhuan", "kai_gong", "zixun", "jiufen", 
                           "guanggao", "huiyuan", "ziyuan", "tousu", 
                           "yanqun", "xiaoqhf"]
        missing_services = [s for s in required_services if s not in services]
        
        if missing_services:
            return False, f"缺少服务配置: {', '.join(missing_services)}"
        
        return True, f"配置文件正常 (版本: {config.get('version', 'unknown')})"
    
    except json.JSONDecodeError as e:
        return False, f"JSON 格式错误: {e}"
    except Exception as e:
        return False, f"读取配置失败: {e}"

def check_env_file() -> Tuple[bool, str, List[str]]:
    """检查环境变量配置"""
    warnings = []
    
    # 检查 .env 文件是否存在
    if not Path(".env").exists():
        return False, ".env 文件不存在", warnings
    
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 必填项检查
    bot_token = os.getenv("BOT_TOKEN", "")
    payment_address = os.getenv("PAYMENT_ADDRESS", "")
    
    if not bot_token or bot_token == "your_bot_token_here":
        return False, "BOT_TOKEN 未配置或使用了示例值", warnings
    
    if not payment_address:
        return False, "PAYMENT_ADDRESS 未配置", warnings
    
    # 验证 BOT_TOKEN 格式 (数字:字母数字)
    if ":" not in bot_token:
        return False, "BOT_TOKEN 格式不正确", warnings
    
    # 验证 PAYMENT_ADDRESS 长度 (TRC20 地址通常 34 字符)
    if len(payment_address) < 30:
        warnings.append(f"PAYMENT_ADDRESS 长度异常 ({len(payment_address)} 字符)")
    
    # 可选项警告
    admin_ids = os.getenv("ADMIN_USER_IDS", "")
    if not admin_ids:
        warnings.append("ADMIN_USER_IDS 未配置，人工客服通知将无法使用")
    
    return True, "必填环境变量已配置", warnings

def check_module_imports() -> Tuple[bool, str]:
    """检查模块导入"""
    try:
        # 添加项目根目录到路径
        sys.path.insert(0, str(Path.cwd()))
        
        # 测试核心模块导入
        from bot.config import config
        from bot.services.text_manager import TextManager
        from bot.handlers import start_command, button_callback, message_handler
        from bot.keyboards.inline import get_main_menu_keyboard
        from bot.keyboards.reply import get_main_menu_reply_keyboard
        
        return True, "所有模块导入正常"
    except ImportError as e:
        return False, f"模块导入失败: {e}"
    except Exception as e:
        return False, f"导入异常: {e}"

def check_database() -> Tuple[bool, str]:
    """检查数据库"""
    try:
        from bot.database.db import Database
        
        # 使用项目根目录的数据库文件
        db_path = Path("bot_data.db")
        db = Database(str(db_path))
        db.init_tables()
        
        # 测试连接
        count = db.count_groups()
        db.close()
        return True, f"数据库连接正常 (群数据: {count} 条)"
    except Exception as e:
        return False, f"数据库检查失败: {e}"

def run_unit_tests() -> Tuple[bool, str]:
    """运行单元测试"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 解析测试结果
        output = result.stdout + result.stderr
        
        if "passed" in output:
            # 提取通过数量
            import re
            match = re.search(r"(\d+) passed", output)
            passed_count = match.group(1) if match else "?"
            
            if result.returncode == 0:
                return True, f"所有测试通过 ({passed_count} 个)"
            else:
                # 有失败的测试
                fail_match = re.search(r"(\d+) failed", output)
                failed_count = fail_match.group(1) if fail_match else "?"
                return False, f"测试失败: {failed_count} 个失败, {passed_count} 个通过"
        
        return False, "无法解析测试结果"
    
    except subprocess.TimeoutExpired:
        return False, "测试超时 (>60秒)"
    except Exception as e:
        return False, f"测试运行失败: {e}"

def check_bot_token_validity() -> Tuple[bool, str]:
    """检查 Bot Token 是否有效（可选，需要网络）"""
    try:
        import asyncio
        from telegram import Bot
        
        bot_token = os.getenv("BOT_TOKEN", "")
        if not bot_token:
            return False, "BOT_TOKEN 未配置"
        
        async def verify_token():
            bot = Bot(token=bot_token)
            me = await bot.get_me()
            return me.username
        
        username = asyncio.run(verify_token())
        return True, f"Bot Token 有效 (@{username})"
    
    except Exception as e:
        error_msg = str(e)
        if "Unauthorized" in error_msg:
            return False, "Bot Token 无效或已过期"
        elif "Network" in error_msg or "Connection" in error_msg:
            return False, "网络连接失败，无法验证 Token"
        return False, f"Token 验证失败: {error_msg[:50]}"

# ============================================================
# 主程序
# ============================================================

def main():
    """主检查流程"""
    # 设置控制台编码为 UTF-8（Windows 兼容）
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    print(f"\n{Colors.BOLD}[土豆担保 Bot] 生产环境部署前检查{Colors.RESET}")
    print(f"{'─'*50}")
    
    results = []
    warnings = []
    
    # 1. Python 版本检查
    print_header("1. Python 环境检查")
    passed, msg = check_python_version()
    print_result("Python 版本", passed, msg)
    results.append(("Python 版本", passed))
    if passed:
        print_info(msg)
    
    # 2. 依赖包检查
    print_header("2. 依赖包检查")
    passed, msg = check_dependencies()
    print_result("依赖包安装", passed, msg)
    results.append(("依赖包", passed))
    
    # 3. 语法检查
    print_header("3. 代码语法检查")
    passed, msg = check_syntax()
    print_result("Python 语法", passed, msg)
    results.append(("语法检查", passed))
    
    # 4. 配置文件检查
    print_header("4. 配置文件检查")
    passed, msg = check_config_file()
    print_result("texts.json", passed, msg)
    results.append(("配置文件", passed))
    
    # 5. 环境变量检查
    print_header("5. 环境变量检查")
    passed, msg, env_warnings = check_env_file()
    print_result("环境变量", passed, msg)
    results.append(("环境变量", passed))
    for w in env_warnings:
        print_warning(w)
        warnings.append(w)
    
    # 6. 模块导入检查
    print_header("6. 模块导入检查")
    passed, msg = check_module_imports()
    print_result("模块导入", passed, msg)
    results.append(("模块导入", passed))
    
    # 7. 数据库检查
    print_header("7. 数据库检查")
    passed, msg = check_database()
    print_result("数据库连接", passed, msg)
    results.append(("数据库", passed))
    
    # 8. 单元测试
    print_header("8. 单元测试")
    passed, msg = run_unit_tests()
    print_result("单元测试", passed, msg)
    results.append(("单元测试", passed))
    
    # 9. Bot Token 验证（可选）
    print_header("9. Bot Token 在线验证")
    passed, msg = check_bot_token_validity()
    print_result("Token 有效性", passed, msg)
    results.append(("Token 验证", passed))
    
    # ============================================================
    # 汇总报告
    # ============================================================
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  📊 检查结果汇总{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count
    
    for name, passed in results:
        status = f"{Colors.GREEN}✅{Colors.RESET}" if passed else f"{Colors.RED}❌{Colors.RESET}"
        print(f"  {status} {name}")
    
    print(f"\n{'─'*50}")
    print(f"  总计: {total} 项检查")
    print(f"  {Colors.GREEN}通过: {passed_count} 项{Colors.RESET}")
    if failed_count > 0:
        print(f"  {Colors.RED}失败: {failed_count} 项{Colors.RESET}")
    if warnings:
        print(f"  {Colors.YELLOW}警告: {len(warnings)} 项{Colors.RESET}")
    
    print(f"\n{'─'*50}")
    
    if failed_count == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}  ✅ 所有检查通过！可以部署到生产环境{Colors.RESET}")
        if warnings:
            print(f"{Colors.YELLOW}     (请注意处理警告项){Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}  ❌ 检查未通过，请修复以上问题后再部署{Colors.RESET}")
        return 1

if __name__ == "__main__":
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    sys.exit(main())

