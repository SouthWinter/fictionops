# FictionOps 项目结构说明

> 目标：让长篇小说项目在数十万字、数百万字、多人或 Agent 协作、反复修订以后，仍然知道“什么是正史、什么是草稿、什么是废案、什么是发布版”。

## 1. 最小可用结构

```text
my-novel/
  README.md
  project.yml

  00_management/
    current_context.md
    handoff_log.md
    decision_log.md
    workflow.md
    glossary.md
    model_config.json

  01_story_seed/
    story_seed.md

  02_world/
    world_rules.md
    factions.md
    naming_rules.md
    regional_voices.md

  03_characters/
    character_index.md
    character_arcs/
    intelligence_profiles.md
    voice_profiles.md
    relationship_map.md

  04_structure/
    series_outline.md
    volume_outlines/
    book_outlines/
    act_pressure_chains/
    timeline.md

  05_canon/
    information_release_table.md
    foreshadowing_echo_table.md
    object_locations.md
    open_questions.md
    resolved_questions.md

  06_drafts/
    book_01/
      chapters/
      chapter_engines/
      draft_briefs/
      revision_notes/

  07_audits/
    continuity/
    character_arc/
    style/
    pacing/
    post_draft/
    review_gate/
    book_gate/
    release_gate/
    book_retrospectives/

  08_publish/
    clean_markdown/
    epub/
    synopsis/
    metadata/
    manifest/

  99_archive/
    old_outlines/
    deprecated_canon/
    abandoned_scenes/
```

如果项目还很小，可以先只建立：

- `project.yml`
- `00_management/current_context.md`
- `01_story_seed/story_seed.md`
- `03_characters/character_index.md`
- `04_structure/book_outlines/`
- `05_canon/information_release_table.md`
- `06_drafts/book_01/chapters/`
- `07_audits/post_draft/`
- `07_audits/review_gate/`
- `07_audits/book_gate/`
- `07_audits/release_gate/`
- `07_audits/book_retrospectives/`

## 2. 文件夹职责

| 目录 | 放什么 | 不放什么 |
| --- | --- | --- |
| `00_management` | 接手状态、工作流、决策记录、术语表、模型供应商配置 | 正文章节、临时灵感堆 |
| `01_story_seed` | 故事承诺、主题问题、读者体验、反目标 | 章节细纲 |
| `02_world` | 世界规则、势力、语言、命名、制度、神话版本 | 正文解释段 |
| `03_characters` | 人物弧线、智慧模式、口吻、关系图 | 某章具体写法 |
| `04_structure` | 系列、卷、书、幕、章节压力链、时间线 | 已废弃旧案 |
| `05_canon` | 信息释放、伏笔回声、物件位置、未解问题 | 新剧情草稿 |
| `06_drafts` | 正文草稿、章节发动机、写前任务单、修订笔记 | 发布版文件 |
| `07_audits` | 连续性、人物弧线、风格、节奏、写后关门报告、单章审稿门禁、书级收束门禁、最终发布门禁、书级复盘 | 未确认设定 |
| `08_publish` | 清稿、简介、标签、EPUB、发布元数据 | 写作过程文件 |
| `99_archive` | 旧大纲、废弃设定、弃稿 | 仍在使用的正史 |

## 3. 正史路由

修改一个设定时，按这个顺序同步：

1. **世界规则变了**：先改 `02_world`，再检查 `05_canon` 和相关书纲。
2. **人物终点变了**：先改 `03_characters`，再改 `04_structure`。
3. **某个秘密释放节奏变了**：先改 `05_canon/information_release_table.md`，再改章节发动机。
4. **正文写出了比大纲更好的事实**：先在章节修订笔记记录，再同步到大纲和正史表。
5. **旧设定废弃**：不要删除得无影无踪，移到 `99_archive/deprecated_canon/`，并在决策记录写原因。

## 4. Agent 读取顺序

Agent 不应该一次性吞完整项目。不同任务读取不同层：

实际交接时优先运行 `fictionops context-pack` 生成带体量预算的任务上下文包，再决定是否人工补充少量文件。

| 任务 | 必读 | 选读 |
| --- | --- | --- |
| 写一章正文 | 当前书纲、章节发动机、相关人物弧线、信息释放表、上一章正文 | 世界规则、伏笔表、风格审计 |
| 审一章正文 | 该章正文、章节发动机、上一章/下一章、信息释放表 | 人物口吻、伏笔表 |
| 修人物 | 人物弧线、已出场章节、关系图 | 书纲、复盘表 |
| 做书级复盘 | 全书章节、书纲、伏笔表、信息释放表 | 写作经验、读者体验审计 |
| 打包发布 | 清稿正文、元数据、简介、标签 | 字数统计、内容提示 |

## 5. 目录健康标准

一个 FictionOps 项目是健康的，应能快速回答：

1. 最新总纲在哪里？
2. 旧案在哪里，不会不会被误当正史？
3. 某个角色此刻知道什么？
4. 某个伏笔最后一次回声在哪章？
5. 某个物件现在在哪里？
6. 这一章为什么必须存在？
7. 发布版和草稿版有没有分开？
8. 新 Agent 接手时先读什么？

如果这些问题只能靠作者记忆回答，项目就还没有被真正维护起来。
