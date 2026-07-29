#!/usr/bin/env bash
# 启动 qq_bot 全部服务并打印当前公网 URL
#
# 用法：
#   bash scripts/start.sh
#
# 依赖：docker、docker compose、grep、awk
# 说明：quick tunnel 模式下 URL 在 tunnel 容器启动后才生成，
#       本脚本会轮询容器日志直至抓到 https://*.trycloudflare.com。

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
URL_POLL_TIMEOUT="${URL_POLL_TIMEOUT:-60}"  # 抓 URL 最长等待秒数

echo "==> 启动 docker compose 服务（onebot / api / tunnel）..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> 等待 tunnel 容器分配公网 URL（最多 ${URL_POLL_TIMEOUT}s）..."
elapsed=0
url=""
while [ "$elapsed" -lt "$URL_POLL_TIMEOUT" ]; do
    # cloudflared quick tunnel 启动时会输出形如：
    #   Your quick Tunnel has been created! Visit it at: https://xxx.trycloudflare.com
    url="$(docker logs qq_bot_tunnel 2>&1 \
            | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' \
            | tail -n 1 || true)"
    if [ -n "$url" ]; then
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ -z "$url" ]; then
    echo "!! 未能从 tunnel 容器日志抓取到公网 URL"
    echo "!! 请手动执行: docker logs qq_bot_tunnel"
    exit 1
fi

echo ""
echo "============================================================"
echo " 服务已启动"
echo "------------------------------------------------------------"
echo " 公网入口:  $url"
echo " 健康检查:  $url/api/v1/health"
echo " Swagger :  $url/docs"
echo "------------------------------------------------------------"
echo " 注意: quick tunnel 域名在 tunnel 容器重建后会变化"
echo "       调用方需以本次输出为准"
echo "============================================================"
