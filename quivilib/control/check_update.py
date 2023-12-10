from threading import Thread
from datetime import datetime
import traceback
import logging

from pubsub import pub as Publisher
import wx

from quivilib import meta

log = logging.getLogger('check_update')

_DATE_FMT = '%Y-%m-%d %H:%M'


def _is_version_newer(last, current):
    last = [int(n) for n in last.split('.')]
    current = [int(n) for n in current.split('.')]
    return last > current 

class UpdateChecker(object):
    def __init__(self, settings):
        self.settings = settings
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def run(self):
        try:
            avail = self.settings.get('Update', 'Available')
            url = self.settings.get('Update', 'URL')
            version = self.settings.get('Update', 'Version')
            
            last_check = self.settings.get('Update', 'LastCheck')
            if last_check:
                last_check = datetime.strptime(last_check, _DATE_FMT)
                diff = datetime.today() - last_check
                
            if not last_check or diff.days > 0:
                log.debug('Checking for updates...')
                info = self._get_update_info(meta.UPDATE_URL)
                self._check_update(*info)
            elif avail != '0' and url and version and _is_version_newer(version, meta.VERSION):
                self._notify_update(url, None, None)
            else:
                self._no_update(None)
                
        except:
            log.error(traceback.format_exc())
            
    def _get_update_info(self, url):
        import urllib.request, urllib.error, urllib.parse
        with urllib.request.urlopen(url) as f:
            txt = f.read()
            txt = txt.decode('utf-8')
            last_update, down_url = txt.split()[0:2]
            return last_update, down_url

    def _check_update(self, last_update, down_url):
        notify = _is_version_newer(last_update, meta.VERSION)
        check_time = datetime.today().strftime(_DATE_FMT)
        if notify:
            log.debug(f'Update available: {last_update}')
            self._notify_update(down_url, check_time, last_update)
        else:
            log.debug(f'No update available ({last_update})')
            self._no_update(check_time)
            
    def _notify_update(self, down_url, check_time, last_update):
        def fn():
            Publisher.sendMessage('program.update_available', down_url=down_url, check_time=check_time, version=last_update)
        wx.CallAfter(fn)
        
    #Notify application of no update. Used to set application settings in the main thread.
    def _no_update(self, check_time):
        def fn():
            Publisher.sendMessage('program.no_update_available', check_time=check_time)
        wx.CallAfter(fn)
