# Luna CAD Sheet Layout

**An AI Agent Skill for AutoCAD Sheet Layout, Title Blocks & Drawing Index Management**

Give your AI agent a practical workflow for the final preparation of CAD construction drawings. The engineering design is finished and the DWGs are drawn—but title blocks, sheet layouts, viewport scales, drawing numbers and the drawing index still need attention.

Luna CAD Sheet Layout equips an existing AI agent with task instructions, reusable native CAD helpers and lessons from real AutoCAD framing work. The agent interprets the drawings, plans the sheets, calls CAD tools and reviews the deliverables. **This is an executable workflow Skill for AI agents, not a conventional one-click CAD plugin or a standalone AI agent.**

[中文介绍](README.zh-CN.md) · [Skill entry](skills/luna-cad-sheet-layout/SKILL.md) · [Validation & limitations](skills/luna-cad-sheet-layout/references/validation.md)

## Two modes, chosen by the agent

|Mode|Guidance|Best fit|
|---|---|---|
|**Low-compute / guided — default**|Clear steps, reusable scripts, known failure cases and recovery notes. Follow the next relevant step instead of rediscovering the workflow.|Limited compute or context, less CAD experience, or unfamiliar tasks.|
|**High-compute / concise**|Goals, main workflow, necessary boundaries and key checks. Read detailed troubleshooting only when needed.|Agents able to interpret drawings, choose parameters and recover independently.|

The agent selects or switches modes based on its capabilities and task complexity. No model names are prescribed. Guided mode is intended to reduce trial and error; this beta does not claim measured token savings or a proven independent success rate for lower-compute agents.

The guidance comes from actual AutoCAD work: accidental edits to the overall paper-space viewport, unloaded Xrefs, insertion-unit scaling, viewport-specific layer freezing, clipping remnants after framing, and inspection actions that unexpectedly changed viewport state.

## From finished design to an organized drawing set

**Start with:** completed design DWGs, a drawing index, candidate title-block/frame DWGs and a working CAD environment.

**Ask the agent to:**

1. Find candidate title-block external references (Xrefs), inspect revision-date clues and select a suitable frame. Prefer newer revisions where appropriate; a date alone does not prove suitability.
2. Match actual design content to the index, organize sheets and layouts, attach the selected Xref, and adjust viewport framing and scales.
3. Reconcile drawing numbers, titles and page fields with the drawing index.
4. Find existing drawings, add/remove/rearrange sheets, and update affected numbering, titles and index entries.
5. Preserve engineering content, save tracked DWG changes, export PDFs and inspect output as the task requires.

**Receive:** an organized working drawing set, an updated index when included in the task, and a record of completed sheets, checked output, dependencies and unresolved items. These are agent-executed tasks, not unattended batch-processing guarantees.

## Skill, CAD tools and Foundation

The **Skill guides the agent** in understanding the task, interpreting drawings, selecting suitable frames and scales, planning actions and reviewing output. **CAD Agent Foundation provides general native CAD operations.** Reuse available Foundation tools first; Foundation is an optional backend, not the only way to use this Skill.

Where layouts, viewports or Xrefs are not yet exposed by the available Foundation version, retain the **AutoCAD native COM** path inherited from field-tested work. Select and disclose the backend before writing to a drawing. Never switch to COM to bypass an unknown write, failed verification or Foundation protection state. This beta adds no Foundation APIs.

|Component|Role and current scope|
|---|---|
|AI agent|Drawing interpretation, frame suitability, sheet planning, explicit parameters and visual review.|
|Skill and references|Guided or concise procedures, index maintenance and targeted troubleshooting.|
|Bundled Python helpers|Read-only inventories, frame/date candidates, viewport fitting/freezing, saving and plotting helpers; not a complete batch layout engine.|
|AutoCAD native COM|Existing path with AutoCAD 2022 field history; requires Windows, installed AutoCAD and Python/pywin32.|
|CAD Agent Foundation|Preferred where real tools cover the operation; assessed local 1.2.0-beta.1 integration is partial.|

See [backend selection](skills/luna-cad-sheet-layout/references/backends.md) and [native operations](skills/luna-cad-sheet-layout/references/native-com.md).

## Install

Download or clone this repository. Copy **`skills/luna-cad-sheet-layout`** into your agent's configured skill directory, then refresh skill discovery. For a Codex installation, a common location is `~/.codex/skills/luna-cad-sheet-layout`; use the location configured by your host.

Alternatively, extract the **skill-only ZIP** into the skill directory: it contains a top-level `luna-cad-sheet-layout` folder. The **repository ZIP** contains a nested `skills/` folder; install the nested skill, not the entire repository as a skill.

Prepare work copies, an index and usable frame DWGs. COM helpers require Python with `pywin32` in the interpreter that runs them. Your agent needs authorized local CAD execution access. Installing this Skill does not install AutoCAD, an AI runtime or a Foundation server. No project DWGs, commercial fonts or signed title-block templates are bundled.

The landing page is English-first; detailed operating instructions currently use Chinese. Host-specific skill discovery and tool access must be configured separately; this package does not certify every agent host.

## Ask your agent

**Guided mode:**

> Use $luna-cad-sheet-layout in low-compute guided mode. Inspect these completed DWGs and the drawing index, choose suitable title-block Xrefs using revision dates as clues, then arrange sheets and reconcile titles and numbers. Preserve correct existing layouts and check representative sheet types.

**Concise mode:**

> Use $luna-cad-sheet-layout in high-compute concise mode to prepare this completed drawing set for delivery. Decide layout and viewport parameters from the actual content, reuse available CAD operations and consult troubleshooting only when needed. Report checked output and unresolved items.

**Continue an existing set:**

> Use $luna-cad-sheet-layout to locate the requested drawing, add one sheet and update affected sheet numbers, titles, page fields and index entries. Keep the engineering content intact.

## What has actually been validated?

**Version: 3.0.0-beta.1 — beta prerelease.**

|Evidence level|What it means|
|---|---|
|Historical AutoCAD 2022 field work|An original project sheet was framed through COM, visually reviewed from PDF output and checked for preservation of original model objects. This informs the guidance; it is not a new-project certification.|
|Current offline checks|18 targeted tests cover viewport protection, read-only inspection, freezing, explicit version selection and date-candidate behavior. Naming, links, metadata and entry points are checked separately.|
|Current workflow support|Agent-led layout, title-block and index maintenance instructions plus reusable helpers. Matching content, changing sheets and synchronizing the index require agent decisions and explicit operations.|
|AutoCAD 2026|An explicit connection option exists. **The new Skill has not completed AutoCAD 2026 sheet-layout field validation.**|
|Foundation-only framing|Not complete in assessed local 1.2.0-beta.1; paper-space, layout, viewport and Xref primitives remain gaps.|

Rotated/3D viewport fitting is outside the helper's supported scope. Proxy and block-content visibility depends on actual backend read capabilities. Normal font-width changes are handled by agent review and adjustment, but this documentation update has not relaxed existing Foundation save-verification restrictions.

Protect engineering originals, record partial completion and inspect proportionately. API success or a PDF file's existence alone does not prove a sheet looks right. See the [validation record](skills/luna-cad-sheet-layout/references/validation.md) for retained history and outstanding checks.

## 中文速览

**Luna CAD 智能体套图排版技能：让 AI 智能体完成 CAD 施工图最后一道整理工序。**

面向设计和绘图已经完成，但套框、布局分幅、视口比例、图号图名及目录尚未整理的场景。Skill指导智能体读取实际内容，选择适用的图框外参，组织图幅并维护目录一致性。默认低算力分步模式，高算力可选简明模式；规则来自真实AutoCAD套框经验。优先复用CAD Agent Foundation，缺少操作时保留明确选择的原生COM路径。这是供现有AI Agent使用的技能，不是独立Agent或传统一键插件。

详见[中文介绍](README.zh-CN.md)。

## Release information

[Release notes](RELEASE-NOTES.md) · [Description & topics](docs/GITHUB-METADATA.md) · [Provenance](docs/PROVENANCE.md) · [Local preparation](docs/RELEASE-PREP.zh-CN.md)

Source and beta packages: [GitHub repository](https://github.com/capskov/luna-cad-sheet-layout) · [Releases](https://github.com/capskov/luna-cad-sheet-layout/releases). A distribution license has not yet been selected; this package does not assert an open-source redistribution grant.
