#!/usr/bin/env bash
# 一键联调脚本：通过公网（或本地）API 网关发送"私聊 + 群聊"测试消息
#
# 用法：
#   bash scripts/test_send.sh
#
# 必填环境变量（可在 .env 或 shell 中 export）：
#   BASE_URL    API 网关地址，例如 https://abc-xyz.trycloudflare.com
#               （从 scripts/start.sh 输出获取；本地直跑可用 http://127.0.0.1:8000）
#   API_KEY     调用 /api/v1/send/* 所需的 Bearer Token
#
# 可选环境变量（默认值见下方）：
#   TEST_USER_ID    私聊测试目标 QQ 号
#   TEST_GROUP_ID   群聊测试目标群号
#   TEST_TEXT       测试消息文本
#
# 示例：
#   BASE_URL=https://abc.trycloudflare.com API_KEY=xxx \
#   TEST_USER_ID=3157396832 TEST_GROUP_ID=1107376628 \
#   bash scripts/test_send.sh

set -euo pipefail

# ---- 参数校验 ----
BASE_URL="${BASE_URL:-}"
API_KEY="${API_KEY:-}"
TEST_USER_ID="${TEST_USER_ID:-3157396832}"
TEST_GROUP_ID="${TEST_GROUP_ID:-1107376628}"
TEST_TEXT="${TEST_TEXT:-QQ Bot 联调测试消息}"

if [ -z "$BASE_URL" ]; then
    echo "!! 缺少环境变量 BASE_URL"
    echo "!! 请先执行 bash scripts/start.sh 获取公网 URL，然后："
    echo "!!   export BASE_URL=https://xxx.trycloudflare.com"
    exit 1
fi
if [ -z "$API_KEY" ]; then
    echo "!! 缺少环境变量 API_KEY"
    echo "!! 请检查 .env 中的 API_KEY 配置"
    exit 1
fi

# 去除尾部斜杠，避免双斜杠
BASE_URL="${BASE_URL%/}"

echo "============================================================"
echo " QQ Bot 联调测试"
echo "------------------------------------------------------------"
echo " BASE_URL : $BASE_URL"
echo " USER_ID  : $TEST_USER_ID"
echo " GROUP_ID : $TEST_GROUP_ID"
echo " TEXT     : $TEST_TEXT"
echo "============================================================"

# ---- 1. 健康检查 ----
echo ""
echo "==> [1/3] 健康检查: GET /api/v1/health"
http_code=$(curl -s -o /tmp/qq_bot_health.json -w "%{http_code}" \
    "${BASE_URL}/api/v1/health")
echo "    HTTP $http_code"
cat /tmp/qq_bot_health.json && echo
if [ "$http_code" != "200" ]; then
    echo "!! 健康检查失败"
    exit 1
fi

# ---- 2. 私聊 ----
echo ""
echo "==> [2/3] 发送私聊: POST /api/v1/send/private"
http_code=$(curl -s -o /tmp/qq_bot_private.json -w "%{http_code}" \
    -X POST "${BASE_URL}/api/v1/send/private" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":${TEST_USER_ID},\"message\":[{\"type\":\"text\",\"data\":{\"text\":\"[私聊] ${TEST_TEXT}\"}}]}")
echo "    HTTP $http_code"
cat /tmp/qq_bot_private.json && echo
if [ "$http_code" != "200" ]; then
    echo "!! 私聊发送失败"
    exit 1
fi

# ---- 3. 群聊 ----
echo ""
echo "==> [3/3] 发送群聊: POST /api/v1/send/group"
http_code=$(curl -s -o /tmp/qq_bot_group.json -w "%{http_code}" \
    -X POST "${BASE_URL}/api/v1/send/group" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"group_id\":${TEST_GROUP_ID},\"message\":[{\"type\":\"text\",\"data\":{\"text\":\"[群聊] ${TEST_TEXT}\"}}]}")
echo "    HTTP $http_code"
cat /tmp/qq_bot_group.json && echo
if [ "$http_code" != "200" ]; then
    echo "!! 群聊发送失败"
    exit 1
fi

echo ""
echo "============================================================"
echo " 联调完成：请确认目标 QQ 是否收到 2 条测试消息"
echo "============================================================"
