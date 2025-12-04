"""
发布 Ant Build Menu 到 Gitee，自动覆盖同名 Release/Tag，并上传 dist 全部产物。

需求实现：
- 版本号默认从 setup.py 读取，强制前缀大写 V
- 如同名 Release/Tag 已存在，先删除后重建
- 自动上传 dist 目录下所有文件（含子目录）
- 不做 git tag/push
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import requests
except ImportError as exc:  # pragma: no cover - 环境依赖提示
        print("缺少 requests 库，请先执行: pip install requests")
        sys.exit(1)


BASE_URL = "https://gitee.com/api/v5"


def format_version(raw: str) -> str:
    v = (raw or "").strip()
    if not v:
        raise ValueError("版本号为空")
    if v.startswith("V"):
        return v
    if v.startswith("v"):
        return "V" + v[1:]
    return "V" + v


def read_version(version_arg: Optional[str]) -> str:
    if version_arg:
        return format_version(version_arg)
    setup_path = Path(__file__).resolve().parent.parent / "setup.py"
    if not setup_path.exists():
        raise FileNotFoundError(f"未找到 setup.py: {setup_path}")
    content = setup_path.read_text(encoding="utf-8")
    match = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("无法从 setup.py 中解析 VERSION")
    return format_version(match.group(1))


def get_dist_files() -> List[Path]:
    dist_dir = Path(__file__).resolve().parent.parent / "dist"
    if not dist_dir.exists():
        raise FileNotFoundError(f"dist 目录不存在: {dist_dir}")
    files = [p for p in dist_dir.rglob("*") if p.is_file()]
    if not files:
        raise FileNotFoundError(f"dist 目录没有可上传的文件: {dist_dir}")
    return files


class GiteeClient:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict] = None,
        files: Optional[dict] = None,
        expect_404_ok: bool = False,
    ):
        url = f"{BASE_URL}{path}"
        params = {"access_token": self.token}
        headers = {"Authorization": f"token {self.token}"}
        resp = requests.request(method, url, params=params, json=json_body, files=files, headers=headers)
        if expect_404_ok and resp.status_code == 404:
            return None
        if not resp.ok:
            detail = resp.text
            raise RuntimeError(f"HTTP {resp.status_code} {resp.reason}: {detail}")
        if resp.status_code == 204:
            return None
        return resp.json()

    def get_release_by_tag(self, tag: str):
        path = f"/repos/{self.owner}/{self.repo}/releases/tags/{tag}"
        return self._request("GET", path, expect_404_ok=True)

    def delete_release(self, release_id: int):
        path = f"/repos/{self.owner}/{self.repo}/releases/{release_id}"
        self._request("DELETE", path)

    def delete_tag(self, tag: str):
        path = f"/repos/{self.owner}/{self.repo}/tags/{tag}"
        self._request("DELETE", path, expect_404_ok=True)

    def create_release(self, tag: str, target: str) -> int:
        body = f"""Ant Build Menu {tag} 发布

## 更新内容
- 新增功能
- 问题修复
- 性能优化

## 安装说明
1. 下载 installer.exe
2. 以管理员身份运行安装程序
3. 按照提示完成安装
4. 右键点击 build.xml 文件即可使用 Ant 构建功能
"""
        payload = {
            "tag_name": tag,
            "name": f"Release {tag}",
            "body": body,
            "target_commitish": target,
            "prerelease": False,
            "draft": False,
        }
        data = self._request("POST", f"/repos/{self.owner}/{self.repo}/releases", json_body=payload)
        return int(data["id"])

    def upload_assets(self, release_id: int, files: Iterable[Path]):
        path = f"/repos/{self.owner}/{self.repo}/releases/{release_id}/attach_files"
        for file_path in files:
            with file_path.open("rb") as fh:
                multipart = {"file": (file_path.name, fh, "application/octet-stream")}
                self._request("POST", path, files=multipart)
                print(f"上传完成: {file_path}")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="发布到 Gitee（覆盖同名发布并上传 dist 文件）")
    parser.add_argument("-v", "--version", help="版本号，可带或不带 V 前缀", dest="version")
    parser.add_argument("-t", "--token", help="Gitee Personal Access Token", dest="token")
    parser.add_argument("-o", "--owner", default="xskywalker", help="仓库所属用户或组织")
    parser.add_argument("-r", "--repo", default="ant-build-menu", help="仓库名")
    parser.add_argument(
        "--target",
        default="master",
        help="Release 指向的分支或提交（默认 master）",
    )
    args = parser.parse_args(argv)

    token = args.token or os.environ.get("GITEE_TOKEN")
    if not token:
        print("缺少 Token，请使用参数 --token 或设置环境变量 GITEE_TOKEN")
        return 1

    try:
        version_tag = read_version(args.version)
        files = get_dist_files()
    except Exception as exc:
        print(f"初始化失败: {exc}")
        return 1

    print(f"准备发布版本: {version_tag}")
    print(f"将上传 dist 下文件数量: {len(files)}")

    client = GiteeClient(token=token, owner=args.owner, repo=args.repo)
    try:
        existing = client.get_release_by_tag(version_tag)
        if existing and "id" in existing:
            print(f"删除已存在的 Release: {version_tag}")
            client.delete_release(existing["id"])
        print(f"删除已存在的 Tag: {version_tag}（若不存在将忽略）")
        client.delete_tag(version_tag)

        print(f"创建 Release: {version_tag} -> {args.target}")
        release_id = client.create_release(version_tag, target=args.target)
        print(f"Release 创建成功，ID: {release_id}")

        print("开始上传附件...")
        client.upload_assets(release_id, files)
        print("发布完成")
        print(f"Release 页面: https://gitee.com/{args.owner}/{args.repo}/releases")
        return 0
    except Exception as exc:
        print(f"发布失败: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
