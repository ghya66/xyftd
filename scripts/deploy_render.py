#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render 一键部署准备脚本

功能:
    1. 检查部署前置条件
    2. 验证配置文件
    3. 生成部署指南
    4. 可选：自动提交并推送代码

使用方式:
    python scripts/deploy_render.py [--push]

参数:
    --push    自动提交并推送代码到远程仓库
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str) -> None:
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")

def print_step(step: int, title: str) -> None:
    print(f"\n{Colors.BLUE}{Colors.BOLD}[步骤 {step}] {title}{Colors.RESET}")

def print_success(msg: str) -> None:
    print(f"  {Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str) -> None:
    print(f"  {Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str) -> None:
    print(f"  {Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str) -> None:
    print(f"  {Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def run_command(cmd: List[str], capture: bool = True) -> Tuple[int, str]:
    """运行命令并返回结果"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return result.returncode, stdout + stderr
        else:
            result = subprocess.run(cmd)
            return result.returncode, ""
    except Exception as e:
        return -1, str(e)

def check_required_files() -> bool:
    """检查必要文件是否存在"""
    required_files = [
        ("render.yaml", "Render 部署配置"),
        ("requirements.txt", "Python 依赖"),
        ("bot/main.py", "Bot 主入口"),
        ("config/texts.json", "文案配置"),
    ]
    
    all_exist = True
    for file_path, desc in required_files:
        if Path(file_path).exists():
            print_success(f"{desc}: {file_path}")
        else:
            print_error(f"{desc} 不存在: {file_path}")
            all_exist = False
    
    return all_exist

def check_render_yaml() -> bool:
    """验证 render.yaml 配置"""
    try:
        import yaml
        with open("render.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", [])
        if not services:
            print_error("render.yaml 中没有定义服务")
            return False
        
        service = services[0]
        print_success(f"服务类型: {service.get('type', 'unknown')}")
        print_success(f"服务名称: {service.get('name', 'unknown')}")
        print_success(f"运行时: {service.get('runtime', 'unknown')}")
        print_success(f"计划: {service.get('plan', 'unknown')}")
        
        return True
    except ImportError:
        # 没有 yaml 库，使用简单检查
        with open("render.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        
        if "type: worker" in content and "startCommand" in content:
            print_success("render.yaml 格式基本正确")
            return True
        else:
            print_error("render.yaml 格式可能有问题")
            return False
    except Exception as e:
        print_error(f"验证 render.yaml 失败: {e}")
        return False

def check_git_status() -> Tuple[bool, List[str]]:
    """检查 Git 状态"""
    # 检查是否是 Git 仓库
    code, output = run_command(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        print_error("当前目录不是 Git 仓库")
        return False, []
    
    # 获取未提交的文件
    code, output = run_command(["git", "status", "--porcelain"])
    if code != 0:
        print_error("无法获取 Git 状态")
        return False, []
    
    uncommitted = [line.strip() for line in output.strip().split("\n") if line.strip()]
    
    # 检查远程仓库
    code, output = run_command(["git", "remote", "-v"])
    if "origin" in output:
        print_success("远程仓库已配置")
    else:
        print_warning("未配置远程仓库 (origin)")
    
    return True, uncommitted

def check_env_for_render() -> bool:
    """检查本地 .env 配置（用于验证）"""
    if not Path(".env").exists():
        print_warning(".env 文件不存在（Render 上需要手动配置环境变量）")
        return True
    
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN", "")
    payment_address = os.getenv("PAYMENT_ADDRESS", "")
    admin_ids = os.getenv("ADMIN_USER_IDS", "")
    
    if bot_token and bot_token != "your_bot_token_here":
        print_success("BOT_TOKEN 已配置")
    else:
        print_warning("BOT_TOKEN 未配置（需要在 Render 控制台设置）")
    
    if payment_address:
        print_success("PAYMENT_ADDRESS 已配置")
    else:
        print_warning("PAYMENT_ADDRESS 未配置（需要在 Render 控制台设置）")
    
    if admin_ids:
        print_success(f"ADMIN_USER_IDS 已配置 ({len(admin_ids.split(','))} 个)")
    else:
        print_warning("ADMIN_USER_IDS 未配置（建议在 Render 控制台设置）")
    
    return True

def run_pre_deploy_check() -> bool:
    """运行部署前检查脚本"""
    check_script = Path("scripts/pre_deploy_check.py")
    if not check_script.exists():
        print_warning("pre_deploy_check.py 不存在，跳过详细检查")
        return True
    
    print_info("运行部署前检查...")
    code, output = run_command([sys.executable, str(check_script)])
    
    if code == 0:
        print_success("所有检查通过")
        return True
    else:
        print_error("部分检查未通过")
        print(output)
        return False

def git_add_commit_push(message: str) -> bool:
    """Git 添加、提交并推送"""
    # 添加所有更改
    code, _ = run_command(["git", "add", "."])
    if code != 0:
        print_error("git add 失败")
        return False
    print_success("已添加所有更改")
    
    # 提交
    code, output = run_command(["git", "commit", "-m", message])
    if code != 0:
        if "nothing to commit" in output:
            print_info("没有需要提交的更改")
        else:
            print_error(f"git commit 失败: {output}")
            return False
    else:
        print_success("已提交更改")
    
    # 推送
    code, output = run_command(["git", "push", "origin", "main"])
    if code != 0:
        # 尝试推送到 master
        code, output = run_command(["git", "push", "origin", "master"])
        if code != 0:
            print_error(f"git push 失败: {output}")
            return False
    
    print_success("已推送到远程仓库")
    return True

def print_deploy_guide() -> None:
    """打印部署指南"""
    print_header("📖 Render 部署指南")
    
    guide = """
  {CYAN}1. 登录 Render{RESET}
     访问 https://render.com 并登录

  {CYAN}2. 创建新服务{RESET}
     点击 "New +" → "Background Worker"

  {CYAN}3. 连接代码仓库{RESET}
     选择 GitHub/GitLab → 授权 → 选择此项目仓库

  {CYAN}4. 配置服务{RESET}
     Render 会自动检测 render.yaml 配置
     如未检测到，手动设置：
     • Build Command: pip install -r requirements.txt
     • Start Command: python -m bot.main

  {CYAN}5. 设置环境变量 ⚠️ 重要{RESET}
     在 "Environment" 页面添加：
     ┌─────────────────────┬──────────────────────────┐
     │ BOT_TOKEN           │ 你的 Telegram Bot Token  │
     │ PAYMENT_ADDRESS     │ TRC20 收款地址           │
     │ ADMIN_USER_IDS      │ 管理员ID(逗号分隔)       │
     └─────────────────────┴──────────────────────────┘

  {CYAN}6. 选择计划{RESET}
     推荐: Starter ($7/月)

  {CYAN}7. 创建服务{RESET}
     点击 "Create Background Worker"

  {CYAN}8. 等待部署完成{RESET}
     查看 Logs 确认 Bot 正常启动

  {YELLOW}💡 提示：{RESET}
     • 每次推送到 main 分支会自动重新部署
     • 可在 Render Dashboard 查看日志和监控
     • 环境变量修改后需要手动触发重新部署
""".format(CYAN=Colors.CYAN, YELLOW=Colors.YELLOW, RESET=Colors.RESET)
    
    print(guide)

def main():
    # 设置控制台编码为 UTF-8（Windows 兼容）
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(description="Render 一键部署准备脚本")
    parser.add_argument("--push", action="store_true", help="自动提交并推送代码")
    args = parser.parse_args()
    
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"\n{Colors.BOLD}[Render] 一键部署准备{Colors.RESET}")
    print(f"{'─'*50}")
    
    errors = []
    
    # 步骤 1: 检查必要文件
    print_step(1, "检查必要文件")
    if not check_required_files():
        errors.append("必要文件缺失")
    
    # 步骤 2: 验证 render.yaml
    print_step(2, "验证 render.yaml 配置")
    if not check_render_yaml():
        errors.append("render.yaml 配置有误")
    
    # 步骤 3: 检查 Git 状态
    print_step(3, "检查 Git 状态")
    git_ok, uncommitted = check_git_status()
    if not git_ok:
        errors.append("Git 仓库状态异常")
    elif uncommitted:
        print_warning(f"有 {len(uncommitted)} 个未提交的更改:")
        for f in uncommitted[:5]:
            print(f"       • {f}")
        if len(uncommitted) > 5:
            print(f"       ... 还有 {len(uncommitted) - 5} 个")
    
    # 步骤 4: 检查环境变量配置
    print_step(4, "检查环境变量")
    check_env_for_render()
    
    # 步骤 5: 运行部署前检查
    print_step(5, "运行部署前检查")
    if not run_pre_deploy_check():
        errors.append("部署前检查未通过")
    
    # 步骤 6: 提交并推送（如果指定了 --push）
    if args.push:
        print_step(6, "提交并推送代码")
        if uncommitted:
            if not git_add_commit_push("chore: 准备 Render 部署"):
                errors.append("Git 推送失败")
        else:
            print_info("没有需要提交的更改")
    
    # 结果汇总
    print_header("📊 检查结果")
    
    if errors:
        print(f"\n  {Colors.RED}发现 {len(errors)} 个问题:{Colors.RESET}")
        for err in errors:
            print(f"  {Colors.RED}• {err}{Colors.RESET}")
        print(f"\n  {Colors.YELLOW}请修复以上问题后再部署{Colors.RESET}")
    else:
        print(f"\n  {Colors.GREEN}✅ 所有检查通过！{Colors.RESET}")
        
        if uncommitted and not args.push:
            print(f"\n  {Colors.YELLOW}下一步:{Colors.RESET}")
            print(f"  1. 提交并推送代码:")
            print(f"     {Colors.CYAN}git add . && git commit -m 'chore: 准备 Render 部署' && git push{Colors.RESET}")
            print(f"  2. 或使用自动推送:")
            print(f"     {Colors.CYAN}python scripts/deploy_render.py --push{Colors.RESET}")
        
        # 打印部署指南
        print_deploy_guide()
    
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())

