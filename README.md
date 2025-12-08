# 🥔 土豆担保机器人 (复刻版)

基于 Telegram Bot API 开发的担保交易服务机器人，100% 复刻 [@tddbo4bot](https://t.me/tddbo4bot) 的功能和交互流程。

## ✨ 功能特性

### 主菜单功能 (10个)

| 功能 | 类型 | 描述 |
|------|------|------|
| **拉专群** | 自动回复 → 条件转人工 | 专群收费标准，上押后分配客服 |
| **开公群** | 自动回复 → 条件转人工 | 公群收费标准，上押后分配客服 |
| **业务咨询** | 直接转人工 | 人工客服在线咨询 |
| **纠纷仲裁** | 直接转人工 | 交易纠纷处理 |
| **买广告** | 自动回复 → 条件转人工 | 供需广告发布服务 |
| **买会员** | 自动回复 → 条件转人工 | 高级用户群服务 |
| **资源对接** | 直接转人工 | 资源匹配服务 |
| **投诉建议** | 直接转人工 | 工作人员投诉通道 |
| **自助验群** | 全自动 | 输入群编号验证 |
| **销群恢复** | 直接转人工 | 公群恢复服务 |

### 交互流程

```
用户发送 /start
       ↓
显示招聘信息 + Inline 入口按钮 "点此按钮链接工作流程"
       ↓
用户点击入口按钮
       ↓
显示欢迎消息 + 底部 Reply Keyboard（10个功能按钮，2列×5行）
       ↓
用户点击功能按钮 → 对应服务响应
```

### 核心功能

- ✅ Inline Keyboard 入口按钮 + Reply Keyboard 功能菜单
- ✅ 用户状态管理
- ✅ 图片检测（自动识别付款截图）
- ✅ 人工客服通知系统
- ✅ 自助群验证查询
- ✅ TRC20 USDT 支付地址展示

## 🛠️ 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.10+ |
| Bot 框架 | python-telegram-bot | 20.0+ |
| 数据库 | PostgreSQL / SQLite | - |
| 缓存 | Redis (可选) | 6.0+ |

## 📦 安装步骤

### 1. 克隆项目

```bash
cd c:\Users\Administrator\Desktop\td
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入实际值
# 必填项：BOT_TOKEN, ADMIN_USER_IDS, PAYMENT_ADDRESS
```

## ⚙️ 配置说明

### 必填配置

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `BOT_TOKEN` | Telegram Bot Token | 通过 [@BotFather](https://t.me/BotFather) 创建机器人获取 |
| `ADMIN_USER_IDS` | 管理员用户 ID（支持多个，用逗号分隔） | 通过 [@userinfobot](https://t.me/userinfobot) 获取 |
| `PAYMENT_ADDRESS` | TRC20 收款地址 | 你的 USDT 钱包地址 |

#### 管理员配置说明

`ADMIN_USER_IDS` 用于配置机器人的管理员，管理员将会：
- 接收人工客服通知（用户点击"业务咨询"、"纠纷仲裁"等按钮时）
- 接收用户截图转发（用户发送付款截图时）
- 接收客服请求提醒

**配置示例：**
```bash
# 单个管理员
ADMIN_USER_IDS=123456789

# 多个管理员（用英文逗号分隔）
ADMIN_USER_IDS=123456789,987654321,111222333
```

**容错机制：** 如果配置了无效的 ID（非数字），系统会自动跳过并显示警告，不会导致机器人启动失败。

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | SQLite |
| `REDIS_URL` | Redis 缓存 | 内存缓存 |
| `LOG_LEVEL` | 日志级别 | INFO |

## 🚀 运行方法

### 开发环境

```bash
# 激活虚拟环境
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 初始化数据库（首次运行）
python scripts/init_db.py

# 运行机器人
python -m bot.main
```

### Bot Commands 配置

机器人启动时会自动注册以下命令到 Telegram 菜单：

| 命令 | 描述 |
|------|------|
| `/start` | 开始使用机器人 |

这些命令会显示在 Telegram 聊天界面左下角的菜单按钮中。

### 生产环境

```bash
# 使用 Docker
docker-compose up -d

# 或使用 systemd (Linux)
sudo systemctl start tddb-bot
```

## 📁 项目结构

```
td/
├── bot/                      # 机器人核心代码
│   ├── __init__.py
│   ├── main.py              # 入口文件
│   ├── config.py            # 配置管理
│   ├── handlers/            # 消息处理器
│   │   ├── __init__.py
│   │   ├── start.py         # /start 命令
│   │   ├── callbacks.py     # 按钮回调
│   │   ├── messages.py      # 文本消息
│   │   └── photos.py        # 图片处理
│   ├── keyboards/           # 键盘定义
│   │   ├── __init__.py
│   │   ├── inline.py        # Inline 键盘 (入口按钮等)
│   │   └── reply.py         # Reply 键盘 (底部10个功能按钮)
│   └── services/            # 业务服务
│       ├── __init__.py
│       ├── user_state.py    # 用户状态
│       ├── group_verify.py  # 群验证
│       └── human_agent.py   # 人工客服
├── tests/                   # 测试文件
│   └── test_bot.py
├── .env.example             # 环境变量示例
├── .env                     # 环境变量 (不提交)
├── requirements.txt         # Python 依赖
├── README.md                # 项目文档
└── bot_requirements.md      # 需求文档
```



## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行单个测试文件
python tests/test_bot.py
```

## 📋 开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| P1 | 基础框架 + /start + 主菜单 | ✅ 完成 |
| P2 | 10个功能按钮的自动回复 | ✅ 完成 |
| P3 | 用户状态管理 + 自助验群 | ✅ 完成 |
| P4 | 图片检测 + 人工客服通知 | ✅ 完成 |
| P5 | 数据库集成 + 后台管理 | ⏳ 待开发 |
| P6 | 测试 + 部署 | ⏳ 待开发 |

## 📄 相关文档

- [完整需求文档](bot_requirements.md) - 功能详细说明
- [人工接入分析](human_handoff_analysis.md) - 客服接入规则
- [功能分析数据](bot_analysis.json) - 结构化功能数据

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
