from __future__ import annotations

PROJECT_DIRS = [
    "00_management",
    "01_story_seed",
    "02_world",
    "03_characters/character_arcs",
    "04_structure/volume_outlines",
    "04_structure/book_outlines",
    "04_structure/act_pressure_chains",
    "05_canon",
    "06_drafts/book_01/chapters",
    "06_drafts/book_01/chapter_engines",
    "06_drafts/book_01/draft_briefs",
    "06_drafts/book_01/revision_notes",
    "07_audits/continuity",
    "07_audits/character_arc",
    "07_audits/style",
    "07_audits/pacing",
    "07_audits/post_draft",
    "07_audits/review_gate",
    "07_audits/book_gate",
    "07_audits/release_gate",
    "07_audits/book_retrospectives",
    "08_publish/clean_markdown",
    "08_publish/epub",
    "08_publish/synopsis",
    "08_publish/metadata",
    "08_publish/manifest",
    "99_archive/old_outlines",
    "99_archive/deprecated_canon",
    "99_archive/abandoned_scenes",
]


TEMPLATE_COPIES = {
    "project.yml": "project.yml",
    "story_seed.zh-CN.md": "01_story_seed/story_seed.md",
    "character_arc.zh-CN.md": "03_characters/character_arcs/character_arc_template.md",
    "book_outline.zh-CN.md": "04_structure/book_outlines/book_01_outline.md",
    "chapter_engine.zh-CN.md": "06_drafts/book_01/chapter_engines/ch_001_engine.md",
    "information_release_table.zh-CN.md": "05_canon/information_release_table.md",
    "foreshadowing_echo_table.zh-CN.md": "05_canon/foreshadowing_echo_table.md",
    "book_retrospective.zh-CN.md": "07_audits/book_retrospectives/book_01_retrospective.md",
    "style_audit.zh-CN.md": "07_audits/style/style_audit_template.md",
    "publish_checklist.zh-CN.md": "08_publish/publish_checklist.md",
    "handoff_log.zh-CN.md": "00_management/handoff_log.md",
}

DEFAULT_WATCH_TERMS = [
    "不是",
    "没有",
    "无人",
    "有人",
    "所有人",
    "每个人",
    "忽然",
    "突然",
    "其实",
    "真正",
    "原来",
    "只是",
    "也许",
    "仿佛",
    "像是",
    "因为",
    "所以",
    "仍然",
]

STANDARD_PROJECT_FILES = [
    ("project.yml", "required"),
    ("00_management/current_context.md", "recommended"),
    ("00_management/handoff_log.md", "recommended"),
    ("00_management/decision_log.md", "recommended"),
    ("01_story_seed/story_seed.md", "required"),
    ("03_characters/character_index.md", "recommended"),
    ("03_characters/intelligence_profiles.md", "recommended"),
    ("04_structure/series_outline.md", "recommended"),
    ("04_structure/timeline.md", "recommended"),
    ("05_canon/information_release_table.md", "required"),
    ("05_canon/foreshadowing_echo_table.md", "required"),
    ("05_canon/object_locations.md", "recommended"),
    ("05_canon/open_questions.md", "recommended"),
]

PLACEHOLDER_MARKERS = [
    "Draft starts here",
    "Untitled Novel",
    "|  |",
    "- 当前卷：",
    "- 最新大纲：",
    "未开始 / 进行中 / 完成",
    "暂不判断：",
]

ECHO_TABLE_NAME_MARKERS = [
    "foreshadowing",
    "echo",
    "伏笔",
    "回声",
]

INFO_TABLE_NAME_MARKERS = [
    "information_release",
    "information-release",
    "information",
    "secret",
    "info",
    "信息",
    "秘密",
    "释放",
]


STARTER_FILES = {
    "README.md": """# {title}

This project was initialized with FictionOps.

Start here:

1. Fill `01_story_seed/story_seed.md`.
2. Define the first book in `04_structure/book_outlines/book_01_outline.md`.
3. Track secrets in `05_canon/information_release_table.md`.
4. Plan chapter 1 in `06_drafts/book_01/chapter_engines/ch_001_engine.md`.
5. Draft chapters in `06_drafts/book_01/chapters/`.
""",
    "00_management/current_context.md": """# 当前上下文

## 当前目标


## 当前状态

- 当前卷：
- 当前本：
- 当前章节：
- 最新大纲：
- 最新正史：

## 下一步

1.
2.
3.

## 风险

- 
""",
    "00_management/decision_log.md": """# 决策记录

| 日期 | 决策 | 原因 | 影响文件 |
| --- | --- | --- | --- |
|  |  |  |  |
""",
    "00_management/workflow.md": """# 工作流

默认流程：

1. 故事种子；
2. 世界与人物承重梁；
3. 书级大纲；
4. 章节发动机；
5. 正文；
6. 章节审计；
7. 书级复盘；
8. 清稿发布。
""",
    "00_management/glossary.md": """# 术语表

| 术语 | 含义 | 首次出现 | 备注 |
| --- | --- | --- | --- |
|  |  |  |  |
""",
    "02_world/world_rules.md": """# 世界规则

## 作者真相


## 世界内部版本

| 群体/地区 | 他们相信的版本 | 政治或叙事功能 |
| --- | --- | --- |
|  |  |  |
""",
    "02_world/factions.md": """# 势力

| 势力 | 目标 | 资源 | 恐惧 | 公开说法 | 私下做法 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
""",
    "02_world/naming_rules.md": """# 命名规则

## 人名


## 地名


## 制度名


## 禁用或慎用风格

- 
""",
    "02_world/regional_voices.md": """# 地域与身份口吻

| 地区/阶层/职业 | 词汇倾向 | 句式倾向 | 不该说的话 | 代表人物 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "03_characters/character_index.md": """# 人物索引

| 人物 | 身份 | 首次出现 | 当前状态 | 弧线文件 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "03_characters/intelligence_profiles.md": """# 人物智慧模式

| 人物 | 看得快的东西 | 容易错过的东西 | 解决方式 | 失败方式 | 口吻 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
""",
    "03_characters/voice_profiles.md": """# 人物口吻

| 人物 | 说话节奏 | 常用判断方式 | 不会说的话 | 紧张时动作 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "03_characters/relationship_map.md": """# 关系图

| A | B | 起点关系 | 当前关系 | 未说出口的东西 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "04_structure/series_outline.md": """# 系列总纲

## 一句话


## 长线问题

1.
2.
3.

## 卷结构

| 卷 | 功能 | 进入状态 | 离开状态 |
| --- | --- | --- | --- |
|  |  |  |  |
""",
    "04_structure/timeline.md": """# 时间线

| 时间 | 事件 | 公开版本 | 私人真相 | 影响 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "05_canon/object_locations.md": """# 物件位置

| 物件 | 当前所在 | 上次出现 | 意义变化 | 下一次处理 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "05_canon/open_questions.md": """# 未解问题

| 问题 | 类型 | 当前状态 | 预计处理 |
| --- | --- | --- | --- |
|  | 剧情 / 设定 / 人物 / 信息边界 |  |  |
""",
    "05_canon/resolved_questions.md": """# 已解决问题

| 问题 | 结论 | 决策日期 | 影响文件 |
| --- | --- | --- | --- |
|  |  |  |  |
""",
    "06_drafts/book_01/chapters/ch_001.md": """# 第001章

> Draft starts here.
""",
}
