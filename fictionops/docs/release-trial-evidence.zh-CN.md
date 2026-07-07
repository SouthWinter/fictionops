# 发布演练证据

这份文件用于记录 0.4 发布演练里程碑的外部证据。它是模板和账本，不是证据本身。

本地测试、本地 wheel/sdist 构建、本地干净虚拟环境安装烟测都只是发布前置证据。0.4 真正关闭时，必须记录真实 GitHub Actions run URL；如果使用 TestPyPI，还要记录 TestPyPI 项目或版本 URL，以及从 TestPyPI 安装后的烟测结果。

## 证据规则

- 只把本地 checkout 之外真实存在的记录当作外部证据。
- 本地命令输出只能作为 preflight，不替代 GitHub Actions 或 TestPyPI 记录。
- 如果跳过 TestPyPI，需要记录原因和接受这个决定的人。
- 发布演练只有在外部 artifact 或 TestPyPI 包安装烟测通过后，才能标记为 accepted。
- `Built-wheel smoke result`、`fictionops init smoke result` 和 `fictionops doctor smoke result` 必须明确显示通过，才能标记为 accepted。
- `not passed`、`failed`、`unsuccessful` 等否定结果，或只是包含 `pass` 字符串的无关词，不能当作烟测通过证据。
- `Date` 必须使用 `YYYY-MM-DD` 或 `YYYY-MM-DDTHH:MM:SSZ`；如果本地存在 `pyproject.toml`，`Version` 必须与项目版本一致，两个版本烟测结果也必须包含该版本号。
- `GitHub Actions run URL` 必须使用 `https://github.com/<owner>/<repo>/actions/runs/<run-id>`，且 `GitHub Actions run ID` 必须与 URL 中的正整数 run id 一致。
- 使用 TestPyPI 时，`TestPyPI project URL` 和 `TestPyPI version URL` 必须使用 `https://test.pypi.org/project/...`。
- wheel 文件名必须以 `.whl` 结尾，sdist 文件名必须以 `.tar.gz` 结尾。
- 发布演练不能在缺少具名复核人时标记为 accepted。
- 演练完成后，同步更新 release notes、milestone status 和 release/tag 说明。

## 外部证据模板

可以把下面这一段复制到 release notes，也可以在发布记录旁保存一份填好的副本。

```markdown
## 发布演练证据

- 日期：
- 版本：
- Commit / ref / tag：
- 结论：accepted / deferred / failed
- 复核人：

### GitHub Actions

- Workflow 名称：
- Workflow 文件：
- GitHub Actions run URL：
- GitHub Actions run ID：
- Runner OS / Python matrix：
- build job 状态：
- test job 状态：
- publish job 状态：
- artifact 名称：
- artifact 下载 URL：
- artifact 保留说明：

### 分发包

- wheel 文件名：
- wheel SHA256：
- sdist 文件名：
- sdist SHA256：
- built-wheel smoke 结果：
- sdist 内容检查结果：

### TestPyPI

- 是否使用 TestPyPI：yes / no
- TestPyPI project URL：
- TestPyPI version URL：
- TestPyPI skip reason：
- TestPyPI skip accepted by：
- Trusted Publishing environment：
- 发布结果：
- 干净 venv 安装命令：
- `fictionops --version` 结果：
- `python -m fictionops --version` 结果：
- `fictionops init` 烟测结果：
- `fictionops doctor` 烟测结果：
- 回滚 / 清理记录：

### 备注

- 已知问题：
- 后续动作：
- 豁免记录：
```

## 采集命令

使用干净 shell 和临时目录。

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

如果验证 GitHub Actions artifact 而不是 TestPyPI，先把 workflow artifact 下载到干净目录，再直接安装 wheel：

```bash
python -m venv .venv-release-trial
. .venv-release-trial/bin/activate
python -m pip install --upgrade pip
python -m pip install --no-deps dist/fictionops-*.whl
fictionops --version
python -m fictionops --version
smoke_dir="$(mktemp -d)"
fictionops init "$smoke_dir/release-trial-smoke" --title "Release Trial Smoke"
fictionops doctor "$smoke_dir/release-trial-smoke" --format json
```

Windows PowerShell 可以使用：

```powershell
python -m venv .venv-release-trial
.\.venv-release-trial\Scripts\Activate.ps1
python -m pip install --upgrade pip
$smokeDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ("fictionops-release-trial-" + [guid]::NewGuid()))
fictionops init (Join-Path $smokeDir "release-trial-smoke") --title "Release Trial Smoke"
fictionops doctor (Join-Path $smokeDir "release-trial-smoke") --format json
```

## Workflow-generated draft

`.github/workflows/fictionops-publish.yml` will upload a separate `fictionops-release-trial-evidence-<version>` artifact. The draft records the GitHub Actions run URL, run ID, distribution artifact name, wheel SHA256, and sdist SHA256. Keep this evidence artifact separate from `fictionops-dist-<version>` so PyPI/TestPyPI publish jobs receive only the wheel and sdist files.

The generated draft is not the final acceptance record by itself. After the external run, fill in reviewer, publish result, TestPyPI/PyPI URLs, install smoke output, rollback notes, and the final `accepted/deferred/failed` decision.

Before closing 0.4, run `fictionops audit-release-evidence . --file <filled-evidence.md>`. A template, a deferred record, or an unreviewed workflow draft must not close the release-trial milestone.

## 验收结论

紧凑写法是 `accepted/deferred/failed`。

- `accepted`：外部 workflow 已运行，artifact 已生成，安装烟测通过，release notes 已链接 run。
- `deferred`：仓库侧已准备好，但 GitHub Actions、TestPyPI 或发布时间导致暂缓。
- `failed`：外部证据显示真实问题，需要修复、补测试并重新演练。
