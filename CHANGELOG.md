# Changelog

## v1.2.0-fast — source-order astronomy reading, aligned with CV v1.2.1

- **Reading philosophy**: source chapter order and author argument are the default narrative skeleton; in-depth astronomy/mathematics explanation is embedded in the corresponding chapter. Motivation, observations, theoretical assumptions and method choices must not be collapsed into a replacement thematic story.
- **New schema 1.3 fields**: `reader.argument_route`, `reader.organization`, `reader.departure_reason`, optional `reader.throughline/connections`, and `sections[].source_sections`. Old schema 1.0/1.1 states remain buildable.
- **Validation**: publishing a new deep report checks the recorded original-paper chapter coverage and order; deliberate restructurings require an explicit reason. Quick reports are exempt from full chapter mapping when the source was not fully read.
- **Reader-facing output**: concise argument route near the beginning, original chapter guide at the end; independent assessment after the paper's main case. Evidence ledgers and execution logs remain internal.
- **Field-specific guidance**: clarified different evidence chains for observational, theoretical, numerical/simulation, instrumentation and method papers; retained statistics and microlensing physics modules unchanged in substance.
- **Lightweight default**: once-through reading/writing and integrated check; no obligatory blind retelling, reader-review form, external datasets, numerical refits, pytest, browser checks or release tasks for each paper.
- **Compatibility**: kept the existing astronomy render engine, offline HTML, MathML, simulation/visualization assets, and legacy scientific test fixtures.

## v1.1.1-fast

- Earlier reader-first deepening and lightweight build/validation approach, with optional microlensing components and domain references.
