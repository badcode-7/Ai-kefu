FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
ENV KNOWLEDGE_DIR=/app/knowledge_data

# 创建知识库目录
RUN mkdir -p /app/knowledge_data

# 暴露端口
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]