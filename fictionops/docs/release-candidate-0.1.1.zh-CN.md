# FictionOps 0.1.1 发布候选计划

这份计划的目的，是避免把旧的 `0.1.0` TestPyPI 证据误当成当前 `main` 的精确发布证据。

`0.1.0` 的 TestPyPI 记录依然有价值：它证明过 publish workflow、Trusted Publishing、TestPyPI 安装和烟测链路能跑通。但它对应的是较早 commit。此后我们又补了 GitHub 首页、包 README、模型供应商文档、OpenAI-compatible Chat runner、推广准备包、引用文件、包元数据和 sdist 内容检查。

## 当前判断

不要把当前 `main` 直接作为 `0.1.0` 发到正式 PyPI。

建议下一个公开包版本是：

```text
0.1.1
```

原因：

- TestPyPI / PyPI 同一版本文件不可覆盖。
- `fictionops==0.1.0` 已经在 TestPyPI 上由较早 commit 发布过。
- 当前 `main` 的包内容已经和那次 TestPyPI 产物不同。
- 正式 PyPI 发布前，应该让 TestPyPI 证据对应同一个版本、同一个 commit、同一批 artifact。

## 哪些内容继续保留 0.1.0

以下内容是历史里程碑证据，不需要因为下一个包版本是 `0.1.1` 就改名：

- `docs/release-notes-0.1.0.zh-CN.md`
- `docs/completion-audit-0.1.0.zh-CN.md`
- `docs/release-trial-evidence.md` 中 GitHub Actions run `28837872185` 的 accepted 记录
- roadmap 和 milestone 里关于 0.1.0 pre-alpha MVP 的描述

## 0.1.1 范围

`0.1.1` 应该是包装和上手体验 patch release，不要宣称新的功能里程碑。

范围包括：

- GitHub 根目录 README 和 quickstart 终端预览；
- 根目录 `LICENSE` 和 `CITATION.cff`；
- GitHub topics 和 description；
- OpenAI-compatible Chat Completions runner 示例与模型供应商文档；
- promotion kit 和 quickstart feedback issue 模板；
- 包元数据 URLs / keywords；
- workflow 对新增文档、资产和示例的 sdist 检查。

## 需要改的版本位置

切 `0.1.1` 候选时，需要同步：

- `fictionops/pyproject.toml`
- `fictionops/src/fictionops/__init__.py`
- `fictionops/src/fictionops/cli.py` 里的 fallback `__version__`
- `CITATION.cff`
- CI 和测试中硬编码的包版本检查
- 描述包 artifact 版本的候选说明或 release notes

`0.1.0` 的里程碑证据保留为历史证据。

## TestPyPI 顺序

1. 把包版本 bump 到 `0.1.1`。
2. 本地预检：

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

3. 推送到 `main` 并等待 CI 通过。
4. 手动触发 GitHub Actions `FictionOps Publish`：

```text
target = testpypi
version = 0.1.1
```

5. 下载 `fictionops-release-trial-evidence-0.1.1` artifact。
6. 在干净环境从 TestPyPI 安装：

```bash
python -m venv .venv-release-trial
. .venv-release-trial/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps fictionops==0.1.1
fictionops --version
python -m fictionops --version
smoke_dir="$(mktemp -d)"
fictionops init "$smoke_dir/release-trial-smoke" --title "Release Trial Smoke"
fictionops doctor "$smoke_dir/release-trial-smoke" --format json
```

7. 填写经过复核的 0.1.1 release evidence，并运行：

```bash
fictionops audit-release-evidence . --file <filled-0.1.1-evidence.md> --format json
```

8. 只有当 0.1.1 TestPyPI 证据 accepted 后，才触发：

```text
target = pypi
version = 0.1.1
```

## GitHub Release

建议 tag：

```text
v0.1.1
```

建议标题：

```text
FictionOps 0.1.1: pre-alpha packaging and onboarding release
```

Release notes 应说明：

- `0.1.0` 证明了 MVP 和 TestPyPI 链路；
- `0.1.1` 是补齐 GitHub 首页、模型供应商文档、引用信息和上手体验之后，推荐对外使用的第一个公开包候选；
- 项目仍然是 pre-alpha。

