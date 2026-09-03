# ============================================================
# RepoWatch 课程网站 Docker 镜像
# 阶段1：构建 MkDocs 静态网站（含 PPTX 转高清图）
# 阶段2：用 nginx 托管静态文件
# ============================================================

# ---------- 阶段1：构建 ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# 使用清华 Debian 镜像加速 apt（国内服务器必需）
RUN sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list.d/debian.sources \
    || sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list \
    || true

# 安装 LibreOffice（PPTX 转图片）+ poppler（PDF 转图片）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libreoffice-impress \
    poppler-utils \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 避免 GitPython 在容器内无仓库时报错干扰构建
ENV GIT_PYTHON_REFRESH=quiet

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目源码
COPY mkdocs.yml .
COPY hooks/ hooks/
COPY docs/ docs/

# 构建静态网站
RUN mkdocs build

# ---------- 阶段2：托管 ----------
FROM nginx:1.27-alpine

# 把构建产物复制到 nginx 默认站点目录
COPY --from=builder /app/site /usr/share/nginx/html

EXPOSE 80

# 静态站无需额外命令，nginx 直接托管
