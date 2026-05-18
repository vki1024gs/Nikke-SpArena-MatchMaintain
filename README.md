# Match Maintenance — NIKKE PVP 对局数据维护工具

基于 FastAPI 的 Web 应用，管理 NIKKE PVP 对局数据。**TOML 单数据源 + Git 版本控制**，支持 Web UI、REST API 和 CLI。

## 架构

```
TOML 文件（唯一数据源）
    ↓ git 版本控制
    ├── Web UI (人)    — 浏览器浏览、编辑
    └── CLI (Agent)    — 命令行操作
```

- 每次写入自动 `git commit`，完整审计日志
- `git revert` 回滚任意版本
- 事务预览：diff → 校验 → 确认 → 写入

## 快速开始

### 1. 安装

```bash
cd match-maintain-web
pip install -e ".[dev]"
```

### 2. 启动

```bash
python run.py
```

访问 http://localhost:2771

### 3. 初始化 Git 版本控制（首次使用）

```bash
mm init
```

## 使用方式

### Web 界面

| 页面 | URL |
|------|-----|
| 仪表盘 | `http://localhost:2771/` |
| 对局列表 | `http://localhost:2771/matches` |
| 数据验证 | `http://localhost:2771/validate` |
| 版本历史 | `http://localhost:2771/history` |

### API

访问 `http://localhost:2771/docs` 查看 Swagger 文档。

核心端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/matches` | GET/POST | 列表/新增 |
| `/api/v1/matches/{id}` | GET/PUT/DELETE | 查询/更新/删除 |
| `/api/v1/matches/{id}/preview` | POST | 预览更新（不保存） |
| `/api/v1/validate/quick` | POST | 快速验证 |
| `/api/v1/validate/deep` | POST | 深度验证 |
| `/api/v1/validate/fix` | POST | 自动修复 |
| `/api/v1/history` | GET | Git 提交历史 |
| `/api/v1/history/{hash}` | GET | 查看 diff |
| `/api/v1/history/revert` | POST | 回滚到指定提交 |

### CLI

项目有两套 CLI：

**`mm`** — 离线操作（直接读写 TOML），通过 `pip install -e .` 安装后可用，不需要服务运行。

```bash
# 数据管理
mm init                  # 初始化 Git 版本控制
mm health                # 检查数据状态
mm list-matches -p 1     # 列出对局
mm show 0001             # 查看对局详情
mm search <关键词>        # 搜索
mm stats                 # 统计
```

**SDK CLI** — 在线操作（通过 HTTP API），服务运行后可用。

```bash
# 验证修复
python sdk/cli.py validate [--mode quick|deep]   # 验证数据
python sdk/cli.py fix                            # 自动修复
python sdk/cli.py maintain                       # 完整维护流程
python sdk/cli.py list-matches -p 1             # 列出对局
python sdk/cli.py health                         # 健康检查
```

所有 SDK CLI 命令支持 `--url` / `-u` 指定服务地址，默认 `http://localhost:2771`。

### SDK

```python
from sdk import MatchClient

client = MatchClient("http://localhost:2771")

# CRUD
client.list_matches(page=1)
client.get_match("0001")
client.create_match({...})
client.update_match("0001", {"result": "defender_win"})
client.delete_match("0001")

# 验证修复
client.quick_validate()
client.deep_validate()
client.fix()

# 版本历史
client.get_history()
client.revert_commit("abc123")
```

## 配置

通过 `.env` 文件或环境变量（`MATCH_` 前缀）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MATCH_PORT` | `8000` | 服务端口 |
| `MATCH_HOST` | `0.0.0.0` | 监听地址 |
| `MATCH_DEBUG` | `false` | 调试模式 |
| `MATCH_LOG_LEVEL` | `INFO` | 日志级别 |
| `MATCH_DATA_DIR` | `data` | 数据目录 |

## 项目结构

```
match-maintain-web/
├── src/match_maintain/
│   ├── app.py              # FastAPI 应用工厂
│   ├── config.py           # Pydantic Settings
│   ├── core/               # 横切关注点
│   │   ├── exceptions.py   # 异常定义
│   │   ├── logging.py      # 日志配置
│   │   ├── schema.py       # TOML Schema 加载器
│   │   ├── cache/          # 内存缓存
│   │   └── dependencies.py # DI
│   ├── models/             # Pydantic 模型
│   ├── domain/             # 业务逻辑（services）
│   │   ├── match_service.py
│   │   ├── validate_service.py
│   │   ├── fixer_service.py
│   │   ├── field_completer.py
│   │   └── transaction.py  # 事务/预览
│   ├── infrastructure/     # 数据访问
│   │   ├── toml_repository.py  # TOML 读写
│   │   └── git_versioning.py   # Git 操作
│   ├── api/v1/             # REST API
│   ├── web/                # Web UI (Jinja2)
│   ├── middleware/         # 中间件
│   └── cli/                # CLI 命令 (Typer)
├── sdk/                    # Python SDK
├── data/                   # TOML 数据 + Git 仓库
│   ├── matches.toml
│   ├── match_schema.toml
│   └── references/
└── tests/
```

## 技术栈

- **后端**: FastAPI
- **数据**: TOML (tomlkit) — 单数据源
- **版本控制**: Git (subprocess)
- **模板**: Jinja2
- **CLI**: Typer + Rich
- **验证**: Pydantic
- **缓存**: 内存缓存 (TTL)
