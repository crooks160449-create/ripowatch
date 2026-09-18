# RepoWatch 课程网站框架仓库

> 本仓库是课程的框架仓库（开发者维护）。
> 课程内容已迁移到独立的内容仓库 repowatch-content。

## 双仓库架构

```
框架仓库 repowatch               内容仓库 repowatch-content
（开发者维护，老师不碰）           （老师和助教编辑内容）
                                  docs/
mkdocs.yml                        内容同步工具.py
hooks/                            启动内容同步.bat
Dockerfile                        .gitlab-ci.yml
docker-compose.yml                （自动监听 + 自动部署）
requirements.txt
                                        |
                                        | watcher 自动 push
                                        v
                                 GitLab Runner 构建
                                        |
                                        v
                                   课程网站
```

## 两个仓库的分工

| 仓库 | 谁用 | 内容 |
|---|---|---|
| repowatch（本仓库） | 开发者 | 框架代码、构建钩子、部署配置 |
| repowatch-content | 老师/助教 | 课程内容（docs）、自动同步工具 |

原则：老师只碰内容仓库，开发者只改框架仓库。

## 开发者本地开发

框架仓库的 docs/ 已被 gitignore（本地保留仅用于预览）：

```bash
# 1. 克隆框架仓库
git clone https://git.tsinghua.edu.cn/zhangtw24/repowatch.git

# 2. 拉取课程内容到 docs/（本地预览用）
git clone https://git.tsinghua.edu.cn/zhangtw24/repowatch-content.git docs

# 3. 安装依赖
pip install -r requirements.txt

# 4. 本地预览
mkdocs serve
```

## 框架变更如何发布

开发者在框架仓库改完代码后，把变更同步到内容仓库：

```bash
cp mkdocs.yml /home/libs/course-content/
cp -r hooks/ /home/libs/course-content/
cp Dockerfile docker-compose.yml /home/libs/course-content/
```

内容仓库的 watcher 会自动提交推送，触发网站重新构建。

注意：内容仓库的 `docker-compose.yml` 中媒体目录要用服务器的绝对路径：

```yaml
volumes:
  - /home/libs/course-content/media:/usr/share/nginx/html/media
```

框架仓库保持相对路径 `./media`（本地开发用）。视频文件存放在服务器的 `media/videos/`，由 watcher 生成索引，不进 Git。

## 目录说明

```
repowatch/
|-- mkdocs.yml          # 网站配置
|-- hooks/              # 构建钩子（PPTX/云盘视频/画廊）
|-- Dockerfile          # Docker 镜像
|-- docker-compose.yml  # 部署编排
|-- requirements.txt    # Python 依赖
|-- 部署说明.md          # 部署运维文档
|-- 使用说明.md          # 内容维护手册
`-- legacy/             # 早期 FastAPI 版本归档
```

## 线上地址

- GitHub Pages（公网备份）：https://crooks160449-create.github.io/ripowatch/
- 校园服务器：http://10.10.10.41:8080/（实验室内网）
