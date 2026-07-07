# FictionOps PyPI 发布说明

> 目标：让正式上传可以被审计、可回放、可暂停，并且不在仓库、日志或配置文件中保存任何真实发布 token。

## 1. 发布边界

FictionOps 的 PyPI 发布流程只负责发布 CLI 包本身，不发布任何真实小说正文、私有大纲或作者项目。

发布工作流位于 `.github/workflows/fictionops-publish.yml`，只能手动触发：

```text
workflow_dispatch
```

触发时必须输入：

- `target`：`testpypi` 或 `pypi`。
- `version`：期望发布的版本号，例如 `0.1.0`。

工作流会读取 `fictionops/pyproject.toml` 的版本号；如果输入版本与包内版本不一致，构建会失败，不会进入上传阶段。

## 2. 凭据隔离

发布流程使用 PyPI Trusted Publishing / OIDC，不在仓库中保存 API token。

需要在 PyPI 或 TestPyPI 后台配置 Trusted Publisher，绑定：

- GitHub owner / repository；
- workflow 文件：`.github/workflows/fictionops-publish.yml`；
- environment：`testpypi` 或 `pypi`；
- package name：`fictionops`。

GitHub Actions 中只有发布 job 拥有：

```yaml
permissions:
  id-token: write
  contents: read
```

构建 job 只有 `contents: read`。这意味着测试、构建、wheel/sdist 内容检查都不能获得发布身份；只有用户手动选择目标后，对应 environment 的发布 job 才能向 PyPI 申请临时 OIDC 凭据。

## 3. 发布顺序

建议顺序：

1. 在本地运行 `docs/release-checklist.zh-CN.md` 中的全量验证。
2. 确认 `docs/release-notes-0.1.0.zh-CN.md` 和 `docs/completion-audit-0.1.0.zh-CN.md` 已更新。
3. 在 GitHub Actions 手动触发 `FictionOps Publish`，`target` 选择 `testpypi`。
4. 下载 `fictionops-release-trial-evidence-<version>` artifact；它是 workflow 自动生成的 release trial evidence draft，和 `fictionops-dist-<version>` 分开发放，避免证据文件混入 PyPI/TestPyPI 发布目录。
5. 从 TestPyPI 安装测试包，确认 `fictionops --version`、`python -m fictionops --version`、`fictionops init`、`fictionops agent-connect --help`、`fictionops agent-smoke --help`、`fictionops agent-exec --help`、`fictionops agent-next --help`、`fictionops audit-agent-workflow --help`、`fictionops audit-stability-window --help`、`fictionops audit-stable-core --help` 可用。
6. 按 `docs/release-trial-evidence.zh-CN.md` 补全 GitHub Actions run URL、artifact、TestPyPI URL、安装烟测和 `accepted/deferred/failed` 结论。
7. 运行 `fictionops audit-release-evidence . --file <filled-evidence.md>`；只有返回 `ready=yes` / `ready=true` 时，才把 0.4 视为可关闭。
5. 给代码打 release tag，并记录本次构建产物名称和测试结果。
6. 再次手动触发 `FictionOps Publish`，`target` 选择 `pypi`。

不建议直接跳过 TestPyPI。即使本地 wheel 安装烟测通过，TestPyPI 仍然能暴露包名、元数据、README 渲染和 Trusted Publishing 绑定问题。

## 4. 回滚与事故处理

PyPI 已发布的版本号不能覆盖。发现问题时不要重新上传同版本文件。

处理顺序：

1. 判断问题是否影响安装、命令入口、模板加载、发布包内容或用户数据安全。
2. 如果版本严重错误，先在 PyPI 后台 yank 对应 release，并在 GitHub release notes 中标记原因。
3. 立刻补回归测试，确认问题可复现。
4. 发布补丁版本，例如 `0.1.1`。
5. 在 `CHANGELOG.md`、release notes 和 completion audit 中记录：
   - 出问题的版本；
   - yank 或保留的决定；
   - 修复版本；
   - 新增的回归测试。

如果问题只影响文档，不影响包安装与 CLI 契约，可以保留版本并在下一版修复；但仍应记录在 `CHANGELOG.md`。

## 5. 本地发布前自检

从仓库根目录运行：

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

然后检查：

- `fictionops/dist/fictionops-<version>-py3-none-any.whl` 存在。
- `fictionops/dist/fictionops-<version>.tar.gz` 存在。
- wheel 包含 CLI 模块、Agent 模块和随包模板。
- sdist 包含源码、中英文文档、示例项目、测试和 workflow 文档。
- 本地安装 wheel 后，`fictionops --version` 和 `python -m fictionops --version` 都与 `pyproject.toml` 一致。

完成检查后可以清理本地产物；GitHub 发布工作流会重新构建，不依赖本地 `dist/`。
