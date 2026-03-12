# ==============================================
# Quant-Trade System - Frontend Dockerfile
# ==============================================
# 多阶段构建：构建 -> 生产镜像
# ==============================================

# ==============================================
# 构建阶段
# ==============================================
FROM node:20-alpine as builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --legacy-peer-deps

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# ==============================================
# 生产阶段 - 使用 Nginx 服务静态文件
# ==============================================
FROM nginx:alpine as runner

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/build /usr/share/nginx/html

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
