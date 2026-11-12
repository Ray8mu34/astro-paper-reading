# Schema 1.3：原文章序天文精读示例

这是**纯教学合成结构**，不能当成论文发现或观测数据。`source.md` 模拟四章原文，`analysis.json` 把每一章顺序映射到 `sections[].source_sections`，正文前有一段论证路线，文后有章号与页码的结构索引。独立评价为无源映射的 review，放在作者四章解释之后。

脚本演示（不需要 HTML 依赖）：

```sh
python scripts/build_report.py --analysis examples/paper-order-v13/analysis.json --md-only
python scripts/validate_skill.py --analysis examples/paper-order-v13/analysis.json --md-only --require-artifacts
```

这两条命令验证结构和产物，不会读取外部论文或复现观测。报告本身在 `report.md`；更复杂的物理内容由实际研究论文决定，不应把此教学例子用作固定结构模板。
