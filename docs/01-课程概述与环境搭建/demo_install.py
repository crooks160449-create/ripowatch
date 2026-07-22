"""环境验证脚本 — 检查 Python 开发环境是否正确配置。"""

import sys


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  [WARN] 建议使用 Python 3.10 或更高版本")
    else:
        print("  [OK] 版本满足要求")

    return version


def check_pip():
    """检查 pip 是否可用"""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  [OK] pip 可用: {result.stdout.strip()[:50]}...")
            return True
    except Exception:
        pass
    print("  [WARN] pip 可能未正确安装")
    return False


def check_encoding():
    """检查默认编码"""
    import sys
    print(f"  默认编码: {sys.getdefaultencoding()}")
    if sys.getdefaultencoding().lower() == "utf-8":
        print("  [OK] UTF-8 编码")
    else:
        print("  [WARN] 建议使用 UTF-8 编码")


def check_path():
    """检查工作路径"""
    import os
    cwd = os.getcwd()
    print(f"  工作目录: {cwd}")


def main():
    print("=" * 50)
    print("  RepoWatch 课程 — 环境验证脚本")
    print("=" * 50)
    print()

    print("[1] Python 版本检查")
    check_python_version()
    print()

    print("[2] pip 包管理器检查")
    check_pip()
    print()

    print("[3] 编码检查")
    check_encoding()
    print()

    print("[4] 工作路径")
    check_path()
    print()

    print("=" * 50)
    print("  环境检查完成！如果所有项都是 [OK]，")
    print("  说明你的环境已准备就绪，可以开始编程了。")
    print("=" * 50)


if __name__ == "__main__":
    main()
