# FictionOps 发布检查清单

> 目标：在发布前确认 CLI、模板、文档和包安装状态都能被当前证据证明，而不是只靠“应该没问题”。

## 1. 版本与变更

- `fictionops/src/fictionops/__init__.py` 里的 `__version__` 已更新。
- `fictionops/pyproject.toml` 里的 `version` 已同步。
- `CHANGELOG.md` 已记录新增、修复、破坏性变更和迁移提示。
- `docs/release-notes-0.1.0.zh-CN.md` 已记录验证命令、验证结果、已知边界和下一步。
- `docs/completion-audit-0.1.0.zh-CN.md` 已把 MVP 要求映射到当前证据。
- `docs/roadmap.zh-CN.md` 和 `docs/roadmap.md` 已记录下一阶段验收矩阵，且 release notes 与 completion audit 的下一步描述没有绕开它。
- `docs/compatibility.md` 和 `docs/compatibility.zh-CN.md` 已记录版本阶段、稳定面、兼容新增、破坏性变化和 controller 依赖规则；若命令、schema 或 JSON key 变化，发布前必须同步检查。
- `docs/known-limits.md` 和 `docs/known-limits.zh-CN.md` 已记录文学判断、模型行为、迁移、发布、安全和恢复边界。
- `docs/recovery.md` 和 `docs/recovery.zh-CN.md` 已记录常见损坏状态、诊断命令、安全重生成、迁移恢复、Agent 输出恢复、发布产物恢复和 controller 停止规则。
- `docs/dogfood-legacy-adopt.zh-CN.md` 已记录真实旧项目 adopt 扫描、误判修正和迁移建议。
- `docs/dogfood-cycle-evidence.md` / `docs/dogfood-cycle-evidence.zh-CN.md` 已提供 1.0 持续 dogfood 周期证据模板。
- `docs/stability-window-evidence.md` / `docs/stability-window-evidence.zh-CN.md` 已提供 1.0 稳定窗口证据模板。
- `examples/legacy_novel_source/` 已保留为可运行旧项目迁移样例，并有回归测试覆盖。
- `docs/pypi-release.zh-CN.md` 已记录 TestPyPI/PyPI 发布顺序、Trusted Publishing 凭据隔离和发布后回滚策略。
- `docs/cli-contracts.md`、`docs/compatibility.md`、`docs/agent-integration.md`、`docs/migration.md`、`docs/testing.md`、`docs/release.md`、`docs/known-limits.md` 和 `CONTRIBUTING.md` 已覆盖英文命令契约、兼容性、Agent 接入、迁移、测试、发布、已知限制和贡献入口。
- README 中的命令数量、命令名、安装方式仍然准确。

## 2. 模板与项目结构

- 根目录 `templates/` 与 `src/fictionops/templates/` 内容一致。
- 新增模板已加入 `pyproject.toml` 的 package data。
- `init` 生成的标准项目结构与 `docs/project-structure.zh-CN.md` 一致。
- 新增标准文件已纳入 continuity 检查，或明确说明为什么不纳入。
- `export-clean` 默认输出目录 `08_publish/clean_markdown/` 仍存在于项目结构中。
- `audit-publish` 能检查默认 clean Markdown，并能用 `--file` 检查指定文件。
- `publish-copy` 能从发布清单、故事种子、书纲和 clean Markdown 生成简介、标签、关键词草稿，并能用 JSON 输出供后续工具读取。
- `export-metadata` 默认输出目录 `08_publish/metadata/` 仍存在于项目结构中。
- `export-manifest` 默认输出目录 `08_publish/manifest/` 仍存在于项目结构中。
- `export-epub` 默认输出目录 `08_publish/epub/` 仍存在于项目结构中。
- `audit-epub` 能检查默认 EPUB，并能用 `--file` 检查指定 EPUB。
- `release-gate` 能聚合书级收束、发布稿、元数据、manifest 和 EPUB 准备状态，并能用 JSON 输出供后续工具读取。
- `adopt` 能只读扫描既有写作目录，输出分层迁移诊断、迁移阶段、建议目标路径和风险提示，且不会创建或修改源项目文件。
- `scan-words` 能输出通用高频词、短语和关注词命中，并能用 JSON 输出供后续工具读取。
- `check-tables` 能检查 Markdown 表格结构、占位行和行宽问题，并能用 JSON 输出供后续工具读取。
- `audit-wave` 能输出章节体量波形，并能用 JSON 输出供后续工具读取。
- `audit-info` 能检查信息释放表，并能用 JSON 输出供后续工具读取。
- `audit-characters` 能检查人物弧线、智慧模式、口吻资料和人物索引覆盖，并能用 JSON 输出供后续工具读取。
- `agent-prompt` 能生成角色提示词，并能用 JSON 输出供后续工具读取。
- `agent-run` 能生成 prepare-only Agent 任务包，写出 `request.json`、`prompt.md`、`context_pack.md` 和可选 `draft_brief.md`，不调用模型、不保存密钥、不覆盖正文。
- `agent-exec` 能把 Agent run 任务包交给外部 runner，把 stdout 写成暂存输出并生成 `execution.json`，不保存密钥、不自动应用输出、不覆盖正文；OpenAI Responses runner 示例可用 `--dry-run` 验证真实模型接入边界。
- `agent-inbox` 能检查 Agent run 目录中的回传输出，识别缺输出、空输出、多候选输出和坏 request，且不调用模型、不应用输出。
- `model-config` 能生成模型供应商配置 JSON，不保存真实密钥，也不调用模型。
- `doctor/report` 能纳入 scan-words 与 check-tables 摘要；表格结构问题会计入健康状态，普通正文没有表格不会单独推高状态。
- `doctor/report` 能纳入 book-gate 和 release-gate 的里程碑状态摘要，但不重复计入底层 issue counts。
- `doctor/report` 能纳入模型配置摘要，并把缺供应商、缺模型名、缺密钥环境变量或不安全 key 存储策略计入健康状态。
- `doctor/report` 能在存在 `00_management/agent_runs` 时纳入 Agent 输出收件箱摘要，并把多候选输出或坏 request 计入健康状态。
- `doctor/report` 能纳入人物弧线摘要，并把索引、弧线、智慧模式或口吻资料缺口计入健康状态。
- `context-pack` 能生成范围化上下文包；handoff 任务能纳入交接日志、决策记录、人物资料、正史表、doctor/report、revision-plan 和 book/release gate 里程碑产物；每文件和整包预算会限制内嵌内容，并能用 JSON 输出供后续工具读取。
- `workflow-plan` 能把 init、foundation、book-plan、chapter-prep、draft、review、book-retrospective、publish 和 handoff 阶段转成命令清单；review 阶段包含表格检查和词频扫描，并能用 JSON 输出供后续工具读取。
- `revision-plan` 能把审计问题转成修订任务，包括人物弧线维护、表格结构问题和词频新鲜度提示，并能用 JSON 输出供后续工具读取。
- `scene-plan` 能从章节发动机生成场景骨架，尊重已填写的场景顺序，并能用 JSON 输出供后续工具读取。
- `draft-brief` 能从场景骨架和范围化上下文生成写前任务单，并能用 JSON 输出供后续工具读取。
- `post-draft` 能检查单章草稿、发动机、逐章复盘和同步项是否关门，并能用 JSON 输出供后续工具读取。
- `review-gate` 能聚合单章写后、连续性、信息、人物、伏笔、风格和体量波形信号，并能用 JSON 输出供后续工具读取。
- `book-gate` 能聚合书级计划、复盘、修订、表格结构、词频提示和体量波形信号，并能用 JSON 输出供后续工具读取。

## 3. CLI 契约

- 每个新增命令都有核心函数测试。
- 每个新增命令都有 CLI 子进程测试。
- JSON 输出可被 `json.loads` 解析。
- Markdown 输出没有依赖绝对临时路径才能成立的断言。
- 默认不覆盖用户文件，除非显式传入 `--force`。
- `.github/workflows/fictionops-ci.yml` 会在 PR/push 中运行 compileall、unittest、wheel/sdist build、wheel/sdist 内容检查和 built-wheel clean venv smoke。
- `.github/workflows/fictionops-publish.yml` 只允许手动触发，先构建并检查 wheel/sdist，执行 built-wheel clean venv smoke，再通过 TestPyPI 或 PyPI environment 使用 Trusted Publishing 上传。

## 4. Smoke 测试

必须通过：

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -k adopt -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_smoke -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k workflow_plan -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k scene_plan -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k draft_brief -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k post_draft -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k review_gate -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k book_gate -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k scan_words -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k check_tables -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k installed_console -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k built_wheel_installs -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k export_clean -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k audit_publish -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k publish_copy -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k characters -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k export_metadata -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k export_manifest -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k export_epub -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k audit_epub -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_gate -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_evidence -v
python -m unittest discover -s fictionops/tests -p test_cli.py -k dogfood_cycle -v
```

这些测试分别证明：

- 用户从 `init` 到 `release-gate` 的快速开始链路能走通。
- 既有写作项目能先被只读诊断，不必在迁移前手动猜文件分层。
- 本地安装后，真正的 `fictionops` 入口能运行并找到随包模板。
- 从构建好的 wheel 安装到干净虚拟环境后，`fictionops`、`python -m fictionops`、`init`、`doctor`、`agent-connect --help`、`agent-smoke --help`、`agent-next --help`、`audit-agent-workflow --help`、`audit-stability-window --help` 和 `audit-stable-core --help` 可用。
- 静态原型层词频扫描和表格检查能输出 JSON。
- 发布层 clean Markdown 导出能写入目标文件且默认不覆盖。
- 发布层 clean Markdown 审计能发现缺文件、残留草稿标记、缺章和短章。
- 发布层文案助手能生成可编辑简介、标签和关键词草稿，且默认不覆盖。
- 发布层 metadata JSON 导出能发现缺元数据，并且默认不覆盖。
- 发布层 manifest 能记录 clean Markdown、metadata JSON 和可选封面的 hash，并且默认不覆盖。
- 发布层 EPUB 导出能生成包含 OPF、nav、CSS、章节 XHTML 和可选封面的 `.epub`，并且默认不覆盖。
- 发布层 EPUB 审计能发现坏 zip、缺结构和过期 EPUB。
- 发布层最终门禁能发现缺失、过期或结构损坏的发布物，并在准备完成时给出可发布状态。
- 包发布证据审计能区分空模板、未复核草稿和已填实外部记录，避免 0.4 被弱证据误关。
- 持续 dogfood 周期审计能区分空模板、延期记录、过短周期和已填实维护周期，避免 1.0 被弱证据误关。
- 稳定核心审计能聚合发布证据、dogfood 周期、至少 7 个自然日的稳定窗口和里程碑声明，避免 1.0 被局部证据误关。
- `doctor/report` 能在发布阶段启动后纳入 Publish、Metadata、Manifest 和 EPUB 区块。

## 5. 全量验证

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel --no-deps --no-build-isolation -w dist ./fictionops
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('../dist').mkdir(exist_ok=True); print(b.build_sdist('../dist'))"
```

构建 wheel 后检查：

- wheel 内包含 `fictionops/templates/project.yml`。
- wheel 内包含 `fictionops/templates/chapter_engine.zh-CN.md`。
- wheel 内包含 `fictionops/__main__.py`，安装后 `python -m fictionops --version`、`fictionops agent-connect --help`、`fictionops agent-smoke --help`、`fictionops agent-next --help`、`fictionops audit-agent-workflow --help`、`fictionops audit-stability-window --help` 和 `fictionops audit-stable-core --help` 可用。
- wheel 内包含 `fictionops/adopt.py`、`fictionops/adopt_review.py`、`fictionops/adopt_plan.py`、`fictionops/import_plan.py`、`fictionops/agent_connect.py`、`fictionops/agent_smoke.py`、`fictionops/agent_run.py`、`fictionops/agent_exec.py`、`fictionops/agent_inbox.py`、`fictionops/agent_next.py`、`fictionops/agent_workflow_audit.py`、`fictionops/scene_plan.py`、`fictionops/draft_brief.py`、`fictionops/post_draft.py`、`fictionops/review_gate.py`、`fictionops/book_gate.py`、`fictionops/word_scan.py`、`fictionops/table_check.py`、`fictionops/publish_copy.py`、`fictionops/release_gate.py`、`fictionops/release_evidence.py`、`fictionops/dogfood_cycle.py`、`fictionops/stability_window.py` 和 `fictionops/stable_core.py`。
- wheel 内包含许可证文件。

构建 sdist 后检查：

- sdist 内包含 `LICENSE`、`README.md`、`README.zh-CN.md`、`CHANGELOG.md`、`CONTRIBUTING.zh-CN.md`、`MANIFEST.in` 和 `pyproject.toml`。
- sdist 内包含 `src/fictionops/__main__.py`、`src/fictionops/cli.py`、`src/fictionops/agent_connect.py`、`src/fictionops/agent_smoke.py`、`src/fictionops/agent_run.py`、`src/fictionops/agent_exec.py`、`src/fictionops/agent_inbox.py`、`src/fictionops/agent_next.py`、`src/fictionops/agent_workflow_audit.py`、`src/fictionops/stability_window.py`、`src/fictionops/stable_core.py`、`src/fictionops/templates/project.yml` 和 `src/fictionops/templates/chapter_engine.zh-CN.md`。
- sdist 内包含根模板、中英文文档、英文 CLI 契约、Agent 接入指南、echo/OpenAI 示例 runner、示例 controller、示例项目、测试文件和 workflow 文档。

检查完成后删除本地生成物：

- `fictionops/build/`
- `fictionops/dist/`
- `fictionops/src/*.egg-info/`
- `__pycache__/`

## 6. 发布边界

发布前确认没有包含：

- 真实小说正文、私有大纲或未公开设定。
- 个人绝对路径。
- 临时构建产物。
- 需要联网才能通过的核心测试。

## 7. PyPI 发布自动化

- 先在 GitHub Actions 手动触发 `FictionOps Publish`，`target` 选择 `testpypi`。
- workflow 输入的 `version` 必须与 `fictionops/pyproject.toml` 一致。
- `build` job 只能读取仓库内容，不能获得 PyPI 发布身份。
- `publish-testpypi` 和 `publish-pypi` job 只能通过对应 GitHub environment 获取 OIDC trusted publishing 身份，不使用仓库 secret 保存 token。
- TestPyPI 安装烟测通过后，才能触发 `target=pypi`。
- PyPI 发布或事故处理必须同步记录到 `CHANGELOG.md`、release notes 和 completion audit。

## 8. 发布后

- 给 release 打 tag。
- 把本次验证命令和结果写入 release notes；若验证命令重新运行，应同步更新 release notes 和 completion audit。
- 如果发现发布后问题，优先补回归测试，再修复代码。
## 追加发布检查：迁移沙盒

- `adopt --copy-to <project>` 已验证只能写入带 `project.yml` 的已初始化 FictionOps 项目。
- 目标项目不能位于被扫描的旧目录内部。
- 已有目标文件默认跳过，`--force` 才覆盖。
- `--dry-run` 不写入复制目标。
- 实际复制后应写出 `00_management/adopted_handoff/adopt_manifest.json`。
- JSON 输出包含复制摘要和复制明细，且不会混入人类状态提示。

## 追加发布检查：迁移后复查

- `adopt-review <project>` 已验证会聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`。
- 迁移沙盒中仍有 `06_drafts/import_queue/` 文件时，状态应为 `needs_import_sorting`。
- JSON 输出包含 `checks`、`issues`、`doctor` 和 `book_gate`，且不会混入人类状态提示。
- Markdown 报告默认不覆盖，`--force` 才覆盖。
- wheel 内容检查应包含 `fictionops/adopt_review.py`。
## 追加发布检查：迁移整改计划

- `adopt-plan <project>` 已验证会复用 `adopt-review` 的结论，并把迁移复查问题转成优先级任务。
- `06_drafts/import_queue/` 中仍有导入正文时，任务中必须包含 `import_queue_unsorted`。
- JSON 输出包含 `review_status`、`priority_counts`、`task_groups`、`group_output_dir`、`group_files_written`、`group_files`、`tasks` 和 `adopt_review`，且不混入人读提示。
- `--write-groups` 已验证会写出修复组 `index.md` 和逐组 Markdown 工作文件，默认不覆盖，`--force` 才能覆盖。
- Markdown 计划默认不覆盖，`--force` 才能覆盖，并在逐条任务前输出 `Repair Groups`。

## 追加发布检查：导入队列整理计划

- `import-plan <project>` 已验证会读取 `06_drafts/import_queue/` 并给出逐文件目标建议。
- 存在 `00_management/adopted_handoff/adopt_manifest.json` 时，`import-plan` 应利用旧源路径辅助推断书号。
- 章号缺失、目标已存在或目标重复的文件必须保留为人工复查，不得被 `--apply` 自动移动。
- `--apply` 只移动无歧义、目标不存在的文件。
- `--apply --create-scaffolds` 应为已移动章节补齐缺失的章节发动机和逐章复盘，且不覆盖已有文件。
- `--apply --replace-placeholder-targets` 只应替换仍像生成模板的占位章节目标，真实已有正文必须保留为人工复查。
- JSON 输出包含 `import_queue_files`、`ready_count`、`needs_review_count`、`moved_files`、`replaced_placeholder_targets`、`scaffold_created_files` 和逐文件 `items`，且不混入人读提示。
- Markdown 计划默认不覆盖，`--force` 才能覆盖。
- wheel 内容检查应包含 `fictionops/import_plan.py`。
- wheel 内容检查应包含 `fictionops/adopt_plan.py`。

## 追加发布检查：迁移复制同名消歧

- 同一轮 `adopt --copy-to` 中多个源文件映射到同一建议目标路径时，必须生成唯一目标路径。
- 真实示例长篇迁移沙盒复跑中，5 个同名目标已自动消歧，复制结果为 169 copied / 0 skipped。
- 回归测试 `test_adopt_copy_disambiguates_same_target_paths` 必须通过。

## 追加发布检查：可运行迁移示例

- `examples/legacy_novel_source/` 不是标准 FictionOps 项目，用于模拟旧写作目录。
- 回归测试 `test_legacy_migration_example_runs_sandbox_workflow` 必须通过。
- 该测试应证明 `adopt-review` 先进入 `needs_import_sorting`，`import-plan --apply --create-scaffolds --replace-placeholder-targets` 后导入队列清空，并进入 `needs_migration_fixes`。
