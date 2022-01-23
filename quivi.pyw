#!/usr/bin/env python


def run():
    import sys
    #import wxversion
    #I'd like to require 2.8.9.0 but on Ubuntu it just records the first two numbers...
    #if not hasattr(sys, 'frozen'):
    #    wxversion.ensureMinimal('2.8')
    import wx
    
    import traceback
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    from quivilib.control.main import MainController
    from quivilib.control.file_association import parse_command_line
    from quivilib.gui.error import ErrorDialog
    from pathlib import Path as Path
    from quivilib import util
    
    
    class MyApp(wx.App):
        def __init__(self, redir, script, argv):
            self.script = script
            self.argv = argv
            wx.App.__init__(self, redir)
            
        def OnInit(self):
            try:
                file_to_open = None
                if len(self.argv) > 1:
                    file_to_open = Path(self.argv[1])
                self.controller = MainController(self.script, file_to_open)
                self.SetTopWindow(self.controller.view)
                self.controller.view.Show(True)
                return True
            except Exception as e:
                tb = traceback.format_exc()
                msg, tb = util.format_exception(e, tb)
                logging.error(tb)
                print(traceback.format_exc())##
                dlg = ErrorDialog(parent=None, error=msg, tb=tb)
                dlg.ShowModal()
                dlg.Destroy()
            return False
    
    try:
        script = __file__
        script = Path(script)
        script = script.resolve()
    except NameError:
        script = None

    argv = sys.argv
    
    try:
        if not parse_command_line(argv, script):
            app = MyApp(redir=False, script=script, argv=argv)
            #wx.CallAfter(app.controller.view.Destroy)
            app.MainLoop()
    except:
        logging.error(traceback.format_exc())

if __name__ == '__main__':
#    import cProfile
#    cProfile.run('run()', 'temp.prof')
#    from pstats import Stats
#    stats = Stats("temp.prof")
#    stats.sort_stats('time').print_stats().sort_stats('time').print_callers()
    run()
