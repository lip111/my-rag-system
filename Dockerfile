# 使用 python:3.11-slim 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从构建上下文复制所有内容到镜像的工作目录
COPY . .

# 构建镜像过程中执行pip命令
RUN pip install --no-cache-dir -r requirements.txt

# 声明监听的端口
EXPOSE 8501

# 指定容器启动时默认执行的命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]