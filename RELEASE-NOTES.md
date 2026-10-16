# v3.0.0-beta.1 — Luna CAD Sheet Layout

**An AI Agent Skill for AutoCAD Sheet Layout, Title Blocks & Drawing Index Management**

This beta turns single-project AutoCAD framing experience into a reusable Skill for existing AI agents. It targets the final preparation stage after engineering design and CAD drafting: arrange sheets, attach suitable title-block Xrefs, frame and scale viewports, and reconcile drawing titles, numbers and the index.

## Included

- Low-compute guided mode by default, with clear steps, existing native helpers and targeted failure/recovery notes.
- High-compute concise mode, leaving capable agents room to plan and execute; no prescribed model names.
- Guidance for finding drawings, continuing correct existing sheets, adding/removing/rearranging sheets and updating affected index entries.
- Real AutoCAD lessons: overall viewport protection, Xref load failures, insertion-unit scaling, viewport freezing, clipping remnants and inspection side effects.
- Explicit backend selection: reuse CAD Agent Foundation where supported and retain native COM for remaining operations.
- Read-only frame/date candidates, explicit CAD version selection, inspection-only session protection and unsupported-view rejection before viewport activation.

## Naming and packaging

Project: **Luna CAD Sheet Layout**. Chinese name: **Luna CAD 智能体套图排版技能**. Repository and Skill ID: **`luna-cad-sheet-layout`**. Install and invoke `$luna-cad-sheet-layout`; replace earlier development-name installations rather than keeping duplicate generic entries. Original project-specific skills may remain separate.

Repository and skill-only ZIPs use the new name. Execution scripts and historical test evidence are retained; this naming/documentation update does not alter execution logic. Earlier names appear only in provenance and local archive notices.

## Evidence and limits

Historical evidence comes from AutoCAD 2022 COM work, including a visually reviewed project sheet and checks of original model objects. The current 18 targeted offline tests are distinct from CAD field validation. AutoCAD 2026 has an explicit connection option but **the new Skill has not completed 2026 sheet-layout field validation**. No lower-compute independent success rate or compute-saving percentage is claimed.

Foundation-only framing remains incomplete in assessed local 1.2.0-beta.1; no Foundation APIs were added. Rotated/3D viewport fitting remains unsupported. Existing Foundation save-verification protection is preserved.

## 中文摘要

面向已完成设计的施工图收尾，提供低算力分步与高算力简明双模式，指导智能体套框、排版、维护图签和目录。原生脚本及踩坑经验保留；更名与介绍优化不等于新增2026实图验收。以beta预发布形式分发，2026实图验证及其他未验证能力保持原有说明。
