# 共享状态、读者输出与离线资产

analysis.json是唯一 authored 科学状态。保留claims、parameters、coverage、unknowns、reproduction；这些字段默认只输出到analysis-notes.md。正文只取reader.overview、原文roadmap及公开sections。schema1.0可构建为无自动审计段落的旧版正文；新任务用1.1。

reader.roadmap逐项写section（原文§编号）、title、argument（论证职责）、focus（图表/式定位）、accessed source_id及PDF页码。focus写section_id、question、why；why属于内部叙事选择，快捷导航只显示问题。schema保证引用和字段，作者核对原文所有主要§的真实性与完整性。

sections的audience默认reader；appendix为补充科学推导；internal为执行记录。主文放在附录之前。关键推导保持开放，不将中心机制折叠。角色供科学完整性检查，不强迫所有深读都做数学。相同科学限制必须在论证处由作者解释，不能依靠内部unknowns的自动公开。

visuals每项提供id、kind(image/interactive)、section_id、placement(include/omit)、question、why、alternative、caption与basis；交互需interaction_gain。image为工作区相对PNG/JPEG/WebP路径；interactive提供fragment及可选styles/script/data/data_id。资产是作者审查过的本地组件代码，不能将论文中的未知脚本当组件直接执行。每个include图在对应section.markdown放一次`<!-- astro-visual:ID -->`。构建器使Markdown保留原图/交互链接，HTML原位内嵌。

不规定模块数量。omit资产无需存在、不嵌入输出。资源路径和产物路径限制在工作区，数据拒绝NaN，JSON岛唯一且转义`<`。本地片段应遵守Figure Kit、CSP和科学计算契约。生成文件含共享状态SHA-256；验收从analysis及当前资产重建逐字节比较，资产变动会使旧HTML失效。

`build_report.py --analysis WORK/analysis.json`同时生成report.md、report.html、analysis-notes.md；artifacts.notes可改独立记录位置。`--md-only`只生成Markdown和notes。`--markdown`校验相邻analysis精确一致；作者修正先改状态。完整渲染和验证成功后才写输出；拒绝覆盖状态与另一个产物。

旧section.module的single-lens/binary-lens与--demo-data继续支持，保留独立控件状态和固定数据。新论文先选择图形，不能自动插入教学组件。CSS由assets/report.css统一所有读者报告的排版与基础图形；原生disclosure只用于导航和补充层，原生select接受系统弹出菜单。
