# Astro Paper Reading

面向有专业基础的研究生，把天文学、天体物理与引力透镜论文读成一篇连贯、深入的科学解释文章。

**先理解研究者在解决什么问题、为什么这样思考，以及如何得到结论，再深入关键机制。**

这是一个供 AI Agent 使用的 Skill，包含阅读与写作规范、结构化科学状态、离线 HTML 构建器和经过测试的微透镜教学组件。当前版本为 **1.1.0**，由 Astro Paper X-Ray 演进而来。

## 阅读体验

- **先建立全局。** 开篇交代研究问题、困难、思路、贡献、主要结果与科学适用范围。
- **能回到原文。** 结构导览对应真实的 § 编号，解释各节在论证中的作用，并定位关键图表与公式。
- **围绕关键问题深讲。** 选择决定结论的机制、难点和证据；需要时保留完整推导，简单内容简明解释。
- **图形服务理解。** 优先解读论文原图；只有交互能回答具体的反事实问题时才制作交互，不设数量指标。
- **正文保持连贯。** 关键推导自然展开，补充推导可放附录；文件版本、覆盖范围、执行日志和证据账本独立保存。

天文与微透镜有专门的物理和统计参考规范；其他天体物理领域按论文的问题与方法组织内容。四种输出模式如下：

| 模式 | 适合的任务 |
| --- | --- |
| `quick` | 筛选论文，迅速把握问题、思路和结果；可基于摘要并注明信息范围 |
| `deep-md` | 深入解释论文，交付便于保存与编辑的 Markdown |
| `interactive-html` | 深读文章与独立离线 HTML；按需要嵌入原图或交互，也可以没有交互 |
| `critical-review` | 围绕中心论断分析证据、假设、简并与替代解释 |

## 安装

需要支持本地 Skill、文件访问和脚本执行的 Agent。以 Codex 为例，将本仓库放到其 skills 目录，使目录结构为 `~/.codex/skills/astro-paper-reading/SKILL.md`。

Windows PowerShell：

```powershell
git clone https://github.com/Ray8mu34/astro-paper-reading.git "$HOME/.codex/skills/astro-paper-reading"
Set-Location "$HOME/.codex/skills/astro-paper-reading"
```

macOS / Linux：

```sh
git clone https://github.com/Ray8mu34/astro-paper-reading.git ~/.codex/skills/astro-paper-reading
cd ~/.codex/skills/astro-paper-reading
```

使用自己的项目或虚拟环境安装构建依赖，要求 **Python ≥ 3.10**：

```text
python -m pip install -e .
python scripts/validate_skill.py
```

若使用 Conda，请通过目标环境运行，例如 `conda run -n dl_env python -m pip install -e .`。核心依赖包括 NumPy、SciPy、Mistune、PyYAML、jsonschema 与 latex2mathml。安装完整目录：构建器还需要相邻的 `assets/`、`schemas/` 与参考文档。

安装后在新聊天中调用 `$astro-paper-reading`。已安装旧名 `astro-paper-xray` 的用户，可以保留旧目录作为备份，再将新版安装到新目录；调用时明确使用新名。

## 使用

把 arXiv 链接、DOI、论文 PDF 或正文交给 Agent，例如：

```text
使用 $astro-paper-reading 深度解读 https://arxiv.org/abs/2311.13097。
读者具备微透镜基础，但尚未看过原文。
请先讲清研究问题、贡献、结果和原文章节的论证结构，
再深入最关键的机制，按理解需要使用原图或交互，输出离线 HTML。
```

```text
使用 $astro-paper-reading，以 critical-review 模式分析这篇论文。
重点解释核心结论依赖哪些观测约束和先验，以及什么证据能区分替代解释。
```

Agent 读取论文、核对证据、选择讲解重点并填写 `analysis.json`；Python 脚本负责校验和构建。脚本不会独立阅读论文或调用语言模型。

| 产物 | 内容 |
| --- | --- |
| `report.md` | 面向读者的科学解释文章 |
| `report.html` | 同一文章的离线阅读页面，包含选用的图片、MathML 与交互资产 |
| `analysis.json` | 共享科学状态、原文定位、概览、章节地图与图形选择 |
| `analysis-notes.md` | 独立的来源、证据、参数、覆盖与执行记录 |

生成的 HTML 可直接用现代浏览器打开；阅读与已嵌入控件不需要 Python、服务器或网络。论文获取与依赖安装需要相应资源访问。

## 脚本工作流

下面的命令从 Skill 根目录运行。`reading-work/` 是独立的阅读输出目录，也可指定绝对路径。

```text
python scripts/new_analysis.py "https://arxiv.org/abs/2311.13097" --mode interactive-html --out reading-work
```

草稿默认 `status=draft`。由 Agent 完成全文阅读、科学核查与 schema 1.1 的 `reader.overview`、`reader.roadmap`、`reader.focus`，并按 `reader`、`appendix`、`internal` 区分段落受众。所选图形通过 `visuals` 声明教学目的与本地资产。完成后设为 `ready`：

```text
python scripts/build_report.py --analysis reading-work/analysis.json
python scripts/validate_skill.py --analysis reading-work/analysis.json --require-artifacts
```

仅需 Markdown 时，构建命令加 `--md-only`。使用内置微透镜组件时，按 manifest / section 配置图形，并传入 `--demo-data`。完整约定见 [阅读方法](references/reading-method.md)、[输出模式](references/output-modes.md)、[可视化规范](references/visualization.md) 与 [组件契约](references/component-contract.md)。

## 开发与验证

```text
python -m pip install -e ".[test]"
python -m pytest -q
python scripts/validate_skill.py
python scripts/validate_numerics.py
```

离线组件回归夹具可本地生成并检查：

```text
python scripts/build_report.py --analysis examples/ogle-2016-blg-1928/analysis.json --demo-data examples/ogle-2016-blg-1928/demo-data.json
python scripts/validate_skill.py --analysis examples/ogle-2016-blg-1928/analysis.json --require-artifacts --demo-data examples/ogle-2016-blg-1928/demo-data.json
python scripts/browser_check.py
```

浏览器检查默认寻找 Windows Edge / Chrome；其他平台或浏览器路径可用 `--executable PATH` 指定，或在当前环境安装 Playwright Chromium。测试检查控件、数值一致性、键盘操作、窄屏排版和离线请求。检查记录保存在本地 `validation/`。

该夹具保留 schema 1.0 的兼容性状态，供开发测试使用。其 77 个测光点为模拟数据；新论文阅读使用 schema 1.1。单透镜组件计算均匀源放大率，二元组件提供静态临界曲线与焦散；其他论文所需图形可通过 manifest 接入。科学计算实现沿用已验收版本，内部 Python 模块名保留 `astro_xray`。

创建与核验便携安装包：

```text
python scripts/package_skill.py
python scripts/check_release.py dist/astro-paper-reading-v1.1.skill.zip
```

ZIP 顶层为 `astro-paper-reading/`，包含文件哈希清单。论文副本、生成报告、缓存及执行记录不属于源码提交。结构和数值检查之外，论文的科学准确性与阅读体验仍通过实际阅读和页面检查评估。

## 目录

```text
SKILL.md        Agent 入口与阅读规则
agents/         Skill 展示信息
references/     阅读、科学完整性、领域、统计与可视化规范
schemas/        analysis.json 结构
astro_xray/     报告构建与微透镜数值基元
assets/         离线 HTML 样式、脚本与教学组件
scripts/        草稿、构建、检查与打包入口
tests/          科学数值、状态、产物与前端回归测试
examples/       数值组件测试夹具
docs/           内容架构与设计说明
upstream/       Paper X-Ray 设计参考、溯源与许可证
```

## 许可证与致谢

代码与项目文档使用 [MIT License](LICENSE)。阅读方法与部分视觉设计参考 [Wang-auspicious / Paper X-Ray](https://github.com/Wang-auspicious/paper-xray)，保留其版权与许可证；来源与引用版本见 [upstream/provenance.json](upstream/provenance.json) 和 [设计说明](docs/DESIGN-AUDIT.md)。

论文、原图及第三方科学数据遵循各自的授权。本仓库保存可复用 Skill、代码与合成教学数据，完整论文和个人阅读产物留在各自的阅读工作目录。
