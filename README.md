# Astro Paper Reading

适合天文、天体物理研究生的论文精读 Skill，支持观测、理论、模拟、方法、仪器和混合型研究。**v1.2.0-fast 与 CV Paper Reading v1.2.1 使用同一套组织原则：默认按原文章节和论证顺序讲清整篇论文，并在对应位置深入物理与数学，最后集中做独立评价。** 现有微透镜、统计推断、离线 HTML 和数值教学组件保留。

## v1.2.0-fast 的关键变化

- **遵循原文论证**：先核对作者真正的主要章节，不再默认“暂时放下目录”、由模型重组最短故事。
- **解释研究选择的由来**：相关研究的缺口、观测与样本选择、模型假设、技术瓶颈、方法与图表之间的关系纳入正文。
- **在原文对应位置深入**：解释关键方程、单位、参考系、数值方法、拟合及先验，以及哪些数据支撑什么物理结论。
- **先重建后评价**：重要结论的必要限制在原位写一次，额外的科学审查放在作者论证完整介绍之后；避免重复防御性写作。
- **真正轻量**：普通任务不额外进行逐章自评、读者模拟、全量数值回归、MCMC、浏览器/响应式测试或发布验收。

新任务使用 `schema_version=1.3`。`reader.roadmap` 保存**真实原文主要章节**；`argument_route` 是概览后的一段原文论证路线；`sections[].source_sections` 建立正文与原文章节的对应；默认 `organization=paper-order`。有具体理由需要重组才选 `restructured` 并填写 `departure_reason`。`throughline/connections` 可选，无需额外重复规划。旧 schema 1.0/1.1 的报告保留构建兼容性。

## 四种模式

|模式|目的|
|---|---|
|`quick`|仅根据确实读取的材料快速掌握研究问题与结果|
|`deep-md`|原文顺序的完整深度讲解，交付 Markdown|
|`interactive-html`|同样的深度和章节逻辑，追加离线 HTML；原图优先、交互按需|
|`critical-review`|先讲清作者原文论证，再集中分析重要替代解释与证据边界|

## 安装

从 [GitHub Releases](https://github.com/Ray8mu34/astro-paper-reading/releases/latest) 下载 Skill ZIP，把顶层 `astro-paper-reading/` 放入 Codex 的 Skill 目录（例如 `~/.codex/skills/astro-paper-reading/`），替换同名旧目录。完整目录中应保留 `SKILL.md`、`references/`、`schemas/`、`astro_xray/`、`scripts/` 和 `assets/`。

也可以在目标目录尚不存在时，从仓库安装当前版本：

```powershell
git clone --branch v1.2.0 https://github.com/Ray8mu34/astro-paper-reading.git "$env:USERPROFILE/.codex/skills/astro-paper-reading"
```

Python ≥ 3.10，脚本依赖 numpy、scipy、mistune、PyYAML、jsonschema、latex2mathml。可在已有 Conda 或项目虚拟环境中安装：

```sh
python -m pip install -e .
python scripts/validate_skill.py
```

## 直接用法

把 arXiv 链接、DOI、PDF 或正文交给 Agent：

```text
使用 $astro-paper-reading 精读这篇论文。
按照作者实际的章节与论证顺序讲解：研究问题、背景与动机、
观测/模型/理论方法、关键物理与数学、原图和结果、结论及其意义。
在相关章节展开必要推导；作者主要论证讲完之后再做独立评价。
输出 Markdown 和离线 HTML，不开展额外浏览器或数值复现测试。
```

研究生具有相应专业基础，报告无需把每个普通术语都展开为百科，但不能跳过决定核心方法和结论的推理。理论、观测、模拟研究按实际论文路线分别处理，不给所有论文套固定结构。

## 脚本工作流（Agent 负责阅读）

```sh
python scripts/new_analysis.py "paper.pdf" --mode interactive-html --out WORK
# Agent 阅读原论文，填 analysis.json 与读者文章；status 改为 ready
python scripts/build_report.py --analysis WORK/analysis.json
python scripts/validate_skill.py --analysis WORK/analysis.json --require-artifacts
```

只需 Markdown，两条构建/验证命令加 `--md-only`。`analysis.json` 包含科学证据和章节映射；`report.md`/`report.html` 面向读者；`analysis-notes.md` 放来源、关键参数、未知和执行记录。内置微透镜示意组件只在适合时通过 `--demo-data` 启用；其他论文不要为了使用组件而添加无关图形。离线 HTML 打开后不需要服务器或网络。

**日常交付到这里结束。** 只做一次合并式质量检查，确认与真实原文目录相符、关键物理/统计结论正确、主要原图解释清楚和文件生成成功。不要把 Skill 开发测试纳入每篇论文。

## 可选开发检查（不是读论文步骤）

```sh
python -m pip install -e ".[test]"
python -m pytest -q
python scripts/validate_numerics.py
python scripts/browser_check.py
python scripts/package_skill.py
```

这些命令用于修改了 Skill 结构、报告引擎、前端组件或数值算法后的专项回归。依赖不足时只运行可用的针对性测试，不能声称未运行的 HTML 测试通过；它们不是精读报告生成的前置条件。

## 结构与参考

- [SKILL.md](SKILL.md) — Agent 必要指令与最短运行方式
- [原文优先工作流](references/narrative-workflow.md) — 原文地图、正文映射、一次性检查
- [读者体验](references/reader-experience.md)、[阅读方法](references/reading-method.md) — 分层解释与独立评价
- [论文类型](references/paper-types.md)、[统计推断](references/statistics.md)、[微透镜](references/microlensing.md) — 天文领域按需参考
- [组件契约](references/component-contract.md)、[可视化](references/visualization.md)、[质量检查](references/quality-gates.md) — 结构/图形/交付约定
- `examples/ogle-2016-blg-1928/` — 已有微透镜数值教学测试夹具；`examples/paper-order-v13/` — 新的原文章序合成示例

代码和项目文档采用 [MIT 许可证](LICENSE)；相关上游设计和许可证见 [upstream/provenance.json](upstream/provenance.json)。论文、图片及天文数据的授权由其原始权利人决定；压缩包不包含论文全文。
