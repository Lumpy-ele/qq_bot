# FastAPI 网关镜像
FROM python:3.11-slim

# 设置时区（日志时间与本地一致）
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先装依赖（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝业务代码
COPY app/ ./app/
COPY config/ ./config/
COPY .env ./

# 日志目录（挂载卷用）
RUN mkdir -p /app/logs

EXPOSE 8000

# 生产模式启动（无 --reload）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
