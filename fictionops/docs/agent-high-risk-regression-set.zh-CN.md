# Agent 高风险章节回归集

`tests/fixtures/agent_high_risk_review_cases.json` 保存三类匿名最小案例：

- 信息边界：外部动作允许出现，但旁白不能直接泄露不可见意图；
- 人物声音：少年/少女可以聪明，问题在于认知材料和语言训练是否有来源；
- 行文与读者体验：重复、排比和比喻按功能判断，不能机械删词或轮换同义词。

每个案例同时提供：章节片段、必要项目上下文、预期 reviewer 类别、必须避免的误报、完整六维 reviewer JSON。回归测试验证 schema、证据、稳定 issue identity 和三类覆盖。

这不是文学质量 benchmark，也不声称模型必然找出问题。它保护的是 controller/reviewer 接口：高风险问题有固定结构，外部模型升级或 prompt 调整后可以在同一案例上比较。真实模型效果仍以 dogfood 与作者采纳证据为准。

## Raw / RAG / Workflow 对照

`fictionops.agent_research_baseline` 会让同一 runner 对每个案例分别运行三种条件：`raw` 只看章节片段，`rag` 增加项目上下文，`workflow` 再增加误报护栏与六维审读合同。三组都不接收 `expected_category` 或标准 review。报告比较类别命中率、证据落地率与额外问题数，并保留 runner telemetry。

```powershell
python -m fictionops.agent_research_baseline tests/fixtures/agent_high_risk_review_cases.json --out baseline.json --runner python examples/agent_runner_openai_chat.py --provider deepseek --model deepseek-chat
```

这套最小案例只验证实验协议可复现，不能单独支持“workflow 提升文学质量”的结论。正式研究报告需要固定模型版本和采样参数，多次运行，并报告置信区间、人工盲评与失败案例。
