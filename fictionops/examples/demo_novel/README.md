# FictionOps Demo Novel

这是一个最小可运行示例项目，用来演示 FictionOps 如何把一个小型长篇项目拆成可维护的写作状态。

从本目录运行已安装的 CLI：

```bash
fictionops plan-chapter . --chapter 002 --force
fictionops scene-plan . --chapter 002
fictionops draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
fictionops context-pack . --task handoff --no-content
fictionops doctor . --book book_01 --format json
```

如果是在源码仓库里直接运行：

```bash
python ../../src/fictionops/cli.py plan-chapter . --chapter 002 --force
python ../../src/fictionops/cli.py draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
```

这个 demo 的重点不是文学质量，而是展示一条最小维护链：

- 书纲里的逐章规划同步到章节发动机；
- 章节发动机生成场景计划；
- 写前 brief 合并范围化上下文、信息边界、人物口吻和写作禁区；
- handoff context-pack 只收集接手所需文件；
- doctor 汇总当前项目健康状态。

