# RepoWatch 课程网站

基于 **MkDocs + Material** 的课程资源网页化托管方案。将课程讲义、代码示例、PPT 课件、PDF 文档统一托管，自动构建为可在线浏览的课程网站。

## 线上地址

- GitHub Pages：https://crooks160449-create.github.io/ripowatch/
- 清华 Git（代码仓库）：https://git.tsinghua.edu.cn/zhangtw24/repowatch

## 项目结构

```
repo-watcher/
├── mkdocs.yml          # 网站全局配置（主题、导航、插件）
├── docs/               # 课程内容根目录
│   ├── index.md        # 首页
│   ├── 01-课程概述与环境搭建/
│   ├── 02-Python基础语法/
│   ├── 03-进阶项目实操/
│   └── 资源下载/
├── hooks/
│   ├── pptx_converter.py   # PPTX 自动转图片/文字钩子
│   └── cloud_media.py      # 清华云盘视频外链自动解析钩子
├── .github/workflows/ci.yml # GitHub Pages 自动部署
├── .gitlab-ci.yml          # 清华 Git 自动部署（自建 Runner）
├── Dockerfile              # Docker 多阶段构建镜像
├── docker-compose.yml      # 本地/服务器一键部署
├── 部署说明.md             # Runner/Nginx/Docker 部署文档
├── 使用说明.md             # 老师/助教内容维护手册
└── requirements.txt
```

## 本地预览

```bash
# 安装依赖
pip install mkdocs mkdocs-material mkdocs-git-revision-date-localized-plugin pymdown-extensions python-pptx Pillow

# 启动本地预览（保存文件自动刷新）
mkdocs serve

# 浏览器打开 http://127.0.0.1:8000
```

## 更新课程内容

三种常见操作：

### 1. 添加/修改页面

直接在 `docs/` 下新建或编辑 `.md` 文件。文件夹名即章节名。

### 2. 添加/删除章节

编辑 `mkdocs.yml` 的 `nav:` 部分，添加或删除对应条目。

### 3. 上传 PPT 课件

把 `.pptx` 文件放入 `docs/` 目录，构建时会自动转为在线预览页面（无需手工搬运内容）。

所有修改完成后：

```bash
git add .
git commit -m "更新课程内容"
git push
```

推送后自动构建部署，网站约 1 分钟内更新。

## 权限管理

本项目托管在清华 Git（GitLab），权限由 GitLab 角色控制：

| 角色 | 权限 |
|---|---|
| Owner | 项目所有者，全部权限 |
| Maintainer | 可编辑内容、push、管理成员 |
| Developer | 可 push 代码 |
| Reporter | 只读，可查看代码 |

建议：课程老师设为 Maintainer，学生设为 Reporter。

## 部署架构

```
老师编辑内容 → git push → CI 自动构建 → 部署到服务器 → 学生浏览
```

当前支持两种部署：

1. **GitHub Pages**（已启用）：GitHub Actions 自动构建部署
2. **清华 Git + 自建 Runner**（待服务器到位）：GitLab CI 构建，部署到校园服务器

## 多课程模板

新开一门课程时：

1. 复制本项目为新仓库
2. 修改 `mkdocs.yml` 中的 `site_name` 和 `site_url`
3. 清空 `docs/` 中旧课程内容，按章节结构重新组织
4. 配置对应部署 CI

课程框架、PPTX 转换钩子、主题配置均可直接复用。

## 待办事项

- [ ] 在老师服务器上注册 GitLab Runner
- [ ] 配置 Nginx 托管构建产物
- [ ] 建立多课程 Group 和项目权限
- [ ] 完善课程内容维护文档
