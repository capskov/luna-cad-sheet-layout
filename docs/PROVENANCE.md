# 来源与迁移范围

此技能由作者本地的cad-frame-321 2.0.0（2026-09-28）经验包改造，现使用新ID luna-cad-sheet-layout，避免覆盖旧工程技能。

继承cad_session.py、inspect_cad.py、compare_model_inventory.py及相关离线测试；Session新增显式版本连接、只读会话保护，fit调整不支持视图的拒绝时机，inspect增加必填版本参数。原项目专用prepare_test与独立复测夹具不迁入通用包，因为它们依赖固定工程输入，不适合新项目。

从原工作流和故障记录提炼一般经验，重新组织为简明入口、分步指南、按症状查坑及目录维护说明。没有携带原图、项目坐标表、用户签名、字体或具体工程目录。历史CAD验证与本轮离线验证分别列出，不继承为新版全流程认证。

底座相关能力表仅为本地1.2.0-beta.1的接入评估，未复制或分发底座运行时，也没有新增MCP写入工具。

开发阶段曾用ID为cad-sheet-framing及luna-cad-framing-agent，曾用展示名为Luna CAD Framing Agent。现统一为Luna CAD Sheet Layout，中文名称为Luna CAD 智能体套图排版技能，仓库与Skill ID均为luna-cad-sheet-layout。旧名称仅保留在此溯源，当前入口、安装目录和候选包全部使用新名称。更名未改变执行脚本或扩大验证范围。
