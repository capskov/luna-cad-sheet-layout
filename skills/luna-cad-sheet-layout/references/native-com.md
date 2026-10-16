# 原生COM路径：明确参数后执行局部操作

Windows、已安装AutoCAD及Python的pywin32是条件。安装第三方依赖按运行环境正常方式处理，不自动下载CAD、字体或图框。以下为API配方，Agent应把实际参数写成小脚本；不是自动批量执行器。

## 连接与清点

```text
python scripts/inspect_cad.py --dwg "<已打开DWG绝对路径>" --out "<新的清点JSON绝对路径>" --progid AutoCAD.Application.24.1
```

2022使用24.1，2026使用25.1。本次增加显式版本选择，不代表2026套框全流程已实测。helper仅连接该版本的已运行COM实例，枚举Documents精确匹配路径；找不到就失败，不打开新图、不切到另一CAD版本。多个同版本实例若目标不在连接实例中，明确报告，不能偷偷换到别的图。

inspect不调用SendCommand、切布局、保存或解锁。输出布局/直属实体/文字/块属性/视口纸上尺寸等；属性错误逐项记录，不把错误当“无对象”。实体块内部、代理及部分标注不属完整清点覆盖。

本轮脚本从实际技能路径加入scripts到sys.path，再导入：

```python
from cad_session import Session, get, put, call, point
s = Session(target_absolute_path, evidence_absolute_dir,
            progid='AutoCAD.Application.24.1')
# 只读会话使用allow_read_only=True，其修改方法会拒绝执行。
```

`get/put/call`保留HRESULT，只对已知COM拒绝忙碌码有限重试；不要自己再套无限重试。任何创建/保存结果未知先查状态。helper不提供底座事务日志，不是底座MCP。

## 布局与工作视口

```python
# 先枚举Layouts确认确实缺少；不要反复Add。
layout = call(get(s.doc, 'Layouts'), 'Add', confirmed_new_layout_name)
# Add后重新枚举layout.Block，CAD可能自动创建整体/默认工作视口。
layout = s.select_layout(confirmed_layout_name)
```

新建工作视口（纸空间坐标与宽高由Agent给出）：

```python
vp = call(get(layout, 'Block'), 'AddPViewport', point(px, py, 0.0), paper_width, paper_height)
handle = get(vp, 'Handle')  # 立即记录；结果不明时重新清点差集，不能直接重建。
put(vp, 'Layer', confirmed_nonplot_layer)  # 图层已存在并核实不打印
call(vp, 'Display', True)
call(s.doc, 'Regen', 1)
s.settle()
layout, vp = s.checked_work_viewport(confirmed_layout_name, handle)
state = s.fit(confirmed_layout_name, handle, model_wcs_center_xy, custom_scale)
```

已有视口的任何setter（含层、尺寸、锁定、显示）先调用checked_work_viewport。整体编号1拒绝，未知0/None不猜。fit仅支持未扭转俯视图，会先拒绝不支持视图再激活；已有取景合适时不调用fit。

`activate`会切布局、解锁，是写入上下文。只读用`viewport_snapshot([handle])`，要求目标文档已经活动；DXF12是DCS，只能比同一视口状态，不能当模型WCS中心传fit。VIEWCTR/VIEWSIZE必须在目标工作视口活动后读。

## 外参图框

```python
layout = s.select_layout(layout_name)
ref = call(get(layout, 'Block'), 'AttachExternalReference',
           confirmed_frame_absolute_path, unique_reference_name,
           point(ix, iy, iz), sx, sy, sz, rotation_radians, False)
frame_handle = get(ref, 'Handle')
```

路径、图框身份、插入点、尺度由Agent确认。读取bbox需pywin32的ByRef输出支持，沿用`ref.GetBoundingBox()`与明确错误记录；不能以Path存在证明已加载。可在确认携带依赖后设Path为相对路径，重新检查实际解析与画面。

同图已解析引用可复用。跨DWG曾出现CopyObjects后空bbox、PDF无框，优先在目标重新Attach，只复制明确需要的图签对象。单位换算可能改变实插尺寸：量得1000倍且已确认应为A3时才给ScaleEntity具体校正参数，不硬编码0.001，不改变INSUNITS。

## 图签、增减页与局部隐藏

在layout.Block定位Text/MText及块属性。分别绑定图名、图号、当前页、总页等字段；普通文字用`put(text, 'TextString', value)`，块属性先按tag定位后写TextString。保持原字型与对齐，签名不改。更新后读回文字，字体宽窄变化由Agent看图调整。

可复制已核实的必要图签，避免重建Standard字体。跨图CopyObjects需要`VARIANT(VT_ARRAY|VT_DISPATCH, source_objects)`及目标Block，先小样本核实，不复制整个工作视口。复制返回不明确按前后句柄差集识别，不重放。

增加/减少图幅按catalogue维护。明确删除的布局使用`call(s.layout(name), 'Delete')`，执行前核实不是Model、身份匹配且有工作副本检查点，删除后重新枚举；不调用实体全删，不删源DWG。helper未把增删和目录同步包装成一键功能。

隐藏旧框仅对确认不含工程内容的层：

```python
result = s.freeze_layers_current(layout_name, work_viewport_handle, explicit_layer_names)
```

此方法先查DXF331，只冻结本视口并恢复原锁定，不保存。不用全局Layer.Freeze或VPLAYEROVERRIDES当替代。它通过COM SendCommand执行固定原生Lisp查询/命令，属于本后端实现，不能转用来绕过底座限制。

## 打印与保存

`s.configure_a3(layout_name)`仅适用于已确认的420×297毫米纸空间窗口、DWG To PDF.pc3、monochrome.ctb配置，不能每个项目无条件调用。其他纸幅从实际可用介质选取并明确设置；不猜介质字符串存在。

自定义窗口按`SetWindowToPlot(point(x0,y0),point(x1,y1))`后PlotType=4；纸张单位、方向、设备和介质由Agent确认，再设置UseStandardScale=False、SetCustomScale(1,1)等实际所需参数。纸空间1:1打印不等于工程模型1:1。模型单位含义必须有几何/标注依据，横纵比例也可能不同。

```python
s.save()  # 仅保存已追踪且获授权的修改；DBMOD=0不是几何校验。
s.plot(layout_name, new_absolute_pdf_path)  # 目标布局必须已活动；不覆盖旧PDF。
s.save()  # 打印临时变量恢复可能改变已知状态；需要时保存。
```

保存helper只检查命令完成及DBMOD，不提供磁盘语义读回保证。按用户抽查要求看CAD或渲染PDF；必要时重新打开自己控制的检查副本核对。不要把API成功、PDF存在或字段一致夸成图面已通过。
