# QQ Bot API

基于个人小号 QQ 的公网消息发送 API。本地部署 OneBot 协议端 + FastAPI 网关，通过 Cloudflare Tunnel 暴露为公网 HTTPS 接口，调用方可向指定 QQ 好友或群聊发送定制消息。

## 架构

```
调用方 ──HTTPS──> Cloudflare Tunnel ──> FastAPI 网关(:8000) ──HTTP──> NapCat OneBot(:3000) ──> QQ
                                          ↑ 鉴权: API Key
```

| 组件 | 选型 |
| --- | --- |
| QQ 协议端 | NapCat (OneBot 11) |
| API 网关 | Python + FastAPI |
| 内网穿透 | Cloudflare Tunnel (quick tunnel) |
| 进程管理 | Docker Compose |

## 快速开始

### 1. 准备环境

- 已安装 Docker Desktop（含 `docker` 与 `docker compose`）
- 准备一个 QQ 小号

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少配置：
#   API_KEY=<自定义一个足够长的随机字符串>
#   ONEBOT_QQ=<小号 QQ 号>
```

### 3. 启动服务

```bash
bash scripts/start.sh
```

首次启动需要扫码登录 QQ：
- 浏览器访问 `http://127.0.0.1:6099/webui`
- Token 从 `docker logs qq_bot_onebot` 输出中获取（搜索 `WebUi Token`）
- 在 WebUI 中扫码完成登录

启动成功后，`start.sh` 会打印公网 URL，形如：
```
公网入口:  https://<random>.trycloudflare.com
```

> **重要**：quick tunnel 模式下，公网 URL 为 `*.trycloudflare.com` 随机临时域名，**`tunnel` 容器重建后会变化**，调用方需以 `start.sh` 输出为准。

### 4. 联调验证

```bash
export BASE_URL=https://<random>.trycloudflare.com
export API_KEY=<你配置的 API_KEY>
bash scripts/test_send.sh
```

## 接口文档

启动后访问 Swagger UI：`<BASE_URL>/docs`

### 健康检查

```http
GET /api/v1/health
```

响应：
```json
{"code": 0, "msg": "ok", "data": {"status": "ok", "app": "QQ Bot API", "version": "0.1.0"}}
```

### 发送私聊消息

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

### 发送群聊消息

```http
POST /api/v1/send/group
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "group_id": 987654321,
  "message": [
    {"type": "text", "data": {"text": "群消息"}}
  ]
}
```

### 统一响应格式

```json
{
  "code": 0,
  "msg": "ok",
  "data": {"message_id": 123456}
}
```

| HTTP 状态 | 含义 |
| --- | --- |
| 200 | 成功（`code=0`）或协议端业务失败（`code!=0`） |
| 401 | 缺少/错误 API Key |
| 422 | 参数校验失败 |
| 503 | 协议端不可达 |
| 504 | 协议端超时 |

### 支持的消息段类型

| type | data 字段 |
| --- | --- |
| `text` | `text` |
| `image` | `url`, `cache?`, `proxy?`, `timeout?` |
| `at` | `qq`（`all` 表示全体） |
| `face` | `id` |
| `reply` | `id` |

`message` 字段也支持直接传纯字符串，如 `"你好"`，等价于单段文本。

## 调用示例

以下示例均假设：
- `BASE_URL=https://abc-xyz.trycloudflare.com`
- `API_KEY=your-secret-key`

### curl

```bash
# 私聊
curl -X POST https://abc-xyz.trycloudflare.com/api/v1/send/private \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "message": [
      {"type": "text", "data": {"text": "你好"}},
      {"type": "image", "data": {"url": "https://example.com/a.png"}}
    ]
  }'

# 群聊
curl -X POST https://abc-xyz.trycloudflare.com/api/v1/send/group \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 987654321,
    "message": [{"type": "text", "data": {"text": "群消息"}}]
  }'
```

### Python

```python
import httpx

BASE_URL = "https://abc-xyz.trycloudflare.com"
API_KEY = "your-secret-key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 私聊
resp = httpx.post(
    f"{BASE_URL}/api/v1/send/private",
    headers=HEADERS,
    json={
        "user_id": 123456789,
        "message": [
            {"type": "text", "data": {"text": "你好"}},
            {"type": "image", "data": {"url": "https://example.com/a.png"}},
        ],
    },
    timeout=30,
)
print(resp.json())

# 群聊
resp = httpx.post(
    f"{BASE_URL}/api/v1/send/group",
    headers=HEADERS,
    json={
        "group_id": 987654321,
        "message": [{"type": "text", "data": {"text": "群消息"}}],
    },
    timeout=30,
)
print(resp.json())
```

### Node.js

```javascript
// Node 18+ 内置 fetch，无需额外依赖
const BASE_URL = "https://abc-xyz.trycloudflare.com";
const API_KEY = "your-secret-key";
const HEADERS = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

// 私聊
const privateResp = await fetch(`${BASE_URL}/api/v1/send/private`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({
    user_id: 123456789,
    message: [
      { type: "text", data: { text: "你好" } },
      { type: "image", data: { url: "https://example.com/a.png" } },
    ],
  }),
});
console.log(await privateResp.json());

// 群聊
const groupResp = await fetch(`${BASE_URL}/api/v1/send/group`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({
    group_id: 987654321,
    message: [{ type: "text", data: { text: "群消息" } }],
  }),
});
console.log(await groupResp.json());
```

## 运维

### 查看日志

```bash
# 网关日志（按天滚动）
ls logs/

# 容器实时日志
docker logs -f qq_bot_api
docker logs -f qq_bot_onebot
docker logs -f qq_bot_tunnel
```

### 重启服务

```bash
docker compose restart api      # 仅重启网关
docker compose restart tunnel   # 重启隧道（公网 URL 会变！）
docker compose down && bash scripts/start.sh  # 全量重启
```

### NapCat WebUI

```bash
# 获取 token
docker logs qq_bot_onebot 2>&1 | grep "WebUi Token"
# 浏览器访问
# http://127.0.0.1:6099/webui?token=<token>
```

## 注意事项

1. **公网 URL 不稳定**：quick tunnel 域名在 `tunnel` 容器重建后会变化，调用方需从 `start.sh` 输出获取最新 URL。如需稳定 URL，可升级为 named tunnel + 自有域名。
2. **QQ 风控**：小号频繁或异常消息易被封禁，请控制发送频率，避免批量 @。
3. **协议端掉线**：NTQQ 登录态可能失效，可通过健康检查 + WebUI 重新扫码恢复。
4. **本地机器可用性**：本地断电/休眠会导致公网 API 不可用，建议设置机器不休眠、Docker Desktop 开机自启。

## 项目结构

详见 [AGENTS.md](AGENTS.md)。
