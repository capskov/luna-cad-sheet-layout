"""Offline behavior checks for freeze success criteria and inspection side effects."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import cad_session as cad

class ViewportContracts(unittest.TestCase):
    def session(self):
        s=cad.Session.__new__(cad.Session)
        s.read_only=False; s.doc=object(); s.app=object()
        s.target=Path('C:/test/only.dwg')
        s.idle=lambda:None; s.settle=lambda:None; s.var=lambda _:0
        return s

    def test_frozen_layer_skip_does_not_unlock_or_send_command(self):
        s=self.session(); vp=object()
        s.select_layout=lambda _:object(); s.viewport=lambda *_:vp
        s.viewport_snapshot=lambda _: {'A':{'number':2,'frozen_layers':['FRAME']}}
        s.activate=Mock();s.paper=Mock()
        with patch.object(cad,'get',return_value=True),patch.object(cad,'put') as put,patch.object(cad,'call') as call:
            result=s.freeze_layers_current('sheet','A',['frame'])
            self.assertFalse(result['changed']);s.activate.assert_not_called();put.assert_not_called();call.assert_not_called()

    def test_freeze_uses_layer_list_and_restores_lock(self):
        s=self.session(); vp=object(); layout=object(); state={'locked':True,'frozen':[]}; commands=[]
        s.select_layout=lambda _:layout;s.viewport=lambda *_:vp
        s.viewport_snapshot=lambda _: {'A':{'number':2,'frozen_layers':list(state['frozen'])}}
        def activate(*_): state['locked']=False; return layout,vp
        s.activate=activate;s.paper=lambda:None
        def getter(obj,name):
            if name=='DisplayLocked': return state['locked']
            if name=='IsQuiescent': return True
            return object()
        def caller(obj,name,*args):
            if name=='SendCommand': commands.append(args[0]);state['frozen']=['FRAME']
            return object()
        def setter(obj,name,value):
            if name=='DisplayLocked':state['locked']=value
        with patch.object(cad,'get',getter),patch.object(cad,'call',caller),patch.object(cad,'put',setter):
            result=s.freeze_layers_current('sheet','A',['FRAME'])
        self.assertTrue(result['changed']);self.assertTrue(state['locked']);self.assertIn('"_Current" ""',commands[0])
        self.assertEqual(result['frozen_layers'],['FRAME'])

    def test_checked_work_viewport_rejects_overall_before_setters(self):
        s=self.session();s.select_layout=lambda _:object();s.viewport=lambda *_:object()
        s.viewport_numbers=lambda _: {'A':1}
        with patch.object(cad,'put') as setter:
            with self.assertRaises(RuntimeError):s.checked_work_viewport('sheet','A')
            setter.assert_not_called()

    def test_overall_viewport_never_frozen(self):
        s=self.session();s.select_layout=lambda _:object();s.viewport=lambda *_:object()
        s.viewport_snapshot=lambda _: {'A':{'number':1,'frozen_layers':[]}}
        with patch.object(cad,'get',return_value=True),patch.object(cad,'call') as call:
            with self.assertRaises(RuntimeError):s.freeze_layers_current('sheet','A',['FRAME'])
            call.assert_not_called()

    def test_snapshot_reads_without_setter_or_activation(self):
        s=self.session();s.activate=Mock();s.select_layout=Mock()
        with tempfile.TemporaryDirectory() as directory:
            s.work_dir=Path(directory)
            def getter(obj,name):
                if name=='FullName':return str(s.target)
                return object()
            def caller(obj,name,*args):
                self.assertEqual(name,'SendCommand')
                (s.work_dir/'viewport-state-123.txt').write_text('V\tA\t2\t1.5\t2.5\t262\nF\tA\tFRAME\nDONE\n',encoding='utf-8')
            with patch.object(cad,'get',getter),patch.object(cad,'call',caller),patch.object(cad,'put') as put,patch.object(cad.time,'time_ns',return_value=123):
                result=s.viewport_snapshot(['A'])
                put.assert_not_called()
            self.assertEqual(result['A']['view_center'],[1.5,2.5]);self.assertEqual(result['A']['frozen_layers'],['FRAME'])
            s.activate.assert_not_called();s.select_layout.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
