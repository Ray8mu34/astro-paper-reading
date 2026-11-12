# Astro Paper Reading v1.2.0-fast：原文章序驱动的轻量精读架构

```text
实际论文（已固定版本；正文主要章节、图/式、必要附录）
  ↓
reader.roadmap（按原文主要章序：章号、职责、来源和页码）
reader.argument_route（读者开篇的一段原文论证路线）
sections[].source_sections（报告段落 → 作者原文章节）
  ↓
report.md / report.html（按原文章序精讲，含必要物理/统计与原图）
  ↓
一次交付检查（真实章序、关键科学事实、文件一致性）
```

`schema_version=1.3`、`reader.organization="paper-order"` 为新任务默认。原文章节可以相邻合并或连续细分，主要章节完整覆盖并保持顺序；独立评价在主要作者论证之后。如用户明确要求专题重组，或局部先修解释仍不足以解决严重理解障碍，使用 `restructured` 和具体的 `departure_reason`，保留原文地图。

文首是科学 `overview` 和简短 `argument_route`，不是完整章节目录或模型批评；文末 `roadmap` 为带真实 §/PDF 页码的检索表。`throughline`/`connections` 只是可选的内部理解笔记，非每篇必填。`claims`/`parameters`/`coverage`/`reproduction` 进入内部 `analysis-notes.md`，不会占据读者正文。`sections(audience=appendix)` 为补充科学材料，不用于藏核心方法。

**与 CV v1.2.1 的一致性**：原文忠实、在对应章内深化技术、独立评价集中、一次轻量核对；**天文特有差异**：观测量到物理推断的层级、单位/参考系/时间系统、先验与简并、理论假设和模拟数值域，按论文类型保留。

报告引擎保留离线 MathML、原图/本地示意选择、共享数值组件；不修改 `astro_xray/lensing.py` 或资产的物理计算。兼容旧 schema 1.0/1.1：老报告可以构建，不自动回写新的章序字段。验证器只检查已登记的 roadmap 覆盖，无法自行检查论文真实目录是否被漏抄；人的科学阅读仍有必要。

普通论文读写不启用读者自评、MCMC 重跑、浏览器/响应式检查或软件回归。开发新版本时可按变更运行专项 pytest 和 ZIP 文件哈希校验；测试输出不能代替论文内容的解释质量。
