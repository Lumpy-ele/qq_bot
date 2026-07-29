# QQ Bot 开发文档（AGENTS.md）

## 一、项目概述

基于个人小号 QQ，在本地搭建 HTTP API 服务，并通过内网穿透暴露到公网，允许外部调用方通过该 API 向指定 QQ 好友或群聊发送定制消息。

### 核心需求

1. 使用一个小号 QQ 作为消息发送载体
2. 服务运行在本地机器，通过内网穿透提供公网可访问的 HTTP API
3. 调用方可向指定好友 / 群聊发送文本、图片等定制消息
4. 具备基本的鉴权与防护能力，防止被恶意调用

### 技术选型

| 组件 | 选型 | 说明 |
| --- | --- | --- |
| QQ 协议端 | NapCat / Lagrange.OneBot | 基于 NTQQ 的 OneBot 11 实现，提供正向 WebSocket + HTTP |
| 协议规范 | OneBot 11 | 标准化接口，便于替换底层实现 |
| API 网关 | Python + FastAPI | 轻量、异步、自带 OpenAPI 文档 |
| 内网穿透 | Cloudflare Tunnel（cloudflared） | 出站长连接，无需公网 IP / 开放端口，自带 HTTPS |
| 公网入口 | `*.trycloudflare.com` 随机临时域名 | 免注册、免自有域名；重启可能变化，需同步给调用方 |
| 进程管理 | Docker Compose（`restart: unless-stopped`） | 统一编排协议端 + 网关 + 隧道，异常自启 |
| 部署环境 | 本地机器（Windows + Docker Desktop） | 无需云服务器，仅本机长开即可 |

---

## 二、开发目录结构

```
qq_bot/
├── AGENTS.md                      # 本开发文档
├── README.md                      # 用户使用说明（可选）
├── docker-compose.yml             # 容器编排（协议端 + 网关 + 隧道）
├── Dockerfile                     # FastAPI 网关镜像构建
├── .env.example                   # 环境变量样例
├── .gitignore
│
├── config/                        # 配置文件目录
│   ├── settings.py                # 全局配置加载（环境变量优先）
│   └── logging.conf               # 日志配置
│
├── app/                           # FastAPI 应用主目录
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口、路由注册、生命周期
│   ├── api/                       # 对外 HTTP 路由
│   │   ├── __init__.py
│   │   ├── deps.py                # 鉴权依赖（API Key 校验）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── send_private.py    # 发送私聊消息接口
│   │       ├── send_group.py      # 发送群聊消息接口
│   │       └── health.py          # 健康检查接口
│   │
│   ├── schemas/                   # Pydantic 请求 / 响应模型
│   │   ├── __init__.py
│   │   ├── message.py             # 消息体模型（text / image / at 等）
│   │   └── common.py              # 通用响应包装
│   │
│   ├── services/                  # 业务服务层
│   │   ├── __init__.py
│   │   ├── onebot_client.py       # OneBot HTTP 客户端封装
│   │   └── message_builder.py     # OneBot 消息段构造
│   │
│   ├── core/                      # 核心组件
│   │   ├── __init__.py
│   │   ├── exceptions.py          # 自定义异常
│   │   └── rate_limit.py          # 简单限流（可选）
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       └── logger.py              # 日志封装
│
├── tests/                         # 单元测试与集成测试
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── test_send_private.py
│   ├── test_send_group.py
│   └── test_auth.py
│
├── scripts/                       # 运维脚本
│   ├── start.sh                   # 启动并打印当前 *.trycloudflare.com 公网 URL
│   └── test_send.sh               # 手动联调脚本（curl 调用，URL 运行时填入）
│
└── logs/                          # 运行日志（gitignore）
```

> 说明：原 `deploy/`（nginx.conf / Caddyfile / systemd）已移除——HTTPS 终止由 Cloudflare 边缘完成，进程守护由 Docker `restart: unless-stopped` 完成，不再需要本地反向代理与 systemd 单元。

---

## 三、开发阶段目标与验收标准

### 阶段 0：环境与账号准备

**目标**

- 准备一台长期可开的本地机器（Windows），安装 Docker Desktop
- 注册 Cloudflare 账号（用于 Cloudflare Tunnel；quick tunnel 模式下仅本地 cloudflared 即可，账号可选）
- 准备一个独立 QQ 小号，完成登录并保持在线
- 完成协议端（NapCat / Lagrange）安装与 QQ 登录

**验收标准**

- [x] 本地 `docker --version` 与 `docker compose version` 可正常输出
- [x] 本地机器无需公网 IP，无需在路由器开放任何端口
- [x] QQ 小号在协议端中显示"在线"状态
- [x] 协议端 HTTP 接口（如 `http://127.0.0.1:3000`）可本地 `curl` 调用
- [x] 通过协议端 `send_private_msg` / `send_group_msg` 接口可成功向测试好友 / 群发送一条测试消息

---

### 阶段 1：项目骨架搭建

**目标**

- 初始化 Python 项目，建立目录结构
- FastAPI 应用可本地启动并访问 `/health`
- 配置加载机制（`.env` + `settings.py`）就绪
- 日志输出到文件与控制台

**验收标准**

- [ ] 执行 `uvicorn app.main:app --reload` 可正常启动
- [ ] 访问 `GET /health` 返回 `{"status": "ok"}`
- [ ] 访问 `GET /docs` 可看到 Swagger 文档
- [ ] 修改 `.env` 中日志级别后，重启生效
- [ ] `logs/` 目录下生成结构化日志文件

---

### 阶段 2：OneBot 客户端封装

**目标**

- 封装 `OneBotClient`，对接协议端 HTTP 接口
- 实现消息段（MessageSegment）构造器，支持文本、图片、@、表情
- 统一异常处理与超时控制

**验收标准**

- [ ] `OneBotClient.send_private_msg(user_id, message)` 可成功发送
- [ ] `OneBotClient.send_group_msg(group_id, message)` 可成功发送
- [ ] 消息段构造器支持 `text` / `image` / `at` 三种类型
- [ ] 协议端返回非 0 `retcode` 时，抛出可识别的 `OneBotError`
- [ ] 单元测试覆盖消息段构造逻辑（`tests/test_*` 通过）

---

### 阶段 3：对外 API 实现

**目标**

- 实现 `POST /api/v1/send/private`：发送私聊消息
- 实现 `POST /api/v1/send/group`：发送群聊消息
- 实现 API Key 鉴权中间件
- 统一响应格式与错误码

**接口契约**

请求示例：

```http
POST /api/v1/send/private
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "user_id": 123456789,
  "message": [
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"url": "https://example.com/a.png"}}
  ]
}
```

响应示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {"message_id": 123456}
}
```

**验收标准**

- [ ] 接口可接收 JSON 请求并成功转发到协议端
- [ ] 缺少或错误 `Authorization` 时返回 `401`
- [ ] 参数校验失败返回 `422` 并附带明确错误信息
- [ ] 协议端失败时返回非 0 `code` 与可读 `msg`
- [ ] 接口测试 `tests/test_send_*.py` 全部通过
- [ ] Swagger 文档中可在线调试该接口

---

### 阶段 4：本地部署 + Cloudflare 隧道

**目标**

- 使用 Docker Compose 编排协议端 + FastAPI 网关 + cloudflared 隧道三个 service
- cloudflared 以 quick tunnel 模式启动，将 `http://api:8000` 暴露为 `https://*.trycloudflare.com`
- 容器统一配置 `restart: unless-stopped`，异常退出自动重启
- 日志按天切割（容器内输出 + 宿主机 `logs/` 卷挂载）

**docker-compose 服务结构**

```
services:
  onebot:   NapCat/Lagrange 协议端，仅 compose 内网可达
  api:      FastAPI 网关，暴露 :8000 给 tunnel，depends_on: onebot
  tunnel:   cloudflared/cloudflared:latest
            command: tunnel --url http://api:8000
            depends_on: api
```

**验收标准**

- [ ] `docker compose up -d` 可一键拉起 onebot / api / tunnel 全部服务
- [ ] 从 `tunnel` 容器日志可读取到形如 `https://<random>.trycloudflare.com` 的公网 URL
- [ ] 公网通过该 `https://*.trycloudflare.com/api/v1/health` 可访问，返回 `{"code":0,...}`
- [ ] HTTPS 由 Cloudflare 边缘终止，浏览器无证书告警
- [ ] `docker compose stop api` 后，Docker 在数秒内自动拉起 api 容器
- [ ] 宿主机 `logs/` 目录可见按天滚动的日志文件，保留最近 7 天

**注意事项**

- quick tunnel 的随机域名在 `tunnel` 容器重建后会变化；调用方需从 `start.sh` 输出获取最新 URL
- 如需稳定 URL，后续可改为 named tunnel + 自有域名（注册 Cloudflare 账号并将域名 DNS 托管到 CF），不在本期范围

---

### 阶段 5：安全与稳定性加固

**目标**

- 接入限流（单 IP / 单 API Key QPS 限制）
- 敏感参数（API Key、QQ 账号）仅通过环境变量注入
- 增加调用审计日志（谁、何时、向谁发了什么）
- 增加熔断 / 重试机制应对协议端抖动

**验收标准**

- [ ] 单 IP 超过阈值 QPS 时返回 `429`
- [ ] 代码与配置中无硬编码密钥
- [ ] 每次调用在审计日志中记录：调用方 IP、API Key 标识、目标 QQ、消息摘要、结果
- [ ] 协议端连续失败时触发熔断，返回 `503` 并告警
- [ ] 压测下（如 50 QPS 持续 1 分钟）服务无崩溃、无内存泄漏

---

### 阶段 6：联调与交付

**目标**

- 完成端到端联调
- 提供使用示例与调用脚本
- 文档完善（README + AGENTS.md）

**验收标准**

- [x] 通过 `scripts/test_send.sh` 可一键完成"私聊 + 群聊"发消息联调（URL 从 `start.sh` 输出获取后填入）
- [x] README 中给出至少 3 种语言（curl / Python / Node.js）调用示例，并说明公网 URL 为 `*.trycloudflare.com` 随机域名、重启可能变化
- [x] AGENTS.md 内容与实际实现一致
- [x] 所有验收项打勾，交付可稳定运行的服务

---

## 四、关键技术约束与风险

| 约束 / 风险 | 说明 | 应对 |
| --- | --- | --- |
| QQ 风控 | 小号频繁 / 异常消息易被封禁 | 控制发送频率，模拟真人节奏，避免批量 @ |
| 协议端合规 | 第三方协议存在被腾讯打击风险 | 仅个人使用，不对外公开，遵守相关协议 |
| 公网入口稳定性 | quick tunnel 随机域名重启后变化；Cloudflare 国内访问偶有波动 | `start.sh` 每次启动打印最新 URL 同步调用方；后续可升级 named tunnel + 自有域名 |
| 本地机器可用性 | 本地断电 / 重启 / 休眠会导致公网 API 不可用 | 设置机器不休眠、Docker Desktop 开机自启、容器 `restart: unless-stopped` |
| 协议端掉线 | NTQQ 登录态可能失效 | 健康检查 + 自动重连 + 告警通知 |
| 图片消息 | 需可访问的 URL 或 base64 | 提供 URL 模式，避免上传大文件 |
| API 鉴权 | 隧道一旦泄露 URL 可被滥用 | 强制 API Key + 限流 + 审计（阶段 5 落地） |

---

## 五、里程碑总览

| 阶段 | 关键产出 | 状态 |
| --- | --- | --- |
| 0 | 本地环境 + Docker + 协议端就绪，QQ 在线 | ☑ |
| 1 | FastAPI 骨架 + 健康检查 | ☑ |
| 2 | OneBot 客户端封装 | ☑ |
| 3 | 对外 API + 鉴权 | ☑ |
| 4 | 本地 Docker Compose + Cloudflare 隧道 | ☑ |
| 5 | 安全加固 | ☐ |
| 6 | 联调交付 | ☑ |
