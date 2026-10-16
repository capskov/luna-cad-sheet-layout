# 本地发布准备 · 2026-10-16

## 已整理

- 项目Luna CAD Sheet Layout，中文名称Luna CAD 智能体套图排版技能，仓库与技能ID均为luna-cad-sheet-layout，版本3.0.0-beta.1。
- 从项目专用2.0.0泛化为双指导密度入口，默认服务低算力Agent，不强制模型路由。
- 源码、技能、英文优先README、独立中文介绍、GitHub Description/Topics、发布说明与验证范围独立成库；旧工程技能和原工程保留，开发阶段通用技能安装仅保留新名称。
- 仓库不包含工程DWG、商业字体、用户签名、CAD运行日志、NAS连接或凭证。
- 用户已于2026-10-16授权补充ai-agents及agent-skill关键词，并发布到GitHub和本地NAS仓库。

## 发布前应明确的实际状态

可以作为**技能流程与原生助手的beta候选**介绍；不能作为2026已完成实机验收或底座MCP全流程套框产品发布。2026实测后再补相应证据；如先发布beta，保留现有验证说明。

仓库名已确定为luna-cad-sheet-layout。GitHub归属、公开范围与许可证在最终发布时确定；不擅自授予作者的开源再分发许可，不附带第三方工程图、字体或签名模板。

## 底座是否需要研究

当前完整套框缺纸空间枚举/写入、布局、工作视口及外参挂接原语，不是一个参数补丁能解决。本轮先让技能可沿明确原生路径执行，未修改底座，避免把技能改造扩大成底座新阶段。需要全程MCP时，再以单页闭环为限定任务补基础原语；算法和排版仍由Agent处理。

底座字体保存限制已有真实问题且用户接受正常字体变化；此次只在技能明确验收口径与现有阻塞，不把文档变更当作底座修复，不解除或绕过已有保护。

## 发布简介草稿

Luna CAD Sheet Layout是一份给智能体使用的CAD收尾实战指南：设计人完成图纸后，Agent依据目录和已确认的最新图框外参，组织图幅、配置取景与比例，并统一图号图名。默认分步指导帮助算力有限的Agent按现场证据推进；能力更强的Agent可选择简明主线。真实踩坑按症状查阅，已有正确页面可以续作，不必从头再套。

英文定位：**An AI Agent Skill for AutoCAD Sheet Layout, Title Blocks & Drawing Index Management**。英文首页在README.md，中文介绍在README.zh-CN.md；可直接采用的Description和Topics见[GITHUB-METADATA.md](GITHUB-METADATA.md)。

## 本轮检查与本地Git

18项已有针对性离线测试重新通过，7个Python脚本内容哈希与更名前一致；结构、链接、元数据、调用示例、3个命令帮助入口及Python编译检查通过。没有为了更名重复CAD图面测试，2026实图验证仍未完成。

发布目标为GitHub capskov/luna-cad-sheet-layout及NAS同名Git仓库，使用main分支与v3.0.0-beta.1版本标签，GitHub标记为prerelease。实际提交号、远端核对和附件校验结果记录在本地发布回执。仓库ZIP与技能专用ZIP分别打包，包名与顶层入口使用luna-cad-sheet-layout；安装副本逐文件核对。详细检查结果和包SHA256保存在本地候选包配套记录中，不包含工程DWG或私有测试产物。
