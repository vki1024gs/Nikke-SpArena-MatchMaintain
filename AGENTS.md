# Match Maintenance — Agent 交互指南

NIKKE PVP 对局数据维护工具，提供 **Web UI**、**REST API** 和 **CLI** 三种交互方式。

**TOML 是唯一数据源，每次写入自动 git commit。**

## 服务地址

- **默认端口**: `8000`
- **基础 URL**: `http://localhost:2771`

## API 文档

访问 `http://localhost:2771/docs` 查看 OpenAPI/Swagger 文档。

## Python SDK

```python
from sdk import MatchClient

client = MatchClient("http://localhost:2771")

# 检查服务状态
status = client.health()

# CRUD
client.create_match({"id": "0099", "defender_team": [...], "attacker_team": [...], "result": "attacker_win"})
client.update_match("0099", {"result": "defender_win", "reason": "result corrected"})
client.delete_match("0099")

# 验证 + 修复
result = client.quick_validate()
if not result["passed"]:
    client.fix()

# 完整维护流程
client.full_maintenance()

# 版本历史
history = client.get_history()
client.revert_commit("abc123")
```

## CLI 工具

项目有两套 CLI，注意区分：

### `mm` — 离线操作（直接读写 TOML）

通过 `pip install -e .` 安装后可用，不需要服务运行。

```bash
mm init                    # 初始化 Git 版本控制
mm health                  # 检查数据状态
mm list-matches -p 1       # 列出对局
mm show 0001               # 查看详情
mm search <关键词>          # 搜索
mm stats                   # 统计
```

### SDK CLI — 在线操作（通过 HTTP API）

服务运行后可用，通过 `python sdk/cli.py <command>` 或 `python -m sdk.cli <command>`。

```bash
python sdk/cli.py health                         # 健康检查
python sdk/cli.py validate --mode quick          # 快速验证
python sdk/cli.py validate --mode deep           # 深度验证
python sdk/cli.py fix                            # 自动修复
python sdk/cli.py maintain                       # 完整维护流程
python sdk/cli.py list-matches -p 1             # 列出对局
```

所有 SDK CLI 命令支持 `--url` / `-u` 指定服务地址，默认 `http://localhost:2771`。

## 核心端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/matches` | GET/POST | 列表/新增 |
| `/api/v1/matches/{id}` | GET/PUT/DELETE | 查询/更新/删除 |
| `/api/v1/matches/{id}/preview` | POST | 预览更新 |
| `/api/v1/validate/quick` | POST | 快速验证 |
| `/api/v1/validate/deep` | POST | 深度验证 |
| `/api/v1/validate/fix` | POST | 自动修复 |
| `/api/v1/history` | GET | Git 历史 |
| `/api/v1/history/revert` | POST | 回滚 |

## 注意事项

- **无需鉴权**，仅限内网/本地使用
- **数据文件**: `data/matches.toml`
- **配置文件**: `.env` 或 `MATCH_*` 环境变量
- **版本历史**: `git log` 在 `data/` 目录下查看
- **数据变更**: 每次写入自动 commit，可追溯可回滚
