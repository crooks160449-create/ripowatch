# 旧版 RepoWatch（历史存档）

这里是项目早期 FastAPI 版本的代码，已于 2026-09 月归档。

## 为什么归档

项目最初是一个基于 FastAPI 的本地文件监听工具（自动 Git 提交、文件预览）。
后来按照课程需求，技术路线转向 **MkDocs 静态网站 + 清华 Git 自动部署**，
旧代码不再使用，因此移入本目录保存。

## 包含内容

- `main.py`：FastAPI 入口
- `git_manager.py`：Git 操作 + PPTX/DOCX 解析
- `watcher.py`：watchdog 文件监听
- `templates/`：早期 HTML 模板
- `watched_repos/`：早期演示仓库（含演示文件）

## 后续用途

如果未来需要做"网页后台管理"（CMS），其中的 PPTX 解析逻辑
（`get_pptx_content` 等）可以复用。

## 恢复方法

本目录内容也保存在 Git 历史中，随时可用 `git log --all -- <文件>` 找回。
