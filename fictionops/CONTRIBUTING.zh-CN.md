# 贡献指南

感谢你愿意参与 FictionOps。这个项目的目标不是自动替作者写小说，而是让长篇小说、作者判断和 AI 协作都变得更可维护。

## 1. 贡献优先级

优先接受这些改动：

- 修复 CLI 契约错误，例如命令无法运行、路径解析错误、安装后找不到模板。
- 增强测试，尤其是能防止长线工作流断裂的回归测试。
- 改善中文文档、模板和工作流说明。
- 增加不依赖第三方服务的本地审计能力。
- 让 Agent 协作边界更清楚，例如输入、输出、禁止覆盖范围。

暂缓接受这些改动：

- 一键生成整本小说。
- 需要联网或闭源服务才能运行的核心能力。
- 大型 GUI、数据库或复杂服务端。
- 把文学判断硬编码成唯一标准。

## 2. 开发环境

推荐使用 Python 3.10 或更高版本。

```bash
python -m pip install -e ./fictionops
fictionops --version
```

运行测试：

```bash
python -m unittest discover -s fictionops/tests -v
```

运行单个 smoke：

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_smoke -v
```

## 3. 提交前检查

提交前至少确认：

- 新增命令有核心函数测试和 CLI 子进程测试。
- 会影响安装态的改动通过 packaging smoke。
- 修改根目录 `templates/` 后，也同步 `src/fictionops/templates/`。
- 文档中的命令可以实际运行。
- 不把真实小说项目、私有大纲或发布稿写进测试数据。

## 4. 设计原则

FictionOps 的核心原则：

- 文件优先，便于版本管理和人工审阅。
- 本地优先，不强制依赖数据库、云服务或模型 API。
- 作者优先，工具只提示结构缺口，不替代审美判断。
- Agent 可协作，但必须留下可审计的输入、输出和修改范围。
- 长篇优先，功能要服务数十万字、数百万字后的可维护性。

## 5. 版本策略

- `0.x` 阶段允许 CLI 输出继续调整，但核心命令的参数应尽量稳定。
- 破坏性变更必须写入 `CHANGELOG.md`。
- 每次发布前按 `docs/release-checklist.zh-CN.md` 检查。

## 6. 文档语言

当前项目以中文工作流为第一语言。英文 README 保持可安装、可理解即可；详细方法论优先沉淀在中文文档中，等流程稳定后再系统翻译。
