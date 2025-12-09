# 🥔 土豆担保 Bot - 生产环境部署检查清单

## 快速检查（自动化脚本）

```bash
# 运行一键检查脚本
python scripts/pre_deploy_check.py

# Render 部署准备（推荐）
python scripts/deploy_render.py

# Render 部署准备 + 自动推送代码
python scripts/deploy_render.py --push
```

---

## 详细检查清单

### 一、代码检查 ✅

| 检查项 | 命令 | 期望结果 |
|--------|------|----------|
| Python 语法 | `python -m py_compile bot/**/*.py` | 无错误输出 |
| 单元测试 | `python -m pytest tests/ -v` | 全部 PASSED |
| 模块导入 | `python -c "from bot.main import main"` | 无 ImportError |

### 二、配置检查 ✅

| 检查项 | 检查方法 | 期望结果 |
|--------|----------|----------|
| `.env` 文件存在 | 检查项目根目录 | 文件存在 |
| `BOT_TOKEN` 已配置 | 非空且格式正确 `数字:字母` | ✅ |
| `PAYMENT_ADDRESS` 已配置 | 非空，长度 34 字符 | ✅ |
| `ADMIN_USER_IDS` 已配置 | 至少配置一个管理员 ID | ✅ |
| `config/texts.json` 有效 | JSON 格式正确 | ✅ |

### 三、环境变量清单

#### 必填项（缺失将无法启动）

```env
# Telegram Bot Token（从 @BotFather 获取）
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# TRC20 收款地址（34 字符）
PAYMENT_ADDRESS=TXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 推荐配置（缺失影响部分功能）

```env
# 管理员用户 ID（英文逗号分隔，用于接收客服通知）
ADMIN_USER_IDS=123456789,987654321

# 机器人显示名称
BOT_NAME=土豆担保

# 日志级别
LOG_LEVEL=INFO

# 日志文件（生产环境建议配置）
LOG_FILE=bot.log
```

#### 可选配置

```env
# 支付网络类型
PAYMENT_NETWORK=TRC20

# 是否开启人工客服通知
ENABLE_HUMAN_NOTIFICATION=true

# 用户状态过期时间（秒）
USER_STATE_EXPIRE=3600

# 调试模式（生产环境应设为 false）
DEBUG_MODE=false
```

### 四、网络连接检查 ✅

| 检查项 | 命令 | 期望结果 |
|--------|------|----------|
| Telegram API 连通 | Bot Token 验证 | 返回 Bot 用户名 |
| 网络稳定性 | `ping api.telegram.org` | 延迟 < 500ms |

### 五、数据库检查 ✅

| 检查项 | 检查方法 | 期望结果 |
|--------|----------|----------|
| 数据库文件存在 | `bot_data.db` | 文件存在或自动创建 |
| 表结构正确 | 启动时自动初始化 | 无报错 |

---

## 部署方式

### 方式一：Render 云部署（推荐）

#### 一键部署准备
```bash
# 运行部署准备脚本
python scripts/deploy_render.py

# 自动提交并推送代码
python scripts/deploy_render.py --push
```

#### 手动部署步骤

1. **登录 Render**
   - 访问 https://render.com 并登录

2. **创建新服务**
   - 点击 "New +" → "Background Worker"

3. **连接代码仓库**
   - 选择 GitHub/GitLab → 授权 → 选择此项目仓库

4. **配置服务**
   - Render 会自动检测 `render.yaml` 配置
   - 如未检测到，手动设置：
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python -m bot.main`

5. **设置环境变量** ⚠️ 重要
   | 变量名 | 值 | 必填 |
   |--------|-----|------|
   | `BOT_TOKEN` | 你的 Bot Token | ✅ |
   | `PAYMENT_ADDRESS` | TRC20 收款地址 | ✅ |
   | `ADMIN_USER_IDS` | 管理员ID(逗号分隔) | ⚠️ 推荐 |

6. **选择计划**
   - 推荐: Starter ($7/月)

7. **创建服务**
   - 点击 "Create Background Worker"

8. **验证部署**
   - 查看 Logs 确认 Bot 正常启动

---

### 方式二：VPS/服务器部署

#### 1. 代码同步
```bash
# 拉取最新代码
git pull origin main
```

#### 2. 依赖安装
```bash
# 安装/更新依赖
pip install -r requirements.txt
```

#### 3. 配置检查
```bash
# 确保 .env 文件存在且配置正确
cat .env

# 运行检查脚本
python scripts/pre_deploy_check.py
```

#### 4. 启动服务
```bash
# 方式一：直接运行（测试用）
python -m bot.main

# 方式二：systemd 服务（推荐）
sudo systemctl restart tdbot
sudo systemctl status tdbot
```

#### 5. 验证运行
```bash
# 查看日志
tail -f bot.log

# 或查看 systemd 日志
sudo journalctl -u tdbot -f
```

---

## 常见问题排查

### 1. Bot 启动失败
```
❌ 错误: BOT_TOKEN 环境变量未设置
```
**解决**: 检查 `.env` 文件中 `BOT_TOKEN` 是否正确配置

### 2. 客服通知不工作
```
⚠️ 警告: ADMIN_USER_IDS 未设置
```
**解决**: 在 `.env` 中配置管理员 ID

### 3. 配置热加载失败
```
❌ 配置文件加载失败
```
**解决**: 检查 `config/texts.json` 的 JSON 格式是否正确

### 4. 数据库错误
```
sqlite3.OperationalError: unable to open database file
```
**解决**: 检查文件权限，确保 bot 有写入权限

---

## 监控建议

### 生产环境监控项

1. **进程存活**: 确保 bot 进程持续运行
2. **错误日志**: 监控 `bot.log` 中的 ERROR 级别日志
3. **响应时间**: 用户操作响应应 < 3 秒
4. **内存使用**: 长期运行内存应稳定

### 日志轮转配置（可选）

```bash
# /etc/logrotate.d/tdbot
/path/to/bot.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## 回滚方案

如果部署后发现问题：

```bash
# 1. 停止服务
sudo systemctl stop tdbot

# 2. 回滚代码
git checkout <上一个稳定版本>

# 3. 重启服务
sudo systemctl start tdbot
```

---

## 检查脚本输出示例

```
🥔 土豆担保 Bot - 生产环境部署前检查
──────────────────────────────────────────────────

============================================================
  1. Python 环境检查
============================================================
  ✅ PASS  Python 版本
  ℹ️  Python 3.13.7

============================================================
  2. 依赖包检查
============================================================
  ✅ PASS  依赖包安装

...（其他检查项）...

============================================================
  📊 检查结果汇总
============================================================

  ✅ Python 版本
  ✅ 依赖包
  ✅ 语法检查
  ✅ 配置文件
  ✅ 环境变量
  ✅ 模块导入
  ✅ 数据库
  ✅ 单元测试
  ✅ Token 验证

──────────────────────────────────────────────────
  总计: 9 项检查
  通过: 9 项

──────────────────────────────────────────────────

  ✅ 所有检查通过！可以部署到生产环境
```

