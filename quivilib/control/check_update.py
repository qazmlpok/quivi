

from quivilib import meta

from pubsub import pub as Publisher
import wx

from threading import Thread
from datetime import datetime
import traceback
import logging
log = logging.getLogger('check_update')


_DATE_FMT = '%Y-%m-%d %H:%M'



def _is_version_newer(last, current):
    last = [int(n) for n in last.split('.')]
    current = [int(n) for n in current.split('.')]
    return last > current 


class UpdateChecker(object):
    
    def __init__(self, settings):
        self.settings = settings
        self.thread = Thread(target=self.run)
        self.thread.setDaemon(True)
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
                self._notify_update(url)
            else:
                self.settings.set('Update', 'Available', '0')
                
        except:
            log.error(traceback.format_exc())
            
    def _get_update_info(self, url):
        import urllib.request, urllib.error, urllib.parse
        f = urllib.request.urlopen(url)
        txt = f.read()
        txt = txt.decode('utf-8')
        last_update, down_url = txt.split()[0:2]
        return last_update, down_url
            
    def _check_update(self, last_update, down_url):
        notify = _is_version_newer(last_update, meta.VERSION)
        self.settings.set('Update', 'LastCheck', datetime.today().strftime(_DATE_FMT))
        if notify:
            self.settings.set('Update', 'Available', '1')
            self.settings.set('Update', 'URL', down_url)
            self.settings.set('Update', 'Version', last_update)
            self._notify_update(down_url)
        else:
            self.settings.set('Update', 'Available', '0')
            
    def _notify_update(self, down_url):
        def fn():
            Publisher.sendMessage('program.update_available', down_url=down_url)
        wx.CallAfter(fn)
