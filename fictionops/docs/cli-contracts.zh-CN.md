# FictionOps CLI 契约

> 这份文档定义 CLI 的稳定承诺。`docs/cli.zh-CN.md` 负责教用户怎么用；本文件负责告诉开发者和 Agent：哪些行为不能轻易改。

## 1. 通用契约

所有命令遵循这些规则：

- 成功时退出码为 `0`。
- 失败时退出码为非零，错误信息写入 `stderr`，格式以 `fictionops: <command> failed:` 开头。
- 默认不覆盖用户已有文件；只有明确提供 `--force` 的命令才能覆盖生成文件或输出报告。
- 所有文本文件使用 UTF-8 写入。
- JSON 输出必须能被 Python 标准库 `json.loads` 解析。
- Markdown 输出面向人读，字段顺序可以随可读性调整；JSON 字段更稳定，适合后续 Agent 或脚本读取。
- 路径参数可以是相对路径；写入报告时，相对 `--out` 默认解析到目标项目内部。
- 审计命令只报告维护风险，不判断小说质量。

## 2. 命令总览

| 命令 | 类型 | 写文件 | JSON | 默认覆盖 |
| --- | --- | --- | --- | --- |
| `agent` | 统一有状态 Agent 入口 | 可选 | 是 | 否 |
| `adopt` | 旧项目接入诊断 | 可选 | 是 | 否 |
| `init` | 项目脚手架 | 是 | 否 | 否 |
| `new-book` | 书级脚手架 | 是 | 否 | 否 |
| `new-chapter` | 章节脚手架 | 是 | 否 | 否 |
| `plan-chapter` | 同步章节发动机 | 是 | 否 | 否 |
| `scene-plan` | 场景骨架生成 | 可选 | 是 | 否 |
| `draft-brief` | 写前任务单 | 可选 | 是 | 否 |
| `post-draft` | 写后关门检查 | 可选 | 是 | 否 |
| `review-gate` | 单章审稿门禁 | 可选 | 是 | 否 |
| `book-gate` | 书级收束门禁 | 可选 | 是 | 否 |
| `audit-plan` | 计划审计 | 否 | 是 | 不适用 |
| `retrospective` | 写后复盘汇总 | 可选 | 是 | 否 |
| `stats` | 字数统计 | 否 | 是 | 不适用 |
| `scan-words` | 通用词频扫描 | 否 | 是 | 不适用 |
| `check-tables` | 通用表格检查 | 否 | 是 | 不适用 |
| `audit-wave` | 章节体量波形审计 | 否 | 是 | 不适用 |
| `audit-style` | 风格模式审计 | 否 | 是 | 不适用 |
| `review-workflow` | 章节审读 workflow 编排 | 可选 | 是 | 否 |
| `audit-continuity` | 连续性维护审计 | 否 | 是 | 不适用 |
| `audit-echoes` | 伏笔回声审计 | 否 | 是 | 不适用 |
| `audit-info` | 信息边界审计 | 否 | 是 | 不适用 |
| `audit-characters` | 人物弧线审计 | 否 | 是 | 不适用 |
| `agent-prompt` | Agent 角色提示词 | 可选 | 是 | 否 |
| `agent-connect` | Agent 接入套件 | 是 | 是 | 否 |
| `eval-agent` | Agent harness 评估 | 可选 | 是 | 否 |
| `agent-smoke` | Agent 接入烟测 | 是 | 是 | 是 |
| `agent-run` | Agent 任务包 | 可选 | 是 | 否 |
| `agent-exec` | Agent 外部执行桥 | 否 | 是 | 是 |
| `agent-inbox` | Agent 输出收件箱 | 否 | 是 | 不适用 |
| `agent-revise-workflow` | Agent 审读驱动修订 workflow | 可选 | 是 | 否 |
| `agent-write-workflow` | 新章规划、写作、验证闭环 | 可选 | 是 | 否 |
| `agent-accept-revision` | 已验证候选显式采纳 | 是 | 是 | 否 |
| `write-chapter` | AI-first 章节写作编排 | 可选 | 是 | 否 |
| `revise-chapter` | AI-first 章节修订编排 | 可选 | 是 | 否 |
| `audit-chapter` | AI-first 章节审计编排 | 可选 | 是 | 否 |
| `agent-session` | AI 写作 session 台账 | 是 | 是 | 否 |
| `agent-next` | Agent 下一步选择器 | 否 | 是 | 不适用 |
| `audit-agent-workflow` | Agent workflow 接入预检 | 否 | 是 | 不适用 |
| `setup-ai` | AI 供应商引导配置 | 是 | 是 | 否 |
| `model-config` | 模型供应商配置 | 可选 | 是 | 否 |
| `context-pack` | 范围化上下文包 | 可选 | 是 | 否 |
| `workflow-plan` | 分阶段工作流清单 | 可选 | 是 | 否 |
| `revision-plan` | 审计到修订计划 | 可选 | 是 | 否 |
| `doctor` | 项目健康总览 | 否 | 是 | 不适用 |
| `report` | 健康报告导出 | 可选 | 是 | 否 |
| `export-clean` | 发布稿 Markdown 导出 | 是 | 是 | 否 |
| `audit-publish` | 发布稿维护审计 | 否 | 是 | 不适用 |
| `publish-copy` | 发布文案助手 | 是 | 是 | 否 |
| `export-metadata` | 发布元数据导出 | 是 | 是 | 否 |
| `export-manifest` | 发布包清单导出 | 是 | 是 | 否 |
| `export-epub` | EPUB 导出 | 是 | 是 | 否 |
| `audit-epub` | EPUB 包审计 | 否 | 是 | 不适用 |
| `release-gate` | 最终发布门禁 | 可选 | 是 | 否 |
| `audit-release-evidence` | 包发布证据审计 | 否 | 是 | 不适用 |
| `audit-dogfood-cycle` | 持续 dogfood 周期审计 | 否 | 是 | 不适用 |
| `audit-stability-window` | 稳定窗口证据审计 | 否 | 是 | 不适用 |
| `audit-stable-core` | 稳定核心聚合审计 | 否 | 是 | 不适用 |

## 3. 写入类命令

### `fictionops adopt`

输入：

- `path`：要扫描的既有写作目录，默认当前目录。
- `--max-files`：候选文件明细最多列出多少个；汇总仍统计全部扫描文件，默认 `80`。
- `--include-ignored`：包含默认忽略的 `.git`、`.github`、`fictionops`、`build`、`dist` 等目录。
- `--out`：写入 Markdown 诊断报告；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 只读扫描 `.md`、`.txt`、`.yml`、`.yaml` 和 `.json` 文件。
- 将候选文件映射为 `management`、`story_seed`、`world`、`characters`、`structure`、`canon`、`drafts`、`audits`、`publish`、`archive` 或 `unknown`。
- 为每个候选文件输出 `migration_phase` 和 `suggested_target_path`，用于人工迁移时参考。
- 输出分层文件数、非空白字数、候选文件列表、建议目标路径、迁移风险和下一步建议。
- 默认忽略已有 `fictionops/`、构建产物、依赖目录和版本控制目录，避免把工具自身或旧构建物当成长篇材料。
- 不创建 FictionOps 项目，不搬移文件，不改写旧项目内容。

失败：

- 输入路径不存在或不是目录。
- `--max-files` 小于 `0`。
- `--out` 已存在且未传 `--force`。

### `fictionops init`

输入：

- `path`：目标项目目录。
- `--title`：项目标题，默认使用目标目录名。
- `--language`：项目语言，默认 `zh-CN`。
- `--dry-run`：只显示计划动作。
- `--force`：覆盖生成文件。

输出：

- 创建标准 FictionOps 目录结构。
- 创建 `project.yml`、故事种子、人物、世界、结构、正史、审计、发布等初始文件。
- 创建 `06_drafts/book_01/chapters/ch_001.md` 和对应章节发动机。

失败：

- 模板目录或模板文件不存在。
- 目标路径无法创建或写入。

### `fictionops new-book`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，支持 `2`、`02`、`book_02`、`book-02`。
- `--title`：书名。
- `--dry-run`：只显示计划动作。
- `--force`：覆盖生成的书纲和书级复盘。

输出：

- `04_structure/book_outlines/<book>_outline.md`
- `06_drafts/<book>/chapters/`
- `06_drafts/<book>/chapter_engines/`
- `06_drafts/<book>/draft_briefs/`
- `06_drafts/<book>/revision_notes/`
- `07_audits/book_retrospectives/<book>_retrospective.md`

失败：

- 目标路径不存在或不是目录。
- 书号无法规范化。
- 书纲或复盘模板不存在。

### `fictionops new-chapter`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书稿目录，默认 `book_01`。
- `--chapter`：章节号，支持 `1`、`001`、`ch_001`、`第1章`。
- `--title`、`--viewpoint`、`--kind`、`--target-chars`：写入章节发动机的初始信息。
- `--dry-run`：只显示计划动作。
- `--force`：覆盖生成的正文、发动机和复盘。

输出：

- `06_drafts/<book>/chapters/ch_<chapter>.md`
- `06_drafts/<book>/chapter_engines/ch_<chapter>_engine.md`
- `06_drafts/<book>/revision_notes/ch_<chapter>_retrospective.md`

失败：

- 目标路径不存在或不是目录。
- 章节号无法规范化。
- 章节发动机或复盘模板不存在。

### `fictionops plan-chapter`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--chapter`：要同步的章节号。
- `--outline`：指定书纲路径；相对路径解析到 `path` 内部。
- `--dry-run`：显示会更新哪些字段，不写文件。
- `--force`：覆盖章节发动机中的非空字段。

输出：

- 更新对应章节发动机的标题、视角、性质、体量、压力链字段。
- 默认只填空字段，不覆盖已经手写的字段。

失败：

- 目标路径不存在或不是目录。
- 书纲不存在。
- 书纲中找不到对应章节行。
- 对应章节发动机不存在。

### `fictionops scene-plan`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--chapter`：要读取的章节号。
- `--engine`：指定章节发动机路径；相对路径解析到 `path` 内部。
- `--out`：写入场景计划路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 读取章节发动机中的标题、视角、性质、目标字数和五列发动机。
- 汇总连续性、信息边界、伏笔回声、留白要求和风格提醒。
- 如果“场景顺序”已经填写，按作者填写内容输出；如果为空，按五列发动机生成默认五段场景骨架。
- 对缺失五列发动机字段输出 `missing_engine_field`；自动生成场景顺序时输出 `generated_scene_order`。
- 不调用模型，不写正文，只把章节发动机转为写前可执行的场景层计划。

失败：

- 目标路径不存在或不是目录。
- 对应章节发动机不存在。
- `--out` 已存在且未传 `--force`。

### `fictionops draft-brief`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--chapter`：要准备写作的章节号。
- `--engine`：指定章节发动机路径；相对路径解析到 `path` 内部。
- `--include-context-content`：把范围化上下文文件内容嵌入 brief。
- `--max-chars-per-file`：每个上下文文件最多嵌入多少字符，默认 `6000`。
- `--max-total-chars`：全部上下文文件合计最多嵌入多少字符，默认 `60000`。
- `--out`：写入写前任务单路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 组合 `scene-plan` 的场景任务、信息边界、伏笔回声和留白要求。
- 组合 `context-pack --task draft` 的上下文文件清单、缺失必读材料和可选嵌入内容。
- 输出写前检查、必须做、禁止做、逐场景写作目标、上下文文件表和问题列表。
- 对场景发动机缺口和必需上下文缺口分别保留来源，供后续 Agent 或脚本判断阻断项。
- 不调用模型，不写正文，只生成可交给人类作者或写作 Agent 的任务单。

失败：

- 目标路径不存在或不是目录。
- 对应章节发动机不存在。
- `--out` 已存在且未传 `--force`。

### `fictionops post-draft`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--chapter`：要检查的章节号。
- `--min-chapter-chars`：章节非空白字符低于该值时视为占位，默认 `200`。
- `--out`：写入写后关门报告路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 检查单章正文、章节发动机、逐章复盘是否存在、是否仍像模板或占位。
- 统计章节字符、非空白字符、CJK 字符和复盘中的实际字数。
- 提取逐章复盘里的同步项，状态可为 `needs_draft`、`needs_engine`、`needs_retrospective`、`sync_needed` 或 `ready_for_review`。
- 输出下一步动作，避免写后发现只留在聊天记录或作者记忆里。
- 不调用模型，不改正文，不自动同步正史。

失败：

- 目标路径不存在或不是目录。
- `--out` 已存在且未传 `--force`。

### `fictionops review-gate`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--chapter`：要聚合检查的章节号。
- `--min-chapter-chars`：传给写后关门和连续性检查，默认 `200`。
- `--pattern`：传给底层 Markdown 审计，默认 `**/*.md`。
- `--out`：写入单章审稿门禁报告路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 聚合 `post-draft`、`audit-continuity`、`audit-info`、`audit-characters`、`audit-echoes`、`audit-style` 和 `audit-wave` 的单章相关信号。
- 输出每类检查的状态、问题数、阻塞问题数和摘要。
- 状态可为 `needs_post_draft`、`needs_review_fixes`、`review_notes` 或 `review_passed`。
- 输出下一步动作，用于判断该章应先补写后记忆、修阻塞问题，还是进入定向修订/润色。
- 不调用模型，不改正文，不替代底层详细审计报告。

失败：

- 目标路径不存在或不是目录。
- `--out` 已存在且未传 `--force`。

### `fictionops book-gate`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--outline`：指定书纲路径。
- `--min-chapter-chars`：传给底层审计，默认 `200`。
- `--pattern`：传给底层 Markdown 审计，默认 `**/*.md`。
- `--out`：写入书级收束门禁报告路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 聚合 `audit-plan`、`retrospective`、`revision-plan`、`check-tables`、`scan-words` 和 `audit-wave` 的书级收束信号。
- 输出计划覆盖、复盘闭合、修订阻塞项、表格结构、词频提示和章节体量波形的检查摘要。
- 状态可为 `needs_book_material`、`needs_book_closure`、`book_notes` 或 `ready_for_clean_export`。
- 将缺书纲、无计划章节、无正文、计划章节无正文/发动机、发动机未同步、书/章复盘未闭合、复盘同步项未处理视为书级收束阻塞。
- 不调用模型，不改正文，不导出 clean Markdown，不替代底层详细审计。

失败：

- 目标路径不存在或不是目录。
- `--out` 已存在且未传 `--force`。

## 4. 审计类命令

### `fictionops audit-plan`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--outline`：指定书纲路径。
- `--format table|json`：默认 `table`。

输出：

- 计划章节数、正文文件数、发动机文件数、已同步发动机数。
- 每个计划章节的正文/发动机覆盖情况。
- 缺正文、缺发动机、发动机未同步、正文未规划等问题。

失败：

- 目标路径不存在或不是目录。
- 书纲不存在。

### `fictionops retrospective`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--format markdown|json`：默认 `markdown`。
- `--out`：写入报告路径。
- `--force`：覆盖已有输出报告。

输出：

- 书级复盘是否存在、是否仍像模板。
- 正文章数、逐章复盘数、缺失复盘数、占位复盘数。
- 逐章复盘中的待同步项。

失败：

- 目标路径不存在或不是目录。
- `--out` 已存在且未传 `--force`。

### `fictionops stats`

输入：

- `path`：目标文件或目录，默认当前目录。
- `--all`：统计所有 Markdown。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--metric nonspace|cjk|chars`：默认 `nonspace`。
- `--format table|json`：默认 `table`。

输出：

- 文件数、总字数、平均字数。
- 每个文件的字数和体量分档。
- 默认只统计章节文件，不把章节发动机当正文。

失败：

- 目标路径不存在。

### `fictionops scan-words`

输入：

- `path`：目标文件或目录，默认当前目录。
- `--all`：扫描所有 Markdown。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--watch`：逗号分隔的关注词，会精确计数。
- `--min-count`：高频词最低出现次数，默认 `2`。
- `--top`：最大输出数量，默认 `20`。
- `--format table|json`：默认 `table`。

输出：

- 文件数、总英文单词数、总短语计数。
- 聚合高频词/短语。
- 关注词命中。
- 每个文件的高频词和关注词命中。
- 默认只扫描章节文件，不把章节发动机当正文。

失败：

- 目标路径不存在。
- `--min-count` 或 `--top` 小于 `1`。

### `fictionops check-tables`

输入：

- `path`：目标文件或目录，默认当前目录。
- `--all`：检查所有 Markdown。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--min-filled-cells`：每个表格正文行至少需要多少个有效单元，默认 `1`。
- `--format table|json`：默认 `table`。

输出：

- 文件数、表格数、问题数。
- 每张表的列数、行数、有效单元和空单元。
- 空表头、重复表头、空表、行宽不一致、正文行有效单元过少、文件无表格等问题。
- 默认只检查章节文件；项目结构表格通常需要 `--all`。

失败：

- 目标路径不存在。
- `--min-filled-cells` 小于 `1`。

### `fictionops audit-wave`

输入：

- `path`：目标文件或目录，默认当前目录。
- `--all`：统计所有 Markdown。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--metric nonspace|cjk|chars`：默认 `nonspace`。
- `--flat-tolerance`：相邻章节体量差不超过该值时视为平直延续，默认 `200`。
- `--min-spread-ratio`：整本最大最小差低于平均值多少百分比时提示过平，默认 `15`。
- `--max-flat-run`：连续多少章平直时提示，默认 `4`。
- `--max-same-band-run`：连续多少章同体量档时提示，默认 `5`。
- `--format table|json`：默认 `table`。

输出：

- 章节数、总字数、平均值、最大最小值、离散幅度、相邻平均差。
- 每章的体量值、相邻差值、体量档位和行数。
- 整本过平、连续平直、连续同档、连续短章、连续重章和相邻突跳等维护提示。
- 默认只统计章节文件，不把章节发动机当正文。

失败：

- 目标路径不存在。

### `fictionops audit-style`

输入：

- `path`：目标文件或目录，默认当前目录。
- `--all`：扫描所有 Markdown。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--watch`：逗号分隔的关注词。
- `--top`：聚合输出数量，默认 `12`。
- `--min-repeat`：重复句首阈值，默认 `3`。
- `--format table|json`：默认 `table`。

输出：

- 关注词命中。
- 重复句首。
- 章节开头和结尾类型。

失败：

- 目标路径不存在。

### `fictionops review-workflow`

输入：

- `path`：目标章节文件或目录，默认当前目录。
- `--all`：扫描所有 Markdown，而不只识别出的章节文件。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--focus`：写入报告的人工可读审读焦点标签，默认 `style`。
- `--top-lines`：每个文件最多收集多少条证据行，默认 `40`。
- `--out`：写入 Markdown 或 JSON workflow 报告；相对路径解析到目标目录或章节所在目录。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 对目标章节或章节集合做预扫，统计 `不是`、`没有`、`像`、`忽然/突然`、冷系、热系和解释标记等问题族。
- 把高密度模式归入 `exclusionary_narration`、`absence_filter`、`simile_translation`、`sensory_default`、`turn_signal_overuse` 或 `authorial_explanation`。
- 为每个文件输出 P1-P4 风险、证据行、建议 agent 角色任务、修订队列和修后复检目标。
- 只生成审读 workflow，不调用模型、不改正文、不自动应用修订；真实模型审读仍应通过 `agent-run` / `agent-exec` / `agent-inbox` 或外部 runner 暂存。

失败：

- 目标路径不存在。
- `--top-lines` 小于 `1`。
- `--out` 已存在且未传 `--force`。

### `fictionops audit-continuity`

输入：

- `path`：目标项目、书、章节文件或目录。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--skip-standard`：跳过标准项目记忆文件检查。
- `--min-chapter-chars`：低于该值的章节视为占位，默认 `200`。
- `--format table|json`：默认 `table`。

输出：

- 章节是否有对应章节发动机和复盘。
- 标准项目记忆文件是否缺失或仍像模板。
- 占位章节、占位发动机、占位复盘提示。

失败：

- 目标路径不存在。

### `fictionops audit-echoes`

输入：

- `path`：目标项目、书、伏笔表或目录。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--table`：指定伏笔表路径。
- `--no-text-scan`：不扫描正文粗略命中。
- `--stale-after`：超过多少章未回声视为过久，默认 `8`。
- `--format table|json`：默认 `table`。

输出：

- 伏笔表线程。
- 初种、上次回声、当前状态、下一次轻回声、禁止提前解释、兑现方向。
- 粗略正文命中和过久未回声提示。

失败：

- 目标路径不存在。

### `fictionops audit-info`

输入：

- `path`：目标项目、书、信息释放表或目录。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--table`：指定信息释放表路径。
- `--no-text-scan`：不扫描正文粗略命中。
- `--format table|json`：默认 `table`。

输出：

- 信息释放表文件列表。
- 信息/秘密条目、作者真相、读者当前认知、角色/公共/官方版本、下一次释放和禁止提前暴露项。
- 正文粗略命中数、首次命中文件、最后命中文件。
- 缺表、表无法解析、缺作者真相、缺认知版本、缺下一次释放、缺禁止项、疑似提前命中等维护问题。

失败：

- 目标路径不存在。

### `fictionops audit-characters`

输入：

- `path`：目标项目、人物文件或目录。
- `--pattern`：目录扫描 glob，默认 `**/*.md`。
- `--format table|json`：默认 `table`。

输出：

- 人物索引、智慧模式表、口吻表、关系图和人物弧线文件的覆盖摘要。
- 人物弧线里身份起点、起始状态、智慧模式、口吻、关系锚点、成长路径和失误路径的维护缺口。
- 人物索引与人物弧线文件是否互相覆盖。
- 缺智慧模式资料、缺口吻资料、索引人物缺弧线等维护问题。

失败：

- 目标路径不存在。

### `fictionops agent-prompt`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--role`：必填，支持 `architect`、`canon-keeper`、`character-auditor`、`info-boundary-auditor`、`foreshadowing-auditor`、`chapter-planner`、`draft-writer`、`style-auditor`、`publisher`。
- `--task draft|review|handoff|canon-sync`：上下文任务类型；默认使用该角色的自然任务。
- `--book`：书号，默认 `book_01`。
- `--chapter`：章节号；当 `--include-context` 且任务为 `draft` 或 `review` 时必须提供。
- `--include-context`：把范围化 context-pack 附在提示词后面。
- `--include-context-content`：附带 context-pack 时内嵌文件内容。
- `--max-chars-per-file`：每个上下文文件最多内嵌多少字符，默认 `6000`。
- `--max-total-chars`：全部上下文文件合计最多内嵌多少字符，默认 `60000`。
- `--out`：写出 Markdown 提示词；相对路径解析到 `path` 内部。
- `--dry-run`：构造报告但不写 `--out`。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 角色边界、输入偏好、必须做、禁止做、工作顺序和输出契约。
- 推荐的本地命令，例如 `context-pack` 和 `revision-plan`。
- 如果启用 `--include-context`，输出内嵌的 context-pack 摘要或内容。
- 不调用模型，不直接修改正文或正史文件。

失败：

- 输入 `path` 不存在或不是目录。
- `--role` 不在支持列表中。
- `--include-context` 时底层 context-pack 条件不满足。
- `--out` 已存在且未传 `--force`。

### `fictionops agent-connect`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--name`：接入套件名称，会规范化为目录名，默认 `default`。
- `--mode manual|runner|controller|model-runner`：接入模式，默认 `runner`。
- `--out-dir`：写入接入套件目录；相对路径解析到项目内部，默认 `00_management/agent_connectors/<name>`。
- `--dry-run`：构建报告但不写文件。
- `--force`：覆盖已有接入套件文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 写出 `README.md`、`connector_manifest.json`、`.env.example`、`smoke_commands.md` 和 `runner_adapter.py`。
- `connector_manifest.json` 记录 connector 名称、模式、provider/model 元数据、允许命令、禁止动作、烟测命令和安全标记。
- `.env.example` 只记录环境变量名，不保存真实密钥。
- `runner_adapter.py` 是无网络烟测 stub，可被真实模型 runner 替换。
- 不调用模型，不执行 controller，不应用暂存输出，不修改正文或正史。

失败：

- 目标路径不存在或不是目录。
- `--name` 规范化后为空。
- 输出文件已存在且未传 `--force`。

### `fictionops eval-agent`

**用途**：在临时项目副本上跑一条无网络 Agent workflow 评估链，验证任务包、暂存输出、收件箱复核边界和 controller 下一步选择是否闭合。

**输入**

- `path`：目标 FictionOps 项目 fixture，默认当前目录。命令会复制到临时目录，不修改源 fixture。
- `--book`：书 id，默认 `book_01`。
- `--chapter`：章节号，默认 `002`。
- `--runner echo|openai-chat-dry-run`：内置无网络 runner，默认 `echo`。
- `--out`：写出 Markdown 或 JSON 评估报告；未传时只输出到 stdout。
- `--force`：允许覆盖已有 `--out`。
- `--dry-run`：只规划评估，不执行内置 runner，不写 `--out`。
- `--format markdown|json`：输出格式，默认 `markdown`。

**输出**

- 复制 fixture 到临时目录，运行 `agent-run`、`agent-exec`、`agent-inbox`、`doctor` 和 `agent-next`。
- 报告包含 `status`、`ready`、任务 ID、命令轨迹、指标、观察项和下一步建议。
- 当前内置指标包括 `staged_output_rate`、`direct_write_violations`、`review_boundary_recall`、`doctor_blocking_delta`、`task_trace_completeness`、`recovery_cost` 和 `controller_step_validity`。
- 命令不调用真实模型供应商，不保存密钥，不修改源 fixture，不应用暂存输出到正文或正史。

**失败条件**

- `path` 不存在或不是目录。
- `--runner` 不是支持的无网络 runner。
- `--out` 已存在且未传 `--force`。
- 底层任务包、执行桥、收件箱或下一步选择遇到文件系统异常。

### `fictionops agent-smoke`

**用途**：对 `agent-connect` 生成的接入套件跑一条无网络烟测链，证明 connector staging boundary 能闭合。

**输入**

- `path`：FictionOps 项目目录，默认当前目录。
- `--connector`：必填，指向 `00_management/agent_connectors/<name>`。
- `--level manual|runner|controller|model-runner`：可选；默认读取 connector manifest 的 `mode`，再退回 `runner`。
- `--role`：烟测任务角色，默认 `draft-writer`。
- `--book`：书 id，默认 `book_01`。
- `--chapter`：章节号，默认 `001`。
- `--out-dir`：烟测任务包目录；默认 `00_management/agent_runs/<connector>_smoke_ch_<chapter>`。
- `--output-name`：暂存输出文件名，默认 `output.md`。
- `--timeout-seconds`：adapter 超时秒数，默认 60。
- `--force`：只覆盖当前 smoke run 自己已有的任务包输出和执行回执；其他待复核 agent 输出仍会阻止烟测继续。
- `--dry-run`：只规划烟测链，不写文件、不执行 adapter。
- `--format markdown|json`：输出格式，默认 `markdown`。

**输出**

- 先运行 `audit-agent-workflow --connector <name>`，connector 或项目边界未就绪时停止。
- 正式运行时写出一个 `agent-run` prepare-only 任务包。
- 通过 `agent-exec` 调用 connector kit 里的 no-network `runner_adapter.py`，把 stdout 保存为暂存输出。
- 通过 `agent-inbox` 验证该 run 目录只有一个可复核输出。
- 状态可为 `dry_run`、`smoke_passed`、`smoke_failed` 或 `not_ready`。

**失败条件**

- connector kit 缺失、manifest 不匹配、安全标记不合格或 adapter 文件缺失。
- 项目已有待复核 agent 输出，前置 workflow audit 要求人先处理。
- 任务包或暂存输出已存在且未传 `--force`。
- adapter 超时、非零退出或 stdout 为空。

### `fictionops agent-run`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--role`：必填，支持与 `agent-prompt` 相同的角色。
- `--task draft|review|handoff|canon-sync`：上下文任务类型；默认使用角色自然任务。
- `--book`：书号，默认 `book_01`。
- `--chapter`：章节号；`draft`、`review` 和带章节的 `canon-sync` 使用。
- `--out-dir`：写出 Agent 任务包目录；相对路径解析到 `path` 内部。
- `--no-context-content`：只列出范围化文件，不内嵌正文内容。
- `--max-chars-per-file`、`--max-total-chars`：控制上下文内容预算。
- `--dry-run`、`--force`、`--format markdown|json` 遵循通用契约。

输出：

- `execution_mode` 必须是 `prepare_only`，表示命令只准备任务包。
- 报告包含 `role`、`task`、`book`、`chapter`、`provider`、`model`、`model_config_file`、`files`、`next_actions`、`agent_prompt`、`context_pack`、可选 `draft_brief` 和 `model_config`。
- 使用 `--out-dir` 时，至少写出 `README.md`、`request.json`、`prompt.md` 和 `context_pack.md`；`draft` 任务且有章节时还应写出 `draft_brief.md`。
- `request.json` 必须声明不调用模型、不保存密钥、不覆盖正文，并要求人工或外部 runner 把输出写入 staging 文件。
- JSON 输出必须保持纯 JSON。

失败：

- 输入 `path` 不存在或不是目录。
- `--role` 不在支持列表中。
- 底层 `agent-prompt`、`context-pack` 或 `draft-brief` 条件不满足。
- `--out-dir` 中目标文件已存在且未传 `--force`。

### `fictionops agent-exec`

输入：

- `path`：某个已经由 `agent-run` 生成的 run 目录，必须包含 `request.json`、`prompt.md` 和 `context_pack.md`。
- `--runner ...`：必填。外部 runner 命令；FictionOps 参数必须放在 `--runner` 之前，`--runner` 之后的所有参数原样交给外部命令。
- `--output-name`：写入 run 目录内的暂存输出文件名，默认 `output.md`，必须是单个文件名，不能是绝对路径或跨目录路径。
- `--timeout-seconds`：外部 runner 超时时间，默认 300 秒。
- `--force`：允许覆盖已有暂存输出或 `execution.json`。
- `--dry-run`：只构造 runner 输入和报告，不执行外部命令，不写文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 将 `request.json`、`prompt.md`、`context_pack.md` 和可选 `draft_brief.md` 组合成 runner stdin。
- 执行外部命令，把 stdout 写入 run 目录内的暂存输出文件。
- 写出 `execution.json`，记录外部命令、返回码、输出文件和安全策略。
- 报告必须声明：FictionOps 不保存 API key、不读取真实 API key、不覆盖正文、不自动应用输出；外部 runner 是否调用模型由 runner 自己负责。

失败：

- `path` 不存在、不是目录，或缺少必要任务包文件。
- `request.json` 不是 `fictionops.agent_run_request.v1`，或不是 `prepare_only` 任务包。
- 未传 `--runner` 或 runner 返回非零退出码。
- runner 超时，或 stdout 为空。
- 输出文件或 `execution.json` 已存在且未传 `--force`。

### `fictionops agent-inbox`

输入：

- `path`：FictionOps 项目目录，或某个包含 `request.json` 的单个 Agent run 目录；默认当前目录。
- `--runs-dir`：当 `path` 是项目目录时扫描的任务包目录；默认 `00_management/agent_runs`。
- `--output-name`：指定每个 run 目录里的输出文件名；未指定时寻找 `output.md`、`response.md`、`result.md`、`staging.md`、`model_output.md`、`agent_output.md` 和 `*.staging.md`。
- `--format markdown|json` 遵循通用契约。

输出：

- 报告包含 `status`、`run_count`、`ready_count`、`awaiting_count`、`needs_attention_count`、逐 run 状态、问题列表和下一步动作。
- 如果 run 目录没有输出文件，状态为 `awaiting_output`，问题为 P4 `missing_output`。
- 如果输出文件唯一且非空、`request.json` 安全策略有效，状态为 `ready_for_review`。
- 如果存在多个输出候选、空输出、坏 JSON、缺安全策略或缺必要 bundle 文件，状态为 `needs_attention`。
- 命令只读检查，不调用模型、不保存密钥、不应用输出、不修改正文。

失败：

- 输入 `path` 不存在或不是目录。
- `request.json` 无法读取时应进入问题列表；除非底层文件系统异常，命令本身不应因为单个坏 run 中断整个收件箱审计。

### `fictionops agent`

子命令：

- `agent write`：复用 `agent-write-workflow` 的因果模拟、规划、写作、复修、验证、预算和暂存采纳契约；
- `agent revise`：复用 `agent-revise-workflow` 的综合审读、preservation verifier、修订、语义复核、预算与暂存契约；
- `agent guard set/retire`：在 `.fictionops/author_guards.json` 创建、更新或退役稳定 `G-*` 作者约束；`agent guards` 查看 active/retired guard。只有 active author guard 能授权 verifier 直接 withdraw。
- `agent accept`：复用 `agent-accept-revision` 的源稿/候选哈希校验和显式采纳契约；
- `agent continue`：扫描项目内 session、`model_budget.json`、采纳状态和 memory stale 状态，选择下一项安全动作。
- `agent issues`：读取 `.fictionops/issues.json`，按状态或章节筛选跨 session 问题；
- `agent issue`：由作者显式把单个稳定 issue 标为 `waived`、`rejected` 或 `reopened`，必须填写理由。
- `agent cancel`：把未应用的 session 显式转为 `cancelled`，写出 `cancellation.json` 与不可恢复 checkpoint；必须填写理由，重复取消和取消已应用 session 均拒绝。

`agent continue --execute` 只自动执行 R0 动作，目前包括重建 stale 的派生记忆索引。候选待采纳、失败候选、预算耗尽和正史同步建议分别停在 R1-R4 人工边界；不能因为传入 `--execute` 而自动接受正文、扩大预算或修改正史。JSON 输出包含所选动作、风险、停止原因、证据文件和建议命令。

项目 issue ledger 使用稳定 ID，记录 `open/planned/addressed/verified/accepted/rejected/waived/reopened` 生命周期、每次观察、session、证据指纹和决定。相同问题改写措辞、增加引文或调整 reviewer 排序时，应按类别、metric key、证据重叠和描述相似度复用 ID。`waived/rejected` 不得重新进入活动修订队列；已解决问题在后续 session 再次观察到时自动 `reopened`。

写章与修订 session 在 `context_ready/causal_ready/plan_ready/review_ready/draft_ready/verification_ready/ready_for_approval/needs_revision_attention/applied/cancelled` 等阶段写 `checkpoint.json`。checkpoint 必须包含源哈希、关键产物路径/大小/SHA-256、下一动作和 `resumable` 标记。`agent resume RUN_DIR --runner ...` 会先校验 session、源文件、章节发动机和 checkpoint 产物，再开启新的预算分段；写章支持从 `context_ready/causal_ready/plan_ready/draft_ready` 恢复，修订支持从 `context_ready/review_ready/verification_ready` 恢复，已完成的模型阶段不会重跑。`agent status` 只读汇总全项目 session、issue、作者待决策项、token 与费用。`--runner` 会接收其后的全部参数，因此必须放在命令最后。尚未支持的中间态、已取消会话、源文件变化或产物哈希变化都会被拒绝。

`agent continue` 的下一动作由纯函数 controller policy 根据 state、evidence、budget 与 authority 选择；输出包含 action、risk、authority 和 executable，模型不能自行取得作者权限。写章与修订 run 同时追加 `trajectory.jsonl`，统一记录上下文来源/权威/选择理由、模型调用与 telemetry、证据、状态迁移和作者/controller 权限。

`agent benchmark` 可在同一 runner 上重复运行 `raw/rag/full/no_memory/no_guard/no_contract`，fixture 标准答案不会进入 prompt。Benchmark v2 同时使用正例和 preservation 负例，报告 precision、recall、accuracy、false-positive rate 与 grounded evidence；`--blind-out` 和 `--blind-key-out` 分开写入匿名人工评审包与条件映射。`agent failure-lab` 在临时工作区注入源文件、checkpoint 产物、预算、receipt、reviewer 证据和故事契约故障，并报告发现点、恢复率与受保护哈希。

`agent counterevidence export` 把 preservation verifier 留下的 `needs_counterevidence` finding 导出为匿名标注包，并把 prompt/case/condition/control 标签隔离到单独私钥。输入可以是 `agent revise` 运行目录，也可以是 preservation evidence、benchmark 输出和 fixture 三件套。`agent counterevidence score` 拒绝未填、非法或 packet/key 不匹配的标注，统计裁决、证据落地、误修风险、人工耗时，以及与继承自 benchmark 的 case-level control 的一致或标签挑战；它不会把 case 标签伪装成动态 finding 的 issue-level 真值。

`agent counterevidence escalate` 对人工标为 `insufficient` 的 finding 做确定性精确去重，并按断言尺度路由到全章、相邻段、知识来源、人物记忆或作者意图证据；未标注 packet 则预路由全部 finding。提供 `--chapter` 时可检索有界正文与项目上下文，缺源时停在 `needs_source`，不会伪造证据或修改正文。

`agent counterevidence reverify` 对 evidence-ready 的去重请求逐条调用独立模型，输出 `uphold/withdraw/still_insufficient`。调用前执行硬预算检查，每条畸形输出最多一次有界 schema repair，并记录 runner receipt 与 token；resolved verdict 若没有逐字存在于所供材料的引文，会被确定性降回 `still_insufficient`。命令不修改正文，也不把模型输出升级为作者权限。

### `fictionops agent-memory`

契约：

- `build` 从 Markdown 正史、人物、大纲、正文和写作指引重建 `.fictionops/memory/index.json`；索引是可重建缓存，不是新正史。
- `query` 根据任务、人物和章节检索分层记忆，返回来源、哈希、权威、行号、分数与裁剪内容。
- `add-preference` 只记录作者明确偏好，必须提供 `--rule` 和 `--evidence`；偏好不能由模型自动升级。
- `status` 报告索引、显式偏好、采纳事件与 stale 状态。
- 命令不调用模型，不改正文，不自动应用正史同步建议。

### `fictionops agent-revise-workflow`

输入：

- `chapter`：要修订的 Markdown 正文章节文件。
- `--review`：已有 `review-workflow` Markdown 报告；未传时命令会基于章节临时生成并写入 bundle。
- `--out-dir`：Agent run bundle 目录；相对路径从发现到的项目锚点解析，默认写入 `00_management/agent_runs/`、`00_总纲与管理/agent_runs/` 或章节旁的 `.fictionops_agent_runs/`。
- `--role`：写入 `request.json` 的 Agent 角色，默认 `style-auditor`。
- `--provider` / `--model`：写入 `request.json` 的供应商和模型标签；未传时使用可发现的 model config。
- `--runner ...`：可选外部 runner；未传时只准备 bundle。
- `--max-retries`：静态或语义验证失败后的定向重修上限，范围 0-2，默认 1。
- `--max-model-calls` 默认 12，`--max-runtime-seconds` 默认 1800；覆盖综合审读、修订、语义复核和重试的全部模型调用，耗尽时在下一次调用前停止并写出 `model_budget.json`。
- runner 可在 stderr 输出一行 `FICTIONOPS_RUNNER_RECEIPT:` JSON（schema 为 `fictionops.runner_receipt.v1`），回传 provider/model/request id、token usage 和显式价格计算的费用；元数据进入 `execution.json` 与 `model_budget.json`，不会混入候选正文。`--max-total-tokens`、`--max-cost`、`--cost-currency` 会依据已回传的累计消耗，在下一次调用前停止。
- `--no-semantic-verify`：跳过模型驱动的源稿/候选语义不变量比较；默认会执行语义验证。
- `--review-scope style|comprehensive`：默认 `comprehensive`，写前先审连续性、人物、信息边界、伏笔、章节功能和行文/读者体验；`style` 只保留较窄的行文模式路径。
- `--context-file`：显式补入项目记忆文件，可重复；综合模式还会自动检索相邻章、同书材料、人物弧线和正史文件。
- 综合模式默认同时检索类型化记忆和作者显式偏好，并写出 `memory_query.json` / `memory_context.md`；`--no-memory` 只用于兼容或诊断。
- `--output-name`、`--timeout-seconds`、`--force`、`--force-output`、`--dry-run`、`--format markdown|json` 遵循 Agent 执行类命令契约。

输出：

- 写出自包含 bundle，并建立 `session.json`、`events.jsonl`、`source_manifest.json`、`issues.before.json` 和 `audits.before.json`。
- `revision_contract.md` 要求 runner 只输出修订后的章节全文，不输出解释、总结或诊断。
- 传入 `--runner` 时，命令生成 `candidate.md`、`changes.diff`、`audits.after.json`、`issues.after.json` 和 `verification.json`；失败时可把阻塞证据编入一次定向重修。
- 静态验证检查输出完整性、标题/结构、长度区间和风格指标退化；通过后默认再次调用 runner，比较事件、视角、时间、人物意图、信息边界与留白是否保持。
- JSON 输出必须包含 `command`、`chapter_file`、`run_dir`、`session_id`、`source_sha256`、`verification_status`、`ready_for_approval`、`retry_count`、`semantic_call_count`、`max_model_calls`、`model_calls_used`、`files` 和 `staged_outputs`。
- 命令不得自动覆盖源章节；只有 `ready_for_approval` 候选才能交给 `agent-accept-revision`。

失败：

- `chapter` 不存在、不是文件，或 `--review` 指向不存在/非文件。
- bundle 文件已存在且未传 `--force`。
- runner 输出或执行回执已存在且未传 `--force-output` 或 `--force`。
- runner 返回非零、超时或 stdout 为空。

### `fictionops agent-accept-revision`

输入：

- `run_dir`：包含 `session.json`、`candidate.md` 和 `verification.json` 的 revision run 目录。
- `--dry-run`：只验证状态和哈希，不修改源章节。
- `--format markdown|json` 遵循通用契约。

输出与写入：

- 只有 `verification.json` 为 `ready_for_approval` 时才允许继续。
- 同时核对源章节当前 SHA-256 与会话起始哈希，以及候选当前 SHA-256 与验证时哈希。
- 正式接受时原子替换源章节，写出 `acceptance.json`，把 `session.json` 状态更新为 `applied`，并追加 `events.jsonl`。
- 正式接受后追加 `.fictionops/memory/acceptance_events.jsonl` 并将记忆索引标为 stale；正史同步建议仍保持建议状态，显式作者偏好必须另行确认。
- `source_chapter.md` 始终保留会话开始时的源稿快照。

失败：

- 候选未通过验证；
- 源章节在会话开始后发生变化；
- 候选在验证后发生变化；
- `acceptance.json` 已存在，说明该会话已经应用过。
- 命令故意不提供 stale-source 强制覆盖选项；遇到新稿应重新开始修订会话。

### `fictionops agent-write-workflow`

输入：

- `chapter`：新章目标 Markdown 路径；可以尚不存在，也可以只有 FictionOps 生成占位，若已有实质正文则拒绝并要求使用 `agent-revise-workflow`。
- `--engine`：必需的章节发动机 Markdown。
- `--outline`：可选书纲/卷纲文件。
- `--context-file`：额外人物、正史或写作记忆，可重复。
- `--min-chars`：候选正文最低非空白字符数；默认取发动机目标体量减 200，未填目标时为 200。
- `--max-retries`：验证失败后的完整定向重写上限，范围 0-2，默认 1。
- 默认先检索类型化项目记忆，再调用 `causal-simulator` 生成利益相关者、代价转移、视角白名单、知识限制和禁止结论；`--no-memory`、`--no-causal-simulation` 仅用于兼容或诊断。
- 默认在 draft evaluator 之前独立调用 `adversarial-reviewer`；`--no-adversarial-review` 会降低验收强度，只应用于受控调试。
- `--scene-by-scene` 会把每个计划场景交给独立 `scene-writer` 调用，传递入口/出口状态与上一场末尾，再组装成完整候选；默认仍为一次整章写作调用。
- `--max-model-calls` 默认 32，`--max-runtime-seconds` 默认 3600；两者是 controller 硬预算。每次模型调用前检查，预算耗尽时停止并写出 `model_budget.json`，不会继续调用 runner。
- `--max-total-tokens` 与 `--max-cost` 是可选的 receipt-backed 累计阈值；恢复后的预算分段仍继承旧段 token/费用总数。单次正在进行的调用可能越过阈值，但下一次调用会被阻止。
- `--runner`、供应商、模型、上下文预算、覆盖、dry-run 和 JSON 参数遵循 Agent workflow 通用契约。

输出与状态：

- 写出项目感知 `project_context.md`，记录每份上下文的路径、哈希、权威、入选理由和截断状态。
- `chapter-planner` 先把大纲/发动机编译成 `chapter_plan.json`；缺少关键决定时必须阻塞，不能补造正史。
- 写出 `memory_query.json`、`causal_simulation.json`、`chapter_contract.json`、`story_fact_ledger.json` 和 `scene_state_contract.json`，每个场景必须声明稳定 ID、视角、入口状态和出口状态。
- 结构化数量、时间窗和物件转移在正文生成前校验；逐场景模式另外生成 `scene_execution.json`，保存每场目标/实际体量、状态、输出哈希和组装哈希。失败后优先按 reviewer 原文证据和失败 `scene_id` 只复修命中的场景，无法定位才回退为全场复修。
- `draft-writer` 生成完整候选，静态检查标题、体量、占位和输出纯度。
- `draft-evaluator` 检查章节发动机、场景推进、人物声音、信息边界、连续性、伏笔、行文新鲜感和结尾变化八个维度。
- `adversarial-reviewer` 只看候选、章节契约和检索记忆，逐条寻找反证；确定性门禁另外检查禁止结论、可疑禁用视角场景、受限奏疏/梦境/回忆长度和段落节奏证据。
- 验证失败时，问题证据进入下一轮完整重写；旧候选、验证、评估和执行回执按版本保留。
- 通过后写出 `candidate.md`、`changes.diff`、`verification.json`、`draft_evaluation.json`、`retrospective.draft.md` 和 `canon_sync_suggestions.json`，状态为 `ready_for_approval`。
- 命令不直接创建或覆盖目标正文；使用 `agent-accept-revision` 显式采纳。若目标原本不存在但会话期间被其他人创建，采纳必须拒绝。

### `fictionops write-chapter`

契约：

- 准备 AI-first 单章写作任务包，默认 role 为 `draft-writer`，task 为 `draft`。
- 默认只写 `agent-run` 任务包；只有传入 `--runner` 时才执行外部 runner。
- runner 输出必须进入暂存文件，并通过 `agent-inbox` 检查；命令不得自动应用到正文或正史。
- `--force` 只覆盖任务包；`--force-output` 才覆盖已有暂存输出或执行回执。
- JSON 输出必须包含 `command`、`role`、`task`、`run_dir`、`stop_reason`、`ready_count` 和 `staged_outputs`。

### `fictionops revise-chapter`

契约：

- 准备 AI-first 单章修订任务包，默认 role 为 `style-auditor`，task 为 `review`。
- 默认只准备任务包；传入 `--runner` 后才调用外部模型 runner 并写入暂存输出。
- 不得直接重写章节正文；修订建议必须经过 `agent-inbox` 和人工接受。
- 路径、覆盖、JSON 和 runner 规则与 `write-chapter` 保持一致。

### `fictionops audit-chapter`

契约：

- 准备 AI-first 单章审计任务包，默认 role 为 `info-boundary-auditor`，task 为 `review`。
- 适合信息边界、知识泄露、章节风险等审计型输出。
- 默认不调用模型；传入 `--runner` 时只把外部输出保存为暂存审计结果。
- 不得自动修改正文、人物、设定或信息表；接受后的同步由作者或后续门禁决定。

### `fictionops agent-session`

契约：

- 为单章 AI 写作链路创建或刷新持久 session 台账，默认跟踪 `write`、`revise`、`audit` 三步。
- 台账写入 `00_management/agent_sessions/<session-id>/README.md` 和 `session.json`。
- 每一步指向对应的 `00_management/agent_runs/<session-id>_<stage>_<book>_ch_<chapter>` 目录。
- 命令只读取已有 staged run 状态并给出下一步建议；不调用模型、不执行 runner、不自动应用输出。
- JSON 输出必须包含 `schema`、`session_id`、`status`、`steps`、`files` 和 `next_actions`。

### `fictionops agent-next`

输入：

- `path`：目标 FictionOps 项目目录、旧写作目录，或尚不存在的未来项目路径；默认当前目录。
- `--book`：书 id，默认 `book_01`。
- `--chapter`：可选章节号；提供后会纳入章节脚手架、草稿和审稿门禁判断。
- `--no-text-scan`：构造底层健康证据时跳过正文扫描，适合外部 controller 做轻量状态轮询。
- `--format markdown|json`：默认 `markdown`。

输出：

- 报告包含 `status`、`selected_command`、`selected_reason`、`candidate_count`、`candidates`、`evidence` 和 `notes`。
- `candidates` 中每项必须包含 `priority`、`stage`、`command`、`reason`、`safe_to_auto_run` 和 `requires_human_review`。
- 命令会优先处理迁移导入队列和 Agent 收件箱，再考虑章节准备、正文任务包、审稿门禁、修订计划、发布门禁和工作流清单。
- 状态可为 `ready_for_agent_step`、`needs_human_review`、`needs_manual_step` 或 `no_action`。
- 命令只读，不执行 `selected_command`，不调用模型，不保存密钥，不应用暂存输出，不修改正文或正史。

失败：

- `path` 存在但不是目录。
- 底层健康检查遇到文件系统异常。

### `fictionops audit-agent-workflow`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--level manual|runner|controller|model-runner`：要审计的接入层级，默认 `runner`。
- `--book`：controller 级证据使用的书 id，默认 `book_01`。
- `--chapter`：controller 级证据使用的可选章节号。
- `--connector`：可选，校验 `00_management/agent_connectors/<name>` 下的接入套件。
- `--scan-text`：允许通过 `agent-next` 做正文扫描；默认跳过，适合接入前轻量预检。
- `--format markdown|json`：默认 `markdown`。

输出：

- 报告包含 `target`、`level`、`status`、`ready`、`issue_count`、`blocking_issue_count`、`issues`、`evidence` 和 `next_actions`。
- 传入 `--connector` 时，报告还会校验 connector manifest、必需文件、安全标记、允许命令和烟测命令。
- `manual` 级检查项目骨架与基础暂存边界；`runner` 级检查外部 runner 暂存输出边界；`controller` 级还检查 `agent-next` 是否碰到人工复核边界；`model-runner` 级还要求模型供应商配置足以支撑真实 runner。
- 状态可为 `ready`、`not_ready`、`needs_human_review`、`missing_project` 或 `not_standard_project`。
- 命令只读，不调用模型，不执行 controller，不应用暂存输出，不修改正文或正史。

失败：

- `path` 存在但不是目录。
- `--level` 不是支持的接入层级。
- 底层收件箱、模型配置或 `agent-next` 检查遇到文件系统异常。

### `fictionops setup-ai`

契约：

- 面向首次接入真实模型 API，按 provider preset 写入 `00_management/model_config.json` 和 `00_management/ai_runner.env.example`。
- 支持 OpenAI-compatible provider：`openai-chat`、`deepseek`、`qwen`/`dashscope`、`kimi`/`moonshot`、`glm`/`zhipu`、`doubao`/`volcengine-ark`、`siliconflow`、`local-openai`。
- 只记录 API key 所在环境变量名，不得写入真实 API key。
- 默认不覆盖已有 setup 文件；传入 `--force` 才能覆盖。
- `--dry-run` 只输出计划，不写文件。
- JSON 输出必须包含 `schema=fictionops.ai_setup.v1`、`provider`、`model_config`、`files`、`dry_run_command`、`real_run_command`、`next_actions` 和 `safety`。
- 命令不得调用模型，不得写正文或正史；真实模型调用仍必须通过 runner 暂存输出并进入 `agent-inbox`。

### `fictionops model-config`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--provider`：模型供应商名，例如 `openai`、`anthropic`、`local` 或项目自定义供应商。
- `--planning-model`、`--drafting-model`、`--audit-model`：分别记录规划、正文和审计任务使用的模型名。
- `--api-key-env`：密钥所在环境变量名；命令只保存变量名，不保存真实密钥。
- `--base-url`：可选的供应商基础地址。
- `--max-context-chars`、`--max-output-tokens`、`--timeout-seconds`：本地配置中的软限制。
- `--out`：指定配置文件路径；相对路径解析到 `path` 内部，默认 `00_management/model_config.json`。
- `--write`：写出配置文件；未提供时只预览报告。
- `--dry-run`：构造报告但不写文件。
- `--force`：覆盖已有配置文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 供应商、三个任务模型、基础地址、密钥环境变量名和环境变量是否存在。
- 本地配置 JSON，schema 为 `fictionops.model_config.v1`。
- 配置问题，例如供应商未配置、模型名未配置、密钥环境变量未填写或未设置。
- 如果使用 `--write`，写出配置文件；不保存真实 API key，不调用模型。

失败：

- 输入 `path` 不存在或不是目录。
- 已有配置文件不是 JSON 对象。
- `--write` 目标文件已存在且未传 `--force`。

### `fictionops context-pack`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--task draft|review|handoff|canon-sync`：上下文任务类型，默认 `draft`。
- `--book`：书号，默认 `book_01`。
- `--chapter`：章节号；`draft` 和 `review` 必须提供，`canon-sync` 可选。
- `--no-content`：只列出范围化文件，不内嵌文件内容。
- `--max-chars-per-file`：每个文件最多内嵌多少字符，默认 `6000`。
- `--max-total-chars`：全部文件合计最多内嵌多少字符，默认 `60000`。
- `--out`：写出 Markdown 上下文包；相对路径解析到 `path` 内部。
- `--dry-run`：构造报告但不写 `--out`。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 本次任务的检查问题清单。
- 范围化文件列表：角色、是否必需、是否存在、字数、实际嵌入字符数、是否截断、路径。
- `handoff` 任务必须纳入交接日志、决策记录、书纲和正史表，并应携带人物索引/智慧/口吻资料、doctor/report、revision-plan、book/release gate 等里程碑产物。
- 默认内嵌被选中文件内容；超过 `--max-chars-per-file` 或 `--max-total-chars` 会截断并标记。
- 缺少必读上下文时输出维护问题，不调用模型，也不判断文学质量。

失败：

- 输入 `path` 不存在或不是目录。
- `draft` / `review` 缺少 `--chapter`。
- `--out` 已存在且未传 `--force`。

### `fictionops workflow-plan`

输入：

- `path`：目标 FictionOps 项目目录；当 `--stage init` 时也可以是未来项目路径。
- `--stage`：工作流阶段，支持 `all`、`init`、`foundation`、`book-plan`、`chapter-prep`、`draft`、`review`、`book-retrospective`、`publish`、`handoff` 及常见别名。
- `--book`：书号，默认 `book_01`。
- `--chapter`：章节号；`chapter-prep`、`draft` 和 `review` 阶段必须提供。
- `--out`：写出 Markdown 工作流清单；相对路径解析到 `path` 内部。
- `--dry-run`：构造报告但不写 `--out`。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 分阶段步骤清单：阶段、步骤标题、目的、命令、产物和出口标准。
- 可逐条执行的命令列表；命令本身不会被自动执行。
- 手动步骤会显式标为 `manual:`，避免把作者判断伪装成自动化。
- JSON 输出包含 `steps`、`commands`、`notes`、`stage`、`book`、`chapter` 和写文件状态。

失败：

- 输入 `path` 不存在，且当前阶段不是 `init`。
- 输入 `path` 已存在但不是目录。
- 章节型阶段缺少 `--chapter`。
- `--out` 已存在且未传 `--force`。

### `fictionops revision-plan`

输入：

- `path`：目标项目、书或目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--outline`：指定书纲路径；相对路径解析到 `path` 内部。
- `--all`、`--pattern`、`--metric`：传给 stats、audit-wave、style 和 scan-words；表格检查会扫描项目内 Markdown 表格并忽略“没有表格”的普通正文提示。
- `--flat-tolerance`、`--min-spread-ratio`、`--max-flat-run`、`--max-same-band-run`：传给 audit-wave。
- `--skip-standard`、`--strict-standard`、`--min-chapter-chars`：传给 continuity。
- `--watch`、`--top`、`--min-repeat`：传给 style 和 scan-words。
- `--no-text-scan`、`--stale-after`：传给 echoes 和 audit-info。
- `--out`：写出 Markdown 修订计划；相对路径解析到 `path` 内部。
- `--dry-run`：构造报告但不写 `--out`。
- `--force`：覆盖已有 `--out`。
- `--format markdown|json`：默认 `markdown`。

输出：

- 按 P1-P5 排序的修订任务。
- 每个任务包含来源命令、区域、问题代码、章节/条目、路径、问题说明和建议动作。
- 风格问题以提示任务输出，不覆盖更高优先级的正史、信息边界、计划和发布问题。
- `scan-words` 的高频词只作为 P5 新鲜度提示；`check-tables` 的表格结构问题会按自身严重度进入任务列表。
- 不调用模型，不直接修改正文或正史文件。

失败：

- 输入 `path` 不存在。
- 显式传入的 `--outline` 不存在。
- `--out` 已存在且未传 `--force`。

## 5. 总览与报告命令

### `fictionops doctor`

输入：

- `path`：目标项目、书或目录。
- `--all`、`--pattern`、`--metric`：传给 stats、audit-wave、style 和 scan-words；`check-tables` 汇总项目内 Markdown 表格结构。
- `--flat-tolerance`、`--min-spread-ratio`、`--max-flat-run`、`--max-same-band-run`：传给 audit-wave。
- `--skip-standard`、`--strict-standard`、`--min-chapter-chars`：传给 continuity；`--min-chapter-chars` 也会传给发布稿短章检查。
- `--watch`、`--top`、`--min-repeat`：传给 style 和 scan-words。
- `--no-text-scan`、`--stale-after`：传给 echoes；`--no-text-scan` 也会传给 audit-info。
- `--book`、`--outline`：传给 plan、retrospective、book-gate、publish、metadata、manifest、EPUB 和 release-gate 集成。
- `--format table|json`：默认 `table`。

输出：

- `book-gate`、`release-gate`、`stats`、`scan-words`、`check-tables`、`audit-wave`、`audit-style`、`audit-continuity`、`audit-echoes`、`audit-info`、`audit-characters`、`audit-plan`、`retrospective`、`model-config`、`audit-publish`、`export-metadata`、`export-manifest`、`export-epub`、`audit-epub` 的聚合摘要。
- 健康状态：`pass`、`review`、`maintenance_needed`、`needs_attention`、`critical`。
- 建议列表。

失败：

- 目标路径不存在。
- 显式传入的 `--outline` 不存在。

说明：

- 如果默认 clean Markdown 不存在，Publish 区块会标为 skipped，不会推高健康状态。
- 标准项目的 Model Config 区块会检查默认 `00_management/model_config.json` 或默认占位配置；供应商、模型名、密钥环境变量和不安部 key 存储策略问题会进入总健康状态。
- 如果 clean Markdown 存在，发布稿审计问题会进入总健康状态。
- 如果 clean Markdown、metadata JSON 和已填写发布清单都不存在，Metadata 区块会标为 skipped。
- 如果 clean Markdown 已存在或发布清单已开始填写，发布元数据审计问题会进入总健康状态。
- 如果 clean Markdown、metadata JSON 和 manifest 都不存在，Manifest 区块会标为 skipped。
- 如果 clean Markdown 或 metadata JSON 已存在，发布包 manifest 问题会进入总健康状态。
- `check-tables` 的 `no_tables` 只用于统计没有表格的文件数量，不会单独推高健康状态；真正的表格结构问题会进入总健康状态。
- Book Gate 和 Release Gate 区块是里程碑摘要，展示门禁状态但不重复计入 issue counts；底层问题已经由对应审计区块计入。
- 如果 clean Markdown、metadata JSON、manifest 和 EPUB 都不存在，EPUB 区块会标为 skipped。
- 如果发布包阶段已经启动，EPUB 缺失、结构不可打开或早于输入文件，会进入总健康状态。

### `fictionops report`

输入：

- 与 `doctor` 相同的审计参数。
- `--format markdown|json`：默认 `markdown`。
- `--out`：写入报告路径。
- `--force`：覆盖已有输出报告。

输出：

- 与 `doctor` 相同内容的 Markdown 或 JSON 报告。
- 不传 `--out` 时写入 stdout。

失败：

- 目标路径不存在。
- `--out` 已存在且未传 `--force`。
- 显式传入的 `--outline` 不存在。

## 6. 发布命令

### `fictionops export-clean`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--out`：输出路径，默认 `08_publish/clean_markdown/<book>.md`。
- `--title`：可选顶层标题，会写在章节正文之前。
- `--format table|json`：摘要输出格式，默认 `table`。
- `--dry-run`：只显示会导出的章节与目标路径，不写入文件。
- `--force`：覆盖已有 clean Markdown 输出。

输出：

- 按自然章节顺序合并 `06_drafts/<book>/chapters/*.md`。
- 写入 `08_publish/clean_markdown/<book>.md` 或 `--out` 指定路径。
- 移除由 `new-chapter` 创建的精确草稿标记行 `> Draft starts here.`。
- 不修改 `06_drafts/` 下的草稿源文件。
- 输出章节数、来源文件、总字数摘要。

失败：

- 目标路径不存在或不是目录。
- 对应书的 `chapters/` 目录不存在。
- 找不到任何章节 Markdown。
- 输出文件已存在且未传 `--force`。

### `fictionops audit-publish`

输入：

- `path`：目标 FictionOps 项目目录或 clean Markdown 文件，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认 clean Markdown 路径。
- `--file`：指定 clean Markdown 文件；相对路径解析到 `path` 内部。
- `--min-chapter-chars`：低于该非空白字符数的章节会被标记，默认 `200`。
- `--format table|json`：默认 `table`。

输出：

- clean Markdown 是否存在。
- clean Markdown 中可识别章节数。
- 源草稿章节数与 clean 章节数是否一致。
- 章节标题是否可识别、是否重复、是否倒退、是否缺号。
- 是否残留 `Draft starts here`。
- 是否有空章或过短章。

失败：

- 输入 `path` 不存在。
- 指定 clean Markdown 路径是目录而不是文件。

### `fictionops publish-copy`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认发布路径。
- `--clean-file`：指定 clean Markdown 文件；相对路径解析到 `path` 内部。
- `--checklist-file`：指定发布清单；相对路径解析到 `path` 内部。
- `--outline-file`：指定书纲；相对路径解析到 `path` 内部。
- `--seed-file`：指定故事种子；相对路径解析到 `path` 内部。
- `--out`：写出发布文案草稿；默认 `08_publish/synopsis/<book>_publish_copy.md`。
- `--dry-run`：构建报告但不写文件。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 从发布清单、故事种子、书纲和 clean Markdown 聚合标题候选、标签候选、关键词候选、章节标题和来源证据。
- 生成可编辑的 `suggested_metadata`，包含书名、分类、标签、短简介、长简介和关键词。
- 不调用模型，不直接修改 `08_publish/publish_checklist.md`，也不导出 metadata JSON。
- 缺少可选来源文件时输出提示；所有来源都缺失或为空时输出阻塞问题。

失败：

- 输入 `path` 不存在或不是目录。
- 指定来源路径存在但不是文件。
- 输出文件已存在且未传 `--force`。

### `fictionops export-metadata`

输入：

- `path`：目标 FictionOps 项目目录或发布清单 Markdown 文件，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认 metadata 输出路径。
- `--file`：指定发布清单文件；相对路径解析到 `path` 内部。
- `--out`：输出路径，默认 `08_publish/metadata/<book>_metadata.json`。
- `--format table|json`：默认 `table`。
- `--dry-run`：只显示摘要，不写 metadata JSON。
- `--force`：覆盖已有 metadata JSON。

输出：

- 发布清单是否存在。
- 导出的发布元数据字段。
- 是否写出 metadata JSON。
- 可选 `cover_image` 字段会原样导出，供 manifest 和 EPUB 使用。
- 缺书名、作者名、分类、标签、短简介、长简介等必填项时输出审计问题。
- 内容提示未记录、标签过少、简介过短时输出维护问题。

失败：

- 输入 `path` 不存在。
- 指定发布清单路径是目录而不是文件。
- 输出文件已存在且未传 `--force`。

### `fictionops export-manifest`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认发布包路径。
- `--clean-file`：指定 clean Markdown 文件；相对路径解析到 `path` 内部。
- `--metadata-file`：指定 metadata JSON 文件；相对路径解析到 `path` 内部。
- `--out`：输出路径，默认 `08_publish/manifest/<book>_manifest.json`。
- `--format table|json`：默认 `table`。
- `--dry-run`：只显示摘要，不写 manifest JSON。
- `--force`：覆盖已有 manifest JSON。

输出：

- clean Markdown、metadata JSON 和可选封面图片的路径、存在状态、大小和 SHA256。
- 组合后的发布包 manifest。
- 缺 clean Markdown 或 metadata JSON 时输出审计问题。
- metadata JSON 无法解析时输出审计问题。

失败：

- 输入 `path` 不存在或不是目录。
- 输出文件已存在且未传 `--force`。

### `fictionops export-epub`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认发布路径。
- `--manifest-file`：指定 publish manifest JSON；相对路径解析到 `path` 内部。
- `--clean-file`：指定 clean Markdown 文件；相对路径解析到 `path` 内部。
- `--metadata-file`：指定 metadata JSON 文件；相对路径解析到 `path` 内部。
- `--cover-file`：可选封面图片；相对路径解析到 `path` 内部，并覆盖 manifest 或 metadata 中的 `cover_image`。
- `--out`：输出路径，默认 `08_publish/epub/<book>.epub`。
- `--format table|json`：默认 `table`。
- `--dry-run`：只显示摘要，不写 EPUB。
- `--force`：覆盖已有 EPUB。

输出：

- 读取的 manifest、clean Markdown 和 metadata JSON 路径。
- EPUB 输出路径、章节数、基础字数统计和封面状态。
- 缺 clean Markdown、metadata JSON 或 manifest 时输出审计问题。
- 生成的 EPUB 必须包含 `mimetype`、`META-INF/container.xml`、`OEBPS/content.opf`、`OEBPS/nav.xhtml`、默认 CSS 和章节 XHTML；有封面时还必须包含封面页和封面图片。

失败：

- 输入 `path` 不存在或不是目录。
- 输出文件已存在且未传 `--force`。

### `fictionops audit-epub`

输入：

- `path`：目标 FictionOps 项目目录或 EPUB 文件，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认发布路径。
- `--file`：指定 EPUB 文件；相对路径解析到 `path` 内部。
- `--manifest-file`：指定 publish manifest JSON；相对路径解析到 `path` 内部。
- `--clean-file`：指定 clean Markdown 文件；相对路径解析到 `path` 内部。
- `--metadata-file`：指定 metadata JSON 文件；相对路径解析到 `path` 内部。
- `--format table|json`：默认 `table`。

输出：

- EPUB 路径、存在状态、结构有效性和过期状态。
- mimetype、container、OPF、nav、CSS、章节 XHTML、封面页和封面图片检查结果。
- 缺 EPUB、坏 zip、缺必需结构、封面声明损坏或早于输入文件时输出审计问题。

失败：

- 输入 `path` 不存在。
- 审计命令不写文件，也不覆盖任何发布物。

### `fictionops release-gate`

输入：

- `path`：目标 FictionOps 项目目录，默认当前目录。
- `--book`：书号，默认 `book_01`，用于推导默认发布路径。
- `--min-chapter-chars`：传给 clean Markdown 发布稿审计，默认 `200`。
- `--out`：写入最终发布门禁报告路径；相对路径解析到 `path` 内部。
- `--dry-run`：构建报告但不写 `--out`。
- `--force`：覆盖已有输出文件。
- `--format markdown|json`：默认 `markdown`。

输出：

- 聚合 `book-gate`、`audit-publish`、`export-metadata`、`export-manifest` 和 `audit-epub` 的发布链尾端信号。

### `fictionops audit-release-evidence`

输入：

- `path`：仓库根目录或证据文件，默认当前目录。
- `--file`：指定 release evidence Markdown；相对路径解析到 `path` 内部。
- `--format markdown|json`：默认 `markdown`。

契约：

- 只读，不写文件。
- 区分空模板、workflow 自动生成但未复核的草稿、`deferred`、`failed` 和可验收的 `accepted` 证据。
- `accepted` 只有在 GitHub Actions run URL、run ID、wheel/sdist hash、具名复核人、安装烟测结果等关键字段填实且无阻塞问题时才可返回 `ready=true`。
- Date 必须是 `YYYY-MM-DD` 或 `YYYY-MM-DDTHH:MM:SSZ`；如果本地存在 `pyproject.toml`，Version 必须与项目版本一致，版本烟测结果必须包含该版本号。
- GitHub Actions run ID 必须是正整数；wheel filename 必须以 `.whl` 结尾，sdist filename 必须以 `.tar.gz` 结尾。
- 如果 `TestPyPI used: no`，必须记录跳过理由和接受人；如果 `TestPyPI used: yes`，必须记录 TestPyPI URL、发布结果和干净 venv 安装命令。
- built-wheel、`fictionops init` 和 `fictionops doctor` 的烟测结果必须明确显示通过；随便填写非通过文本不能关闭发布演练。
- 不调用模型，不写文件，不替代真实 GitHub Actions/TestPyPI/PyPI 外部证据。

失败：

- 证据路径是目录或不可读文件。

### `fictionops audit-dogfood-cycle`

输入：

- `path`：仓库根目录或 dogfood cycle evidence 文件，默认当前目录。
- `--file`：指定 dogfood cycle evidence Markdown；相对路径解析到 `path` 内部。
- `--format markdown|json`：默认 `markdown`。

契约：

- 只读，不写文件。
- 区分缺失记录、空模板、`deferred`、`failed` 和可验收的 `accepted` 周期。
- `accepted` 只有在周期字段填实、起止日期有效且结束日期不早于开始日期、至少覆盖 7 个自然日、至少覆盖三条命令路径、最终 adopt-review 状态 ready/complete、`import_queue_files=0`、`blocking_issue_count=0` 且兼容性/恢复说明存在时才可返回 `ready=true`。
- 不调用模型，不修改 dogfood 项目，不替代真实持续维护周期。

失败：

- 证据路径是目录或不可读文件。

### `fictionops audit-stability-window`

Input:
- `path`: repository root or stability window evidence Markdown file, default current directory.
- `--file`: specific stability window evidence Markdown file; relative paths resolve inside `path`.
- `--format markdown|json`: default `markdown`.

Contract:
- Read-only; writes no files.
- Distinguishes missing records, empty templates, `deferred`, `failed`, and verifiable `accepted` stability-window records.
- `accepted` returns `ready=true` only when window id, valid date range with end date not earlier than start date and at least 7 calendar days covered, version range, concrete release/dogfood evidence file/run/artifact references, compatibility notes, breaking-change notes, recovery notes, and decision are filled. Local Markdown release/dogfood references must exist and pass their own evidence audits.
- It does not replace real elapsed use; it only audits the written evidence after that window has happened.

Failure:
- Evidence path is a directory or unreadable file.

### `fictionops audit-stable-core`

输入：

- `path`：仓库根目录，默认当前目录。
- `--release-file`：指定 release evidence Markdown；相对路径解析到 `path` 内部。
- `--dogfood-file`：指定 dogfood cycle evidence Markdown；相对路径解析到 `path` 内部。
- `--stability-file`：指定 stability window evidence Markdown；相对路径解析到 `path` 内部。
- `--format markdown|json`：默认 `markdown`。

契约：

- 只读，不写文件。
- 聚合本地治理文件、发布证据、持续 dogfood 周期、稳定窗口证据、`stable-core-audit.md` 声明和 `milestone-status.md` 声明。
- `ready=true` 只有在 release evidence、dogfood cycle、stability window 都已 `accepted`，本地治理文件齐全，且稳定核心文档与里程碑账本都已标记完成时才可返回。
- JSON 输出包含结构化 `action_items`，列出剩余 1.0 证据线的证据文件、验收命令和完成标准。
- 当前本地测试、空模板、`deferred` 记录或未复核 workflow 草稿都不能关闭 1.0。

失败：

- `path` 不存在或不是目录。
- 任一指定证据路径是目录或不可读文件。

## 7. 帮助文案契约

- 根命令 `fictionops --help` 必须列出全部 56 个 MVP 命令。
- 每个子命令必须支持 `fictionops <command> --help`。
- 帮助文案应说明默认值、是否写文件、是否覆盖、路径如何解析。

## 8. 变更规则

修改 CLI 时：

1. 先更新本文件。
2. 再更新 `docs/cli.zh-CN.md` 中面向用户的说明。
3. 补核心函数测试和 CLI 子进程测试。
4. 如果新增写入行为，确认默认不覆盖。
5. 如果新增 JSON 输出，确认测试中用 `json.loads` 解析。
## 附录：`fictionops adopt --copy-to` 契约

`fictionops adopt <old-project> --copy-to <new-project>` 在普通诊断报告之外，增加一个保守迁移沙盒动作：

- `<old-project>` 仍然只读，不会被修改。
- `<new-project>` 必须是已经由 `fictionops init` 初始化、且存在 `project.yml` 的 FictionOps 项目。
- `<new-project>` 不能位于 `<old-project>` 内部，避免扫描源目录时把迁移产物重新吞进去。
- 复制目标来自每个候选文件的 `suggested_target_path`。
- 同一轮复制中如果多个源文件映射到同一目标路径，必须生成带源路径上下文和短 hash 的唯一目标路径，不能跳过候选材料。
- 已有目标文件默认跳过；传入 `--force` 才覆盖。
- `--dry-run` 只记录计划复制项，不写入任何文件。
- 实际复制后必须写出 `00_management/adopted_handoff/adopt_manifest.json`，记录源路径、目标路径和复制状态，供后续导入整理使用。
- JSON/Markdown 报告新增 `copy_to`、`copied_files`、`skipped_files`、`planned_copies` 和 `copy_files`。
## 追加契约：`fictionops adopt-review`

`fictionops adopt-review <project>` 用于复查 `adopt --copy-to` 之后的迁移沙盒。

输入：
- `path`：已初始化的 FictionOps 迁移沙盒，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--pattern`：底层审计使用的 Markdown glob，默认 `**/*.md`。
- `--min-chapter-chars`：短章/占位章阈值，默认 `200`。
- `--max-issues`：报告中展开的迁移复查问题数量上限，默认 `80`。
- `--out`、`--force`、`--dry-run`、`--format markdown|json` 遵循通用写报告契约。

输出：
- 聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`。
- 输出 `status`、`ready`、`migration_files`、`import_queue_files`、`issue_count`、`blocking_issue_count`、`checks`、`issues` 和 `next_actions`。
- 如果 `06_drafts/import_queue/` 仍有导入正文，状态必须偏向 `needs_import_sorting`，不能把迁移沙盒误判为完成。
- JSON 输出必须保持纯 JSON，不能混入“已写入报告”之类的人读提示。

## 追加契约：`fictionops adopt-plan`

`fictionops adopt-plan <project>` 用于把 `adopt-review` 的迁移复查问题转成按优先级排序的整改任务。

输入：
- `path`：已经初始化的 FictionOps 迁移沙盒，默认当前目录。
- `--book`：书号，默认 `book_01`。
- `--pattern`：底层审计使用的 Markdown glob，默认 `**/*.md`。
- `--min-chapter-chars`：短章/占位章阈值，默认 `200`。
- `--max-issues`：最多从 `adopt-review` 转换多少条问题为任务，默认 `200`。
- `--write-groups <dir>`：把每个 `task_groups` 修复组写成独立 Markdown 工作文件，并在目录内生成 `index.md`。相对路径解析在 `path` 内。
- `--out`、`--force`、`--dry-run`、`--format markdown|json` 遵循通用写报告契约。

输出：
- 复用 `adopt-review` 的判断，输出 `review_status`、`review_ready`、`task_count`、`priority_counts`、`task_groups`、`group_output_dir`、`group_files_written`、`group_files`、`tasks`、`next_actions` 和 `adopt_review`。
- `task_groups` 必须按修复阶段折叠同类任务，包含 `phase`、`priority`、`code`、`count`、`blocking_count`、`areas`、`source_commands`、`sample_subjects`、`sample_paths` 和 `suggested_action`，用于在大量迁移问题中先判断修复顺序。
- `--write-groups` 不应修改正文或正史文件，只能写入修复组工作文件；默认不覆盖已有文件，`--force` 才能覆盖。
- `tasks` 必须包含 `priority`、`area`、`source_command`、`code`、`chapter`、`path`、`message` 和 `suggested_action`。
- 如果 `adopt-review` 发现 `import_queue_unsorted`，`adopt-plan` 必须生成对应迁移任务，提示先把导入正文归入书/章目录。
- JSON 输出必须保持纯 JSON；Markdown 写出默认不覆盖已有文件。

## 追加契约：`fictionops import-plan`

`fictionops import-plan <project>` 用于整理迁移沙盒里的 `06_drafts/import_queue/`。它默认只生成计划；只有传入 `--apply` 时才会移动文件。若存在 `00_management/adopted_handoff/adopt_manifest.json`，它必须优先利用 manifest 中的旧源路径辅助推断书号。

输入：
- `path`：已经初始化的 FictionOps 迁移沙盒，默认当前目录。
- `--book`：无法从路径推断书号时使用的兜底书号，默认 `book_01`。
- `--max-files`：详细列出的导入文件数量，摘要计数仍覆盖全部导入队列。
- `--apply`：只移动无歧义、目标文件不存在的导入正文。
- `--create-scaffolds`：仅与 `--apply` 配合时生效，为已移动章节补齐缺失的章节发动机和逐章复盘，且不得覆盖已有文件。
- `--replace-placeholder-targets`：仅与 `--apply` 配合时生效，只替换仍像生成模板的已存在章节目标；真实已有正文必须继续保留为人工复查。
- `--out`、`--force`、`--dry-run`、`--format` 遵守通用输出契约。

输出：
- 报告必须包含 `import_queue_files`、`ready_count`、`needs_review_count`、`target_exists_count`、`placeholder_target_count`、`duplicate_target_count`、`moved_files`、`replaced_placeholder_targets`、`create_scaffolds`、`replace_placeholder_targets`、`scaffold_created_files`、`scaffold_skipped_files`、`scaffold_planned_actions`、`items` 和 `next_actions`。
- 每个 `items` 条目必须包含 `source_path`、`inferred_book`、`inferred_chapter`、`title`、`target_path`、`status`、`scaffold_status`、`confidence`、`reason` 和 `nonspace_chars`。
- 缺少章号、目标已存在或目标重复的条目必须进入人工复查状态，不能被 `--apply` 自动移动。
- `placeholder_target` 条目只有在传入 `--replace-placeholder-targets` 时才能移动；移动后状态应变为 `replaced_placeholder_target`。
- `--dry-run --apply` 只能报告将要移动的文件和计划生成的配套文件，不得修改文件系统。
- JSON 输出必须保持纯 JSON；Markdown 写出默认不覆盖已有文件。

## FictionOps 源码包 controller 契约

当 `agent-next` 或 `audit-agent-workflow --level controller` 的目标是 FictionOps 源码包 checkout 本身时，命令应进入 package governance 模式，而不是把仓库当成待迁移小说项目。JSON evidence 应暴露 `fictionops_package`、`agent_next_selected_stage`、`stable_core_status` 等字段；若下一步涉及外部发行证据、持续 dogfood 证据或稳定窗口证据，状态应停在 `needs_human_review`，controller 不得自动执行或伪造这些证据。
