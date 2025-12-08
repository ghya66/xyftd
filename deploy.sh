#!/bin/bash
# ============================================
# 土豆担保机器人 - 自动化部署脚本
# ============================================
# 
# 用法: ./deploy.sh [选项]
#
# 选项:
#   --install     首次安装部署
#   --update      更新代码并重启
#   --status      查看服务状态
#   --logs        查看实时日志
#   --restart     重启服务
#   --stop        停止服务
#
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量（根据实际情况修改）
APP_NAME="tdbot"
APP_DIR="/opt/tdbot"
SERVICE_NAME="tdbot"
PYTHON_VERSION="3.10"
VENV_DIR="${APP_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 用户运行此脚本"
        exit 1
    fi
}

# 检查必要的配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "${APP_DIR}/.env" ]; then
        log_error ".env 文件不存在！"
        log_info "请先复制 .env.example 为 .env 并配置必要参数"
        exit 1
    fi
    
    # 检查必要的环境变量
    source "${APP_DIR}/.env"
    
    if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" == "your_bot_token_here" ]; then
        log_error "BOT_TOKEN 未配置！"
        exit 1
    fi
    
    if [ -z "$PAYMENT_ADDRESS" ]; then
        log_error "PAYMENT_ADDRESS 未配置！"
        exit 1
    fi
    
    log_info "✅ 配置检查通过"
}

# 创建系统用户
create_user() {
    if ! id "${APP_NAME}" &>/dev/null; then
        log_info "创建系统用户: ${APP_NAME}"
        useradd --system --no-create-home --shell /bin/false "${APP_NAME}"
    else
        log_info "系统用户 ${APP_NAME} 已存在"
    fi
}

# 设置目录权限
set_permissions() {
    log_info "设置目录权限..."
    chown -R "${APP_NAME}:${APP_NAME}" "${APP_DIR}"
    chmod 700 "${APP_DIR}/.env"  # 保护敏感配置
    chmod 755 "${APP_DIR}"
}

# 创建虚拟环境
setup_venv() {
    log_info "设置 Python 虚拟环境..."
    
    if [ ! -d "${VENV_DIR}" ]; then
        python3 -m venv "${VENV_DIR}"
    fi
    
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r "${APP_DIR}/requirements.txt"
    deactivate
    
    log_info "✅ 依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    source "${VENV_DIR}/bin/activate"
    cd "${APP_DIR}"
    python scripts/init_db.py --db-path "${APP_DIR}/bot_data.db"
    deactivate
    
    log_info "✅ 数据库初始化完成"
}

# 安装 systemd 服务
install_service() {
    log_info "安装 systemd 服务..."
    
    # 复制服务文件
    cp "${APP_DIR}/systemd/tdbot.service" "${SERVICE_FILE}"
    
    # 重新加载 systemd
    systemctl daemon-reload
    
    # 启用开机自启
    systemctl enable "${SERVICE_NAME}"
    
    log_info "✅ 服务安装完成"
}

# 启动服务
start_service() {
    log_info "启动服务..."
    systemctl start "${SERVICE_NAME}"
    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        log_info "✅ 服务启动成功"
    else
        log_error "服务启动失败！请查看日志: journalctl -u ${SERVICE_NAME}"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止服务..."
    systemctl stop "${SERVICE_NAME}" || true
    log_info "✅ 服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    systemctl restart "${SERVICE_NAME}"
    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        log_info "✅ 服务重启成功"
    else
        log_error "服务重启失败！请查看日志: journalctl -u ${SERVICE_NAME}"
        exit 1
    fi
}

# 查看服务状态
show_status() {
    echo ""
    echo "========== 服务状态 =========="
    systemctl status "${SERVICE_NAME}" --no-pager || true
    echo ""
    echo "========== 最近日志 =========="
    journalctl -u "${SERVICE_NAME}" -n 20 --no-pager || true
}

# 查看实时日志
show_logs() {
    log_info "显示实时日志 (Ctrl+C 退出)..."
    journalctl -u "${SERVICE_NAME}" -f
}

# 首次安装
do_install() {
    log_info "========== 开始首次安装 =========="

    check_root
    check_config
    create_user
    setup_venv
    init_database
    set_permissions
    install_service
    start_service

    echo ""
    log_info "========== 安装完成 =========="
    log_info "服务状态: systemctl status ${SERVICE_NAME}"
    log_info "查看日志: journalctl -u ${SERVICE_NAME} -f"
    log_info "重启服务: systemctl restart ${SERVICE_NAME}"
}

# 更新部署
do_update() {
    log_info "========== 开始更新 =========="

    check_root
    check_config

    # 更新依赖
    setup_venv

    # 重启服务
    restart_service

    log_info "========== 更新完成 =========="
}

# 显示帮助
show_help() {
    echo "土豆担保机器人 - 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --install     首次安装部署"
    echo "  --update      更新代码并重启"
    echo "  --status      查看服务状态"
    echo "  --logs        查看实时日志"
    echo "  --restart     重启服务"
    echo "  --stop        停止服务"
    echo "  --help        显示帮助信息"
    echo ""
}

# 主入口
main() {
    case "$1" in
        --install)
            do_install
            ;;
        --update)
            do_update
            ;;
        --status)
            show_status
            ;;
        --logs)
            show_logs
            ;;
        --restart)
            check_root
            restart_service
            ;;
        --stop)
            check_root
            stop_service
            ;;
        --help|*)
            show_help
            ;;
    esac
}

# 运行主函数
main "$@"

