# V1.1 内容与输出分层

读者先建立研究问题、贡献、结果与原文结构的全局认识，再沿概念依赖进入关键机制。科学文章与工作记录从共享状态分别构建，复现和执行信息保存在独立记录中。

```
原文与核查 → analysis.json
                ├ reader.overview / roadmap / focus + sections(reader)
                │     → report.md / report.html（科学文章）
                ├ sections(appendix)
                │     → 文章末尾进一步科学推导
                └ coverage / claims / parameters / reproduction / internal
                      → analysis-notes.md + validation（工作记录）
```

选择图形前保存理解难点、替代方案、include/omit理由及交互增益。原图和局部组件由manifest与共享状态交给同一个构建器；验收比较当前资产确定性生成的完整HTML。

兼容schema1.0的科学状态、数值基元、内置组件和CLI；新草稿为schema1.1，发布需要原文地图与概览。旧正文的防御性段落不会被自动删除，需作者按句子作用重新编辑。没有添加关键词过滤器，也没有假设每个领域都必须写数学或配交互。

DESIGN.md的改动为有意的系统演进：保留白底、语义色、离线系统字体、原生控件和Figure Kit；标题缩到24–34px，正文宽780px，科学概览优先，目录转为原文地图后的小型导航。关键推导默认展开；补充层为原生details。canonical runtime仍是assets/report.css；DESIGN.md记录意图并镜像颜色，现有漂移测试继续使用。

数值模块未改。质量检查新增受众泄漏、原文定位引用、零图、被舍弃资产、附录发现性、资产变更后验收拒绝与失败保留输出的测试；结构完整不等于叙事好读，仍做实际文章/截图评估。
