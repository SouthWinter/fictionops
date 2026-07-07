# FictionOps Dogfood：既有长篇项目 adopt 迁移报告

> 本报告记录一次真实长篇写作目录的只读迁移诊断。它不摘录正文和大纲内容，只记录工具行为、分层结果、风险和改进结论。

## 1. 目标

本次 dogfood 的目标是验证 `fictionops adopt` 能否接住一个已经写了大量正文、大纲、设定、复盘和发布材料的长篇项目，而不是只服务新建的标准 FictionOps 项目。

验证问题：

- 旧目录没有 `project.yml` 时，工具能否给出迁移路线，而不是直接失败。
- 混合目录，例如“总纲与管理”，是否会导致错误分层。
- 正文、书纲、人物、设定、信息释放、伏笔回声、发布材料和归档材料能否被分开。
- 工具是否坚持只读，不创建、不搬移、不改写源项目。

## 2. 运行命令

在长篇项目根目录运行：

```bash
python fictionops/src/fictionops/cli.py adopt . --max-files 0 --format json
```

`--max-files 0` 用于只看汇总，不在报告里列出具体文件清单。

## 3. 扫描结果

| 指标 | 结果 |
| --- | ---: |
| 扫描候选文件 | 169 |
| 默认忽略文件 | 68 |
| 非空白字符总量 | 2,134,535 |

分层结果：

| FictionOps 层级 | 文件数 | 非空白字符 |
| --- | ---: | ---: |
| `management` | 5 | 105,899 |
| `world` | 13 | 82,752 |
| `characters` | 17 | 116,077 |
| `structure` | 16 | 203,487 |
| `canon` | 6 | 24,378 |
| `drafts` | 102 | 906,540 |
| `audits` | 3 | 30,527 |
| `publish` | 3 | 581,098 |
| `archive` | 4 | 83,777 |

工具发现的主要风险：

- `P2 missing_project_config`：项目根目录没有 FictionOps `project.yml`。这是预期结果，因为该目录是被迁入对象，不是标准 FictionOps 项目。
- `P4 archive_present`：存在归档/旧稿材料。迁移时应保持隔离，避免旧设定污染当前正史。

## 4. Dogfood 中暴露的问题

初次扫描时，`adopt` 把部分“接手日志”“当前摘要”等管理文件误归到 `structure`。原因不是文件名，而是父目录名包含“总纲”，旧规则使用完整相对路径做关键词判断，混合目录会把子文件带偏。

这暴露了一个真实作者目录常见问题：旧项目目录名经常是复合桶，例如：

- 总纲与管理
- 设定与资料
- 正文与修订
- 发布与归档

如果工具直接相信父目录，会把文件分层做得过于武断。

## 5. 已做修正

`adopt` 的分类规则已调整为：

1. 归档、发布、复盘等强目录信号仍可优先识别。
2. 具体文件名线索优先于父目录线索。
3. 父目录只做兜底判断。
4. 新增回归测试，确保混合目录中的“当前接手摘要”归入 `management`，而不是被“总纲”误判为 `structure`。
5. `adopt` 报告新增 `migration_phase` 与 `suggested_target_path`，为人工迁移提供目标路径参考，但仍不自动复制或移动文件。

修正后再次扫描，`management` 从 1 个文件提升到 5 个，`structure` 从 20 个文件降到 16 个，分布更贴近真实项目结构。

## 6. 迁移建议

本项目适合按“先复制骨架，再分层迁移”的方式进入 FictionOps：

1. 在新目录运行 `fictionops init <new-project>`，不要直接在旧项目根目录上改造。
2. 把接手摘要、协作工作流、目录说明和统计类材料迁入 `00_management/`。
3. 把信息释放、伏笔回声、时间线、路线和物件状态迁入 `05_canon/`。
4. 把人物弧线、智慧模式、口吻资料和关系材料迁入 `03_characters/`。
5. 把卷纲、书纲、幕结构和桥表迁入 `04_structure/`。
6. 把正文按书拆入 `06_drafts/<book>/chapters/`，再用 `new-book`、`new-chapter`、`plan-chapter` 建齐发动机和复盘入口。
7. 把旧稿、废案、过期设定和历史大纲迁入 `99_archive/`，迁入后默认不参与写作上下文。
8. 发布稿、简介、标签、清稿和 EPUB 材料迁入 `08_publish/`，不要和正文草稿混放。

## 7. 对 FictionOps 的结论

`adopt` 已经可以作为真实长篇迁移的第一步，但它仍应被视为诊断工具，而不是自动整理工具。

当前报告已经给出建议目标路径。下一步仍不应该让它自动搬文件。更合理的方向是：

- 支持项目自定义关键词映射，例如把某些专有文件名固定到指定层。
- 在 `context-pack` 中优先读取 `adopt` 报告，避免 Agent 在迁移早期误吞旧稿。
- 增加“迁移后复查”命令或文档流程：确认旧材料进入 FictionOps 后，`doctor`、`audit-info`、`audit-characters` 和 `book-gate` 能否接着工作。

本次 dogfood 证明：FictionOps 0.1.0 不只适合新项目初始化，也能为已经膨胀到百万字级的旧项目提供可维护入口。
## 8. 追加：迁移沙盒能力

基于本次 dogfood 暴露的问题，`adopt` 已从“只给建议路径”推进到“可复制到独立沙盒”：

```bash
fictionops init migrated-novel --title "迁移沙盒"
fictionops adopt . --copy-to migrated-novel --format json
```

这个能力仍然不修改源项目，也不尝试替作者判断哪些版本是最终版本。它只是把扫描到的候选文件按 `suggested_target_path` 复制到一个已经初始化的 FictionOps 项目中，方便后续人工整理、归档、合并和门禁复查。

下一步的真实 dogfood 不应直接覆盖示例长篇工作目录，而应先复制到沙盒，再观察 `doctor`、`audit-info`、`audit-characters` 和 `book-gate` 对迁移后结构的反馈。

`adopt-review` 已把这一步固化成命令：

```bash
fictionops adopt-review migrated-novel --book book_01 --format json
```

`adopt-plan` 则把复查结果继续转成整改清单：

```bash
fictionops adopt-plan migrated-novel --book book_01 --out 07_audits/adopt_review/plan.md
```

`import-plan` 可以继续把 `06_drafts/import_queue/` 拆成逐文件整理建议；默认不移动文件，传入 `--apply` 时也只移动无歧义、目标不存在的正文：

```bash
fictionops import-plan migrated-novel --book book_01 --out 07_audits/adopt_review/import_plan.md
```

它不会替作者整理材料，但会指出导入队列、信息边界、人物资料和书级收束中哪些问题还阻止沙盒进入常规 FictionOps 工作流。

## 9. 追加：真实迁移沙盒复跑

复跑日期：2026-07-06

本次复跑使用外部沙盒目录，不在示例长篇源目录内写入任何文件：

```bash
fictionops init ../legacy_fictionops_migration_sandbox_dogfood --title "示例长篇迁移沙盒"
fictionops adopt . --copy-to ../legacy_fictionops_migration_sandbox_dogfood --max-files 300 --format json
fictionops adopt-review ../legacy_fictionops_migration_sandbox_dogfood --book book_01 --max-issues 200 --format json
fictionops adopt-plan ../legacy_fictionops_migration_sandbox_dogfood --book book_01 --max-issues 200 --format json
fictionops import-plan ../legacy_fictionops_migration_sandbox_dogfood --book book_01 --format json
```

复跑结果：

| 指标 | 结果 |
| --- | ---: |
| 扫描候选文件 | 169 |
| 默认忽略文件 | 69 |
| 非空白字符总量 | 2,134,535 |
| 复制到沙盒文件 | 169 |
| 跳过文件 | 0 |
| 自动消歧同名目标 | 5 |
| adopt manifest | 已生成 |
| 迁移复查状态 | `needs_import_sorting` |
| 迁移复查是否 ready | false |
| 迁移文件 | 169 |
| `06_drafts/import_queue/` 文件 | 102 |
| `import-plan` ready | 101 |
| `import-plan` 需人工复查 | 1 |
| `import-plan` 目标已存在 | 1 |
| `import-plan` 重复目标 | 0 |
| 复查问题 | 92 |
| 阻塞问题 | 30 |
| 整改任务 | 92 |

本轮 dogfood 暴露了一个真实问题：旧项目中多个文件会映射到相同建议路径，例如不同书册中的 `人物出场记录.md`、多个信息释放表、多个 `README.md`。旧实现会产生 `skipped_collision`，这意味着候选材料可能没有进入沙盒。

已修正为：`adopt --copy-to` 在同一轮复制中遇到建议目标路径碰撞时，不再跳过文件，而是在原目标文件名后追加源路径上下文和短 hash，生成唯一目标路径。复跑后 169 个候选文件全部进入沙盒，5 个碰撞文件被自动消歧。

这条修正对应新增回归测试：`test_adopt_copy_disambiguates_same_target_paths`。

迁移复查仍然显示 `needs_import_sorting` 是合理结果：102 个正文类文件仍停留在 `06_drafts/import_queue/`，说明沙盒只是完成了“安全复制”，还没有完成“归入书/章结构”。`adopt-plan` 已能把这一点转成优先级任务，`import-plan` 则能利用 `adopt_manifest.json` 中的旧源路径继续给出逐文件整理建议。本次复跑中，102 个导入正文里 101 个被判为可安全移动，0 个重复目标，1 个因目标已存在保留人工复查。

这个结果说明：导入队列整理不能只看复制后的文件名。真实长篇里多本书都会有 `ch_001.md`、`第1章` 之类的正文，若丢失旧源路径，就会把不同书的章节误判为同一本的重复目标。`adopt_manifest.json` 把旧路径作为迁移证据保留下来，正好补上了这层上下文。

## 10. 追加：导入队列应用与配套文件生成

为了验证迁移链路不止停在“计划”，本轮又在外部临时沙盒中执行：

```bash
fictionops import-plan ../legacy_fictionops_apply_scaffold_sandbox_dogfood --book book_01 --apply --create-scaffolds --format json
```

执行结果：

| 指标 | 结果 |
| --- | ---: |
| 应用前 `06_drafts/import_queue/` 文件 | 102 |
| 应用前 ready | 101 |
| 移动正文 | 101 |
| 生成章节发动机/逐章复盘文件 | 202 |
| 跳过已存在正文文件 | 101 |
| 应用后 `06_drafts/import_queue/` 文件 | 1 |
| 应用后 ready | 0 |
| 应用后需人工复查 | 1 |
| 应用后 `adopt-review` 状态 | `needs_import_sorting` |

这里 `adopt-review` 仍然是 `needs_import_sorting`，因为还剩 1 个目标已存在的导入正文需要人工判断。生成 202 个配套文件后，审计问题数会上升，这是预期结果：原先隐性的“没有章节发动机/逐章复盘”被转成了显性的待填写维护入口。迁移链路的意义不是自动完成文学判断，而是把旧材料安全放进可维护结构。

## 11. 追加：占位目标替换后清空导入队列

上一步剩余的 1 个 `target_exists` 来自初始化项目自带的占位章节目标。为避免误覆盖真实正文，`import-plan` 新增显式选项 `--replace-placeholder-targets`：它只替换仍像生成模板的章节目标，真实已有正文仍会保留为人工复查。

本轮在外部临时沙盒中执行：

```bash
fictionops import-plan ../legacy_fictionops_replace_placeholder_sandbox_dogfood --book book_01 --apply --create-scaffolds --replace-placeholder-targets --format json
```

执行结果：

| 指标 | 结果 |
| --- | ---: |
| 应用前 `06_drafts/import_queue/` 文件 | 102 |
| 应用前 ready | 101 |
| 应用前占位目标 | 1 |
| 移动正文 | 102 |
| 替换占位目标 | 1 |
| 生成章节发动机/逐章复盘文件 | 203 |
| 跳过已存在正文或配套文件 | 103 |
| 应用后 `06_drafts/import_queue/` 文件 | 0 |
| 应用后需人工复查 | 0 |
| 应用后 `adopt-review` 状态 | `needs_migration_fixes` |
| 应用后 `adopt-review` 导入队列文件 | 0 |
| 应用后复查问题 | 530 |
| 应用后阻塞问题 | 29 |

这说明迁移链路已经能完成从“旧项目安全复制”到“导入正文进入书/章结构”的状态转移：`needs_import_sorting` 被解除，后续问题进入 `needs_migration_fixes`，也就是信息边界、人物资料、章节发动机、逐章复盘等维护内容的补全阶段。

## 迁移修复组复跑

清空导入队列后，`adopt-plan --max-issues 2000 --format json` 会把 530 条迁移任务折叠为 16 个修复组，避免真实长篇项目在表格空行、脚手架占位和重复来源上产生噪音。

继续传入 `--write-groups 07_audits/adopt_review/repair_groups` 后，工具会把这些修复组落成可交接的 Markdown 工作文件：

| 指标 | 数值 |
| --- | ---: |
| `adopt-plan` 任务总数 | 530 |
| `task_groups` 修复组 | 16 |
| 写出的修复组 Markdown 文件 | 17 |
| `index.md` | 已生成 |
| 复查状态 | `needs_migration_fixes` |

最前面的修复组显示，当前真正需要先处理的是正史/伏笔边界，而不是逐条清理表格空行：

| Phase | Code | Count | Blocking |
| --- | --- | ---: | ---: |
| `01_migration_shape` | `placeholder_standard_project_files` | 1 | 0 |
| `02_canon_boundaries` | `missing_first_plant` | 21 | 21 |
| `02_canon_boundaries` | `no_information_items` | 8 | 8 |
| `03_character_memory` | `missing_character_arcs` | 2 | 0 |
| `04_book_structure` | `unplanned_chapter_file` | 32 | 0 |
| `05_table_hygiene` | `mostly_empty_row` | 226 | 0 |
| `05_table_hygiene` | `no_filled_cells` | 226 | 0 |

## 12. 追加：0.2 收口复跑与 waiver 记录

为了把 0.2 迁移 dogfood 从“导入队列已清空”继续推进到可验收状态，本轮新建外部沙盒：

```text
C:\Users\z\Documents\story\legacy_fictionops_02_closure_sandbox
```

复跑命令：

```bash
fictionops init ../legacy_fictionops_02_closure_sandbox --title "示例长篇迁移收口沙盒"
fictionops adopt . --copy-to ../legacy_fictionops_02_closure_sandbox --max-files 300 --format json
fictionops adopt-review ../legacy_fictionops_02_closure_sandbox --book book_01 --max-issues 200 --format json
fictionops import-plan ../legacy_fictionops_02_closure_sandbox --book book_01 --apply --create-scaffolds --replace-placeholder-targets --format json
fictionops adopt-review ../legacy_fictionops_02_closure_sandbox --book book_01 --max-issues 2000 --format json
fictionops adopt-plan ../legacy_fictionops_02_closure_sandbox --book book_01 --max-issues 2000 --write-groups 07_audits/adopt_review/repair_groups --format json
```

导入后复查仍有 29 个 blocking issue，集中在两类信息边界问题：

| Code | Count | Meaning |
| --- | ---: | --- |
| `missing_first_plant` | 21 | 已导入伏笔/回声材料，但缺少可信的首次埋设位置。 |
| `no_information_items` | 8 | 已导入信息释放文件，但部分表格尚未归一成标准信息表行。 |

这些不是导入失败，而是人工正史归一问题。为了让迁移里程碑不把“仍需作者判断”误判成“迁移链路未完成”，沙盒中新增：

```text
07_audits/adopt_review/waivers.json
07_audits/adopt_review/dogfood_decisions.md
```

`waivers.json` 只延期三类明确阻塞：

- `book-gate / missing_first_plant`
- `audit-info / no_information_items`
- `book-gate / no_information_items`

延期理由是：旧材料已经进入 FictionOps 结构，但首次埋设位置和信息释放表行需要作者在正史归一阶段判断，不能由迁移工具自动编造。

加入 waiver 后复跑：

```bash
fictionops adopt-review ../legacy_fictionops_02_closure_sandbox --book book_01 --max-issues 2000 --format json
fictionops adopt-plan ../legacy_fictionops_02_closure_sandbox --book book_01 --max-issues 2000 --write-groups 07_audits/adopt_review/repair_groups_after_waivers --format json
```

最终结果：

机器可检索摘要：`ready: true`，`import_queue_files: 0`，`blocking_issue_count: 0`，`waived_issue_count: 31`。

| Metric | Result |
| --- | ---: |
| `adopt-review` status | `migration_notes` |
| `ready` | `true` |
| `import_queue_files` | `0` |
| `blocking_issue_count` | `0` |
| `waived_issue_count` | `31` |
| active issue count | `501` |
| `adopt-plan` task count | `501` |
| repair groups after waivers | `14` |
| blocking repair groups | `0` |

结论：0.2 迁移 dogfood 已经证明真实长篇可以从旧材料复制、导入队列整理，推进到没有迁移阻塞的常规 FictionOps 项目工作状态。剩余问题仍然存在，但已经从“迁移阻塞”降为“普通维护任务”或“明确延期的作者判断”。

这不等于小说内容已经整理完，也不等于信息释放表已经可直接用于写作；它只证明迁移工作流不会把旧材料困在不可维护状态里。
