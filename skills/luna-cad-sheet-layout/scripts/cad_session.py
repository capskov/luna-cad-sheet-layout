"""Explicit AutoCAD COM session. No app restart, global patch, or implicit save.

Inherited native operations were field-tested on 2022. Selecting a 2026 ProgID
does not certify those operations on 2026; see references/validation.md.
"""
from pathlib import Path
import json
import math
import os
import time
import pythoncom
import win32com.client

BUSY = {-2147418111, -2147417846}


def retry(fn, label):
    for attempt in range(31):
        try:
            return fn()
        except pythoncom.com_error as exc:
            if exc.hresult not in BUSY or attempt == 30:
                print(json.dumps({'failed_call': label, 'hresult': exc.hresult,
                                  'error': str(exc)}, ensure_ascii=False), flush=True)
                raise
            print(f'BUSY {label}: {exc.hresult}, retry {attempt + 1}/30', flush=True)
            time.sleep(.5)


def raw(obj):
    return getattr(obj, '_oleobj_', obj)


def invoke(obj, name, kind, *args):
    ole = raw(obj)
    dispid = retry(lambda: ole.GetIDsOfNames(name), f'{name}:lookup')
    args = tuple(raw(a) if hasattr(a, '_oleobj_') else a for a in args)
    result = retry(lambda: ole.Invoke(dispid, 0, kind, kind != 4, *args), name)
    if hasattr(result, 'Invoke'):
        return retry(lambda: win32com.client.Dispatch(result), f'{name}:wrap')
    return result


def get(obj, name):
    return invoke(obj, name, pythoncom.DISPATCH_PROPERTYGET)


def put(obj, name, value):
    # AutoCAD's typelib declares these setters PROPERTYPUT (4), not PUTREF (8).
    # Direct dispatch preserves HRESULT; dynamic.__setattr__ can hide it.
    return invoke(obj, name, pythoncom.DISPATCH_PROPERTYPUT, value)


def call(obj, name, *args):
    return invoke(obj, name, pythoncom.DISPATCH_METHOD, *args)


def point(*coords):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, coords)


class Session:
    def __init__(self, dwg, work_dir, allow_read_only=False, *, progid='AutoCAD.Application.24.1'):
        target = Path(dwg)
        output = Path(work_dir)
        if not target.is_absolute() or not output.is_absolute():
            raise ValueError('dwg and work_dir must be absolute paths.')
        self.target = target.resolve()
        self.work_dir = output.resolve()
        if not self.target.is_file():
            raise FileNotFoundError(self.target)
        if progid not in ('AutoCAD.Application.24.1', 'AutoCAD.Application.25.1'):
            raise ValueError('Explicit supported ProgID required: 24.1 (2022) or 25.1 (2026).')
        self.progid = progid
        self.inspection_only = bool(allow_read_only)
        pythoncom.CoInitialize()
        self.app = retry(lambda: win32com.client.GetActiveObject(progid), 'connect')
        docs = get(self.app, 'Documents')
        matches = []
        for i in range(get(docs, 'Count')):
            d = call(docs, 'Item', i)
            if os.path.normcase(str(Path(get(d, 'FullName')).resolve())) == os.path.normcase(str(self.target)):
                matches.append(d)
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one already-open target DWG; no file was opened or closed.')
        self.doc = matches[0]
        self.read_only = bool(get(self.doc, 'ReadOnly'))
        if self.read_only and not allow_read_only:
            raise RuntimeError('Target DWG is read-only.')
        self.idle()
        if self.var('CMDACTIVE') != 0:
            raise RuntimeError('An AutoCAD command is active. Do not cancel user work.')

    def require_writable(self):
        if self.read_only or getattr(self, 'inspection_only', False):
            raise RuntimeError('Read-only inspection session cannot change layout/view/save/plot.')

    def var(self, name):
        return call(self.doc, 'GetVariable', name)

    def idle(self):
        for _ in range(31):
            if get(call(self.app, 'GetAcadState'), 'IsQuiescent'):
                return
            time.sleep(.5)
        raise RuntimeError('AutoCAD did not become idle within 15 seconds.')

    def settle(self):
        # State transitions can briefly reject COM even before IsQuiescent changes.
        time.sleep(.2)
        self.idle()
        if self.var('CMDACTIVE') != 0:
            raise RuntimeError('An unexpected command is active; stop before further writes.')

    def layout(self, name):
        return call(get(self.doc, 'Layouts'), 'Item', name)

    def viewport(self, layout, handle):
        block = get(layout, 'Block')
        for i in range(get(block, 'Count')):
            entity = call(block, 'Item', i)
            if get(entity, 'Handle').upper() == handle.upper():
                if get(entity, 'ObjectName') != 'AcDbViewport':
                    raise RuntimeError('The requested handle is not a viewport.')
                return entity
        raise RuntimeError('Viewport handle is not in the requested layout.')

    def paper(self):
        self.require_writable()
        if get(self.doc, 'MSpace'):
            put(self.doc, 'MSpace', False)
            self.settle()
        if self.var('CVPORT') != 1:
            raise RuntimeError('Paper-space verification failed.')

    def select_layout(self, layout_name):
        self.require_writable()
        call(self.doc, 'Activate')
        self.settle()
        layout = self.layout(layout_name)
        if get(self.doc, 'ActiveSpace') != 0:
            put(self.doc, 'ActiveSpace', 0)
            self.settle()
        self.paper()
        if get(get(self.doc, 'ActiveLayout'), 'Name') != layout_name:
            put(self.doc, 'ActiveLayout', layout)
            self.settle()
        return layout

    def checked_work_viewport(self, layout_name, handle):
        """Select layout and validate DXF69 BEFORE any work-viewport setters.

        Selection may change view state; this is not a read-only snapshot.
        Use the returned object for sizing/layer/lock/display changes only after
        this method succeeds. Overall viewport number 1 is always rejected.
        """
        layout = self.select_layout(layout_name)
        vp = self.viewport(layout, handle)
        if (self.viewport_numbers([handle])[handle] or 0) <= 1:
            raise RuntimeError('Not a verified work viewport; no viewport setters allowed.')
        return layout, vp

    def activate(self, layout_name, handle):
        layout = self.select_layout(layout_name)
        vp = self.viewport(layout, handle)
        # Inactive layouts can report native number 0 and ViewportOn=False.
        # Query only AFTER selecting this layout, before touching the viewport.
        if (self.viewport_numbers([handle])[handle] or 0) <= 1:
            raise RuntimeError('Selected layout: DXF 69 does not identify a work viewport. Do not unlock/reshape it.')
        if get(vp, 'DisplayLocked'):
            put(vp, 'DisplayLocked', False)
        if not get(vp, 'ViewportOn'):
            call(vp, 'Display', True)
        self.settle()
        if not get(self.doc, 'MSpace'):
            # A displayed viewport outside the current paper view cannot be
            # activated on this CAD instance. Frame it in PAPER space first.
            c = get(vp, 'Center')
            w, h = get(vp, 'Width'), get(vp, 'Height')
            call(self.app, 'ZoomWindow', point(c[0]-w*.55, c[1]-h*.55, 0.0),
                 point(c[0]+w*.55, c[1]+h*.55, 0.0))
            call(self.doc, 'Regen', 1)
            self.settle()
            put(self.doc, 'MSpace', True)
            self.settle()
        active_handle = get(get(self.doc, 'ActivePViewport'), 'Handle')
        if active_handle.upper() != handle.upper():
            put(self.doc, 'ActivePViewport', vp)
            self.settle()
        if not get(self.doc, 'MSpace') or self.var('CVPORT') <= 1:
            raise RuntimeError('Model viewport was not activated.')
        if get(get(self.doc, 'ActivePViewport'), 'Handle').upper() != handle.upper():
            raise RuntimeError('The active viewport is not the requested handle.')
        return layout, vp

    def view_state(self, vp):
        if not get(self.doc, 'MSpace') or get(get(self.doc, 'ActivePViewport'), 'Handle') != get(vp, 'Handle'):
            raise RuntimeError('VIEWCTR/VIEWSIZE describe only the active model viewport; activate this handle first.')
        return {'layout': get(get(self.doc, 'ActiveLayout'), 'Name'),
                'handle': get(vp, 'Handle'), 'MSpace': get(self.doc, 'MSpace'),
                'CVPORT': self.var('CVPORT'), 'view_center': self.var('VIEWCTR'),
                'view_height': self.var('VIEWSIZE'),
                'paper_center': get(vp, 'Center'), 'paper_width': get(vp, 'Width'),
                'paper_height': get(vp, 'Height'), 'scale': get(vp, 'CustomScale'),
                'direction': get(vp, 'Direction'), 'twist': get(vp, 'TwistAngle'),
                'locked': get(vp, 'DisplayLocked'), 'on': get(vp, 'ViewportOn')}

    def viewport_numbers(self, handles):
        """Read DXF 69 via native AutoLISP; no entities or layers are modified."""
        if not handles or any(not h or any(c not in '0123456789ABCDEFabcdef' for c in h) for h in handles):
            raise ValueError('Expected hexadecimal entity handles.')
        self.idle()
        if self.var('CMDACTIVE') != 0:
            raise RuntimeError('Cannot send a read-only query during an active command.')
        if os.path.normcase(get(get(self.app, 'ActiveDocument'), 'FullName')) != os.path.normcase(str(self.target)):
            raise RuntimeError('Activate the target document before a native query.')
        self.work_dir.mkdir(parents=True, exist_ok=True)
        output = self.work_dir / f'viewport-numbers-{time.time_ns()}.txt'
        lisp_path = output.as_posix().replace('"', '\\"')
        quoted = ' '.join(f'"{h}"' for h in handles)
        command = ('((lambda (/ f h e n) '
                   f'(setq f (open "{lisp_path}" "w")) '
                   f'(foreach h (list {quoted}) '
                   '(setq e (entget (handent h)) n (cdr (assoc 69 e))) '
                   '(write-line (strcat h "|" (if n (itoa n) "UNKNOWN")) f)) '
                   '(close f) (princ)))\n')
        call(self.doc, 'SendCommand', command)
        self.settle()
        for _ in range(30):
            if output.exists():
                rows = output.read_text(encoding='ascii').strip().splitlines()
                if len(rows) == len(handles):
                    break
            time.sleep(.5)
        else:
            raise RuntimeError('Read-only viewport query did not finish; do not resend automatically.')
        return {h: int(n) if n != 'UNKNOWN' else None for h,n in (row.split('|') for row in rows)}

    def viewport_snapshot(self, handles):
        """Read DXF view/frozen-layer state without activating/unlocking any viewport.

        view_center is DXF12 in DCS, NOT a WCS model center for fit().

        The document must already be active. DXF69 can be zero on inactive layouts;
        this snapshot is not permission to mutate such a viewport.
        """
        if not handles or any(not h or any(c not in '0123456789ABCDEFabcdef' for c in h) for h in handles):
            raise ValueError('Expected hexadecimal viewport handles.')
        self.idle()
        if self.var('CMDACTIVE') != 0:
            raise RuntimeError('Cannot query during an active command.')
        if os.path.normcase(get(get(self.app, 'ActiveDocument'), 'FullName')) != os.path.normcase(str(self.target)):
            raise RuntimeError('Target document must already be active; snapshot does not activate it.')
        before = self.var('DBMOD')
        self.work_dir.mkdir(parents=True, exist_ok=True)
        output = self.work_dir / f'viewport-state-{time.time_ns()}.txt'
        path = output.as_posix().replace('"', '\\"')
        quoted = ' '.join(f'"{h}"' for h in handles)
        expression = ('((lambda (/ f h e c p n) '
            f'(setq f (open "{path}" "w")) '
            f'(foreach h (list {quoted}) '
            '(setq e (entget (handent h))) '
            '(if (= (cdr (assoc 0 e)) "VIEWPORT") '
            '(progn (setq c (cdr (assoc 12 e)) n (cdr (assoc 69 e))) '
            '(write-line (strcat "V\\t" h "\\t" (if n (itoa n) "0") "\\t" '
            '(rtos (car c) 2 12) "\\t" (rtos (cadr c) 2 12) "\\t" '
            '(rtos (cdr (assoc 45 e)) 2 12)) f) '
            '(foreach p e (if (= (car p) 331) '
            '(write-line (strcat "F\\t" h "\\t" (cdr (assoc 2 (entget (cdr p))))) f)))) '
            '(write-line (strcat "ERROR\\t" h) f))) '
            '(write-line "DONE" f) (close f) (princ)))\n')
        call(self.doc, 'SendCommand', expression)
        self.settle()
        rows = output.read_text(encoding='utf-8', errors='replace').splitlines() if output.exists() else []
        if not rows or rows[-1] != 'DONE':
            raise RuntimeError(f'Incomplete native query: {output}; inspect command history, do not resend blindly.')
        result = {}
        for line in rows[:-1]:
            cols = line.split('\t')
            if cols[0] == 'V':
                _, h, n, x, y, height = cols
                result[h] = {'number': int(n), 'view_center': [float(x), float(y)],
                             'view_height': float(height), 'view_center_coordinate_system': 'DCS (DXF12), not WCS; do not pass to fit', 'frozen_layers': []}
            elif cols[0] == 'F':
                result[cols[1]]['frozen_layers'].append(cols[2])
            else:
                raise RuntimeError(f'Invalid viewport query row: {line}')
        if set(result) != set(handles):
            raise RuntimeError('Native query did not return exactly the requested viewports.')
        if self.var('DBMOD') != before:
            raise RuntimeError('Unexpected DBMOD change during read-only snapshot; inspect before saving.')
        return result

    def freeze_layers_current(self, layout_name, handle, layer_names):
        """Freeze verified display-only layers in this viewport; no implicit save.

        Confirm these layers contain no engineering content before calling.
        Idempotent via DXF331, not VPLAYEROVERRIDES. Restores original lock.
        """
        self.require_writable()
        if not layer_names or any(not n or any(c in n for c in '\n\r\t,;*?"') for n in layer_names):
            raise ValueError('Use explicit layer names, without wildcards or delimiters.')
        layout = self.select_layout(layout_name)
        vp = self.viewport(layout, handle)
        previous_lock = get(vp, 'DisplayLocked')
        before = self.viewport_snapshot([handle])[handle]
        if before['number'] <= 1:
            raise RuntimeError('Not an active-layout work viewport.')
        missing = [n for n in layer_names if n.casefold() not in {x.casefold() for x in before['frozen_layers']}]
        if not missing:
            return {'changed': False, **before}
        for name in missing:
            call(get(self.doc, 'Layers'), 'Item', name)
        try:
            self.activate(layout_name, handle)
            names = ','.join(missing).replace('\\', '\\\\')
            # The final empty input exits VPLAYER's option loop.
            expression = f'(progn (command "_.VPLAYER" "_Freeze" "{names}" "_Current" "") (princ))\n'
            call(self.doc, 'SendCommand', expression)
            self.settle()
            after = self.viewport_snapshot([handle])[handle]
            if not {n.casefold() for n in layer_names}.issubset({n.casefold() for n in after['frozen_layers']}):
                raise RuntimeError(f'Frozen layer verification failed: {after}')
            return {'changed': True, **after}
        finally:
            # If the command is still active, preserve the scene rather than injecting recovery input.
            if get(call(self.app, 'GetAcadState'), 'IsQuiescent') and self.var('CMDACTIVE') == 0:
                self.paper()
                put(vp, 'DisplayLocked', previous_lock)

    def fit(self, layout_name, handle, center, scale):
        if len(center) != 2 or not all(math.isfinite(x) for x in (*center, scale)) or scale <= 0:
            raise ValueError('Invalid center/scale.')
        # Reject unsupported views before activate() can unlock a viewport.
        vp = self.viewport(self.layout(layout_name), handle)
        if abs(get(vp, 'TwistAngle')) > 1e-8 or tuple(get(vp, 'Direction')) != (0.0, 0.0, 1.0):
            raise RuntimeError('This fit helper is verified only for untwisted top views.')
        layout, vp = self.activate(layout_name, handle)
        view_height = get(vp, 'Height') / scale
        call(self.app, 'ZoomCenter', point(*center, 0.0), float(view_height))
        self.settle()
        put(vp, 'CustomScale', float(scale))
        self.settle()
        state = self.view_state(vp)
        if abs(state['view_height'] - view_height) > .01 or any(abs(a-b) > .01 for a,b in zip(state['view_center'], center)):
            raise RuntimeError(f'View geometry did not match the requested fit: {state}')
        self.paper()
        put(vp, 'DisplayLocked', True)
        self.settle()
        call(self.doc, 'Regen', 1)
        self.settle()
        if not get(vp, 'DisplayLocked') or not get(vp, 'ViewportOn'):
            raise RuntimeError('Viewport was not left locked and visible.')
        state['locked'] = True
        state['measurement_context'] = 'view_center/view_height measured inside the target model viewport; other final fields describe paper-space completion'
        state['MSpace'] = False
        state['CVPORT'] = self.var('CVPORT')
        state['finished_in_paper_space'] = self.var('CVPORT') == 1
        return state

    def configure_a3(self, layout_name):
        layout = self.select_layout(layout_name)
        self.paper()
        put(layout, 'ConfigName', 'DWG To PDF.pc3')
        call(layout, 'RefreshPlotDeviceInfo')
        self.settle()
        for name,value in [('CanonicalMediaName','ISO_full_bleed_A3_(420.00_x_297.00_MM)'),
                           ('PlotRotation',0),('PaperUnits',1)]:
            put(layout,name,value)
        call(layout,'SetWindowToPlot',point(0.0,0.0),point(420.0,297.0))
        for name,value in [('PlotType',4),('UseStandardScale',False),
                           ('CenterPlot',True),('StyleSheet','monochrome.ctb'),
                           ('PlotWithPlotStyles',True),('PlotWithLineweights',True)]:
            put(layout,name,value)
        call(layout, 'SetCustomScale', 1.0, 1.0)
        self.settle()

    def save(self):
        self.require_writable()
        self.idle()
        call(self.doc, 'Save')
        self.settle()
        if self.var('DBMOD') != 0:
            raise RuntimeError('DWG still reports unsaved changes after Save.')

    def plot(self, layout_name, output):
        self.require_writable()
        destination = Path(output)
        if not destination.is_absolute() or destination.exists():
            raise ValueError('Use a new absolute PDF path; existing evidence is not overwritten.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if get(get(self.doc, 'ActiveLayout'), 'Name') != layout_name:
            raise RuntimeError('Requested plot layout is not active.')
        self.paper()
        old_bg = self.var('BACKGROUNDPLOT')
        primary_error = None
        try:
            call(self.doc, 'SetVariable', 'BACKGROUNDPLOT', 0)
            result = call(get(self.doc, 'Plot'), 'PlotToFile', str(Path(output).resolve()), 'DWG To PDF.pc3')
            self.settle()
            if not result or not Path(output).is_file():
                raise RuntimeError('Plot did not create the requested PDF.')
        except Exception as exc:
            primary_error = exc
            raise
        finally:
            try:
                call(self.doc, 'SetVariable', 'BACKGROUNDPLOT', old_bg)
            except Exception as cleanup_error:
                if primary_error is None:
                    raise
                print(f'SECONDARY cleanup error: {cleanup_error}', flush=True)
