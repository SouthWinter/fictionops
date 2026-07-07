# 从故事种子到发布：FictionOps 工作流

> 这是一条默认路线。它不是要求作者按表格写小说，而是让每个阶段都有出口标准，避免长篇在后期被记忆、旧案和解释欲拖垮。

可以用 CLI 把这条路线转成可保存的阶段清单：

```bash
fictionops workflow-plan my-novel --stage all --out 00_management/workflow_plan.md
fictionops workflow-plan my-novel --stage review --chapter 003
fictionops workflow-plan my-novel --stage publish --book book_01
```

`workflow-plan` 只生成步骤、命令和出口标准，不会自动执行命令，也不会替作者做审美或剧情判断。

## 阶段 0：初始化项目

产出：

- `project.yml`
- `00_management/current_context.md`
- `00_management/handoff_log.md`
- `01_story_seed/story_seed.md`

出口标准：

- 项目语言、类型、状态明确。
- 能用三句话说清故事承诺。
- 明确故事拒绝变成什么。

## 阶段 1：建立承重梁

产出：

- 世界规则基础文件；
- 主要人物弧线；
- 系列/卷/书的不可逆事件；
- 核心秘密与信息释放表；
- 核心伏笔与回声表。

出口标准：

- 主要人物有各自的欲望、恐惧、智慧模式和失败模式。
- 作者真相、角色认知、公共谣言、官方版本被区分。
- 每本书至少知道“进入状态”和“离开状态”。

## 阶段 2：书级规划

产出：

- 书级大纲；
- 幕结构；
- 章节列表；
- 章节体量波形；
- 视角分配；
- 本书信息释放计划。

出口标准：

- 每章不是内容清单，而有压力、欲望、障碍、变化、余味。
- 章节长度允许波动，不为整齐而整齐。
- 本书结尾有不可逆变化，而不只是下一本预告。

## 阶段 3：章节写前准备

产出：

- `chapter_engine.md`
- 场景骨架；
- 写前任务单；
- 当前章节正史检查；
- 相关伏笔回声；
- 人物情绪残留；
- 信息边界提醒。

推荐命令：

```bash
fictionops plan-chapter my-novel --book book_01 --chapter 003
fictionops scene-plan my-novel --book book_01 --chapter 003
fictionops draft-brief my-novel --book book_01 --chapter 003
fictionops context-pack my-novel --task draft --book book_01 --chapter 003
```

出口标准：

- 视角人物知道什么、不知道什么明确。
- 本章不依赖旁白解释才能成立。
- 有至少一个“场景发动机”，而不是只靠作者总结推进。

## 阶段 4：正文写作

产出：

- 草稿章节；
- 修订备注；
- 写后关门报告。

推荐命令：

```bash
fictionops post-draft my-novel --book book_01 --chapter 003
```

写作原则：

- 先让规则被感到，再让规则被命名。
- 先让人物做出符合局限的动作，再让读者理解动机。
- 允许角色误判、说错、沉默、没看见。
- 不要在耳朵太多的地方大声密谋。
- 不要让所有聪明人共享同一种聪明。

出口标准：

- 章末有变化，也有余留。
- 读者能感到压力推进，而不只是知道信息增加。
- 人物没有突然获得作者级知识。
- `post-draft` 不再提示正文占位、发动机缺失或复盘空壳。

## 阶段 5：章节审计

产出：

- 单章审稿门禁；
- 连续性审计；
- 信息边界审计；
- 表格结构检查；
- 人物弧线审计；
- 词频与关注词扫描；
- 风格与读者体验审计。

重点检查：

- 上章压力有没有被继承？
- 人物刚经历的伤、怕、误解、疲惫有没有留下？
- 伏笔是否轻轻回声，而不是被解释？
- 秘密是否泄露太早？
- 是否出现过多排比、否定句、解释句、同款开头结尾？

推荐命令：

```bash
fictionops review-gate my-novel --book book_01 --chapter 003
fictionops check-tables my-novel --all
fictionops scan-words my-novel --watch "不是,没有,忽然"
fictionops revision-plan my-novel --book book_01
```

出口标准：

- `review-gate` 没有 `needs_post_draft` 或 `needs_review_fixes`；
- 必修问题已修；
- 可修可不修的问题进入修订备注；
- 新增正史已经同步到对应文件。

## 阶段 6：书级复盘

产出：

- 连续性与伏笔回声复盘表；
- 人物离开状态；
- 信息释放变更；
- 废案归档；
- 书级收束门禁；
- 下一本继承清单。

推荐命令：

```bash
fictionops retrospective my-novel --book book_01
fictionops book-gate my-novel --book book_01
```

出口标准：

- `book-gate` 没有 `needs_book_material` 或 `needs_book_closure`；
- 下一本开头不会把人物状态重置。
- 长线伏笔知道下一次该轻碰还是揭晓。
- 已写正文反向修正大纲。

## 阶段 7：清稿与发布

产出：

- 清稿正文；
- 简介；
- 标签；
- 字数统计；
- EPUB 或其他发布包；
- 发布说明。

建议命令：

```bash
fictionops export-clean my-novel --book book_01
fictionops audit-publish my-novel --book book_01
fictionops publish-copy my-novel --book book_01
fictionops export-metadata my-novel --book book_01
fictionops export-manifest my-novel --book book_01
fictionops export-epub my-novel --book book_01
fictionops audit-epub my-novel --book book_01
fictionops release-gate my-novel --book book_01
```

出口标准：

- 发布版与草稿版分开。
- 清稿不反向污染规划文件。
- 需要同步的正史已同步，不需要同步的发布包装不进入写作层。
- 书级收束没有被发布包生成过程绕过去。
- `release-gate` 不处于 `needs_release_artifacts` 或 `needs_release_fixes`。

## 阶段 8：接手与续写

产出：

- 更新后的 `current_context.md`；
- 接手日志；
- 下一阶段计划。

出口标准：

- 新作者或 Agent 能在有限上下文内知道当前要做什么。
- 不需要阅读全部历史聊天记录才能继续。
- 旧问题不会在每次接手时重新被发明。
