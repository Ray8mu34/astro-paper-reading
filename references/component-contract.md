# schema 1.3：科学状态、作者原文顺序与离线资产

`analysis.json` 是唯一 authored 科学状态。保留来源、科学 claims、关键 parameters、coverage、unknowns、reproduction；这些主要进入独立 `analysis-notes.md`。面向读者的主文来自 `reader.overview`、`reader.argument_route`、公开 `sections` 与后置 `reader.roadmap`。schema 1.0/1.1 旧状态保留构建兼容性；**新任务使用 1.3**。

## 原文章节与正文的关系

`reader.roadmap` 按真实主文章序列出主要原文章节，每条有 `section`（原文 § 标识）、`title`、`argument`（该章实际论证职责）、`focus`（最重要的图/式/表）、`source_id` 与 PDF `page`。实际主要章须完整登记；不强制逐个小节/每段都登记。此导览**在正文末尾用于 PDF 回查**，不是一份替换正文的目录式概述。

`reader.argument_route` 是前置的、简短自然段式论证路线，描述作者按什么顺序提出问题和验证结论；`organization` 默认 `paper-order`，如选择 `restructured` 须填写具体 `departure_reason`。`sections[].source_sections` 指向 roadmap 里登记的 § 字符串，主要正文节应覆盖 roadmap 并保持相对顺序；相邻短章可合并、关键长章可拆成连续正文节。作者原文的 limitations/discussion 本身有 § 时映射到相应章节；**额外独立评价**可用不映射的 `review`/`limitations` 正文节，放在完整的作者论证之后。`reader.throughline` 与 `reader.connections` 是可选内部草稿，普通论文不生成重复的逐章依赖表。

校验器能发现已记录章号缺失、倒序、引用未知原文章号以及无说明的重组，不能识别 PDF 中被漏填的章节，也不能判断科学解释的正确性。quick 模式可仅说明实际材料范围，不必声称有完整原文地图。

## 正文、补充和图形

`sections` 的 `audience` 默认为 `reader`；`appendix` 放后置补充科学推导；`internal` 放执行记录。主文先于附录，核心机制不靠折叠层隐藏。role 是背景/方法/推导/证据/局限/独立评价类别，不表示所有深读都必须有大量数学或模型拟合。

`reader.focus` 中的 `section_id`、`question`、`why` 是可选的重点阅读路径：公开快捷导航只展示问题，内部 why 留记录。它影响讲解深度，不允许改变原文主要章节的次序。

`visuals` 元素包含 id、kind(image/interactive)、section_id、placement(include/omit)、question、why、alternative、caption 与 basis；交互才需要 interaction_gain。image 是工作区内的 PNG/JPEG/WebP；interactive 是本地 HTML fragment 和可选 styles/script/data/data_id。每个 include 图的正文相应节插入一次 `<!-- astro-visual:ID -->`，构建器将原图/交互链接放到原论证位置；omit 不需创建资产。论文里的脚本不能直接作为可执行组件。

## 交付与兼容

脚本执行 `python scripts/build_report.py --analysis WORK/analysis.json` 生成 `report.md`、`report.html` 与 `analysis-notes.md`，加 `--md-only` 只需 Markdown 和内部记录；`python scripts/validate_skill.py --analysis ... --require-artifacts` 检查当前状态与文件的一致性。产物包含 analysis SHA-256，所有本地资产限于工作目录且需可靠转义/拒绝非法数值。这是文件和结构的一次性检查，不是浏览器回归和科学复现。

原有 `section.module=single-lens/binary-lens` 及 `--demo-data` 继续兼容。仅当相关天文论文需要该物理示意时使用，不能默认加入。离线 `assets/report.css` 是唯一基础样式所有者，MathML 与原生 disclosure 保持可访问；额外详解可折叠，决定结论的中心公式应在文章正常展开。
