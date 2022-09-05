

import unittest

from quivilib import meta
from quivilib.control.check_update import UpdateChecker, _DATE_FMT
from quivilib.model.settings import Settings
from quivilib.util import monkeypatch_method

from datetime import datetime, timedelta

from pubsub import pub as Publisher

import logging
logging.basicConfig(encoding='utf8')
logging.getLogger().setLevel(logging.ERROR)

DOWN_URL = 'http://example.com/down'



def listen(topic):
    lst = []
    
    def fn(**kwargs):
        lst.append(**kwargs)
    Publisher.subscribe(fn, topic)
    return lst
        
def now():
    d = datetime.today()
    d = d.replace(second = 0, microsecond=0)
    return d

class Test(unittest.TestCase):
    def setUp(self):
        self.UpdateAvailable = []
        self.NoUpdate = []
        outer = self
        
        @monkeypatch_method(UpdateChecker)
        def _notify_update(self, url, check_time, last_update):
            outer.UpdateAvailable.append((url, check_time, last_update))
        @monkeypatch_method(UpdateChecker)
        def _no_update(self, check_time):
            outer.NoUpdate.append(check_time)

    def test_first_run_older(self):
        s = Settings('nonexistantfile')
        
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            return '0.0', DOWN_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 0)
        self.assertEqual(len(self.NoUpdate), 1)
        #self.assertEqual(s.get('Update', 'Available'), '0')
        timeb = datetime.strptime(self.NoUpdate[0], _DATE_FMT)
        self.assertTrue(timea <= timeb <= timec)
        
    def test_first_run_newer(self):
        s = Settings('nonexistantfile')
        
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            return '99.9.0', DOWN_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 1)
        self.assertEqual(len(self.NoUpdate), 0)
        (url, check_time, last_update) = self.UpdateAvailable[0]
        self.assertEqual(url, DOWN_URL)
        #self.assertEqual(s.get('Update', 'Available'), '1')
        timeb = datetime.strptime(check_time, _DATE_FMT)
        self.assertEqual(url, DOWN_URL)
        self.assertEqual(last_update, '99.9.0')
        self.assertTrue(timea <= timeb <= timec)
        
    def test_second_run_older_recent(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '0')
        d = now()
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        
        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return '0.0', DOWN_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 0)
        self.assertEqual(len(self.NoUpdate), 1)
        self.assertEqual(len(called), 0)
        #self.assertEqual(s.get('Update', 'Available'), '0')
        #timeb = datetime.strptime(self.NoUpdate[0], _DATE_FMT)
        #self.assertTrue(timea <= timeb <= timec)
        
    def test_second_run_older_not_recent(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '0')
        d = now()
        d -= timedelta(days=2)
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        
        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return '0.0', DOWN_URL

        timea = now()
        upd = listen("program.update_available")
        noupd = listen("program.no_update_available")
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 0)
        self.assertEqual(len(self.NoUpdate), 1)
        self.assertEqual(len(called), 1)
        timeb = datetime.strptime(self.NoUpdate[0], _DATE_FMT)
        self.assertTrue(timea <= timeb <= timec)
        
    def test_second_run_newer_not_recent(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '0')
        d = now()
        d -= timedelta(days=2)
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        
        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return '99.0', DOWN_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 1)
        self.assertEqual(len(self.NoUpdate), 0)
        (url, check_time, last_update) = self.UpdateAvailable[0]
        self.assertEqual(url, DOWN_URL)
        self.assertEqual(len(called), 1)
        #self.assertEqual(s.get('Update', 'Available'), '1')
        #self.assertEqual(s.get('Update', 'URL'), DOWN_URL)
        self.assertEqual(last_update, '99.0')
        timeb = datetime.strptime(check_time, _DATE_FMT)
        self.assertTrue(timea <= timeb <= timec)
    
    def test_available_not_recent(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '1')
        d = now()
        d -= timedelta(days=2)
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        s.set('Update', 'URL', DOWN_URL)
        
        NEW_URL = DOWN_URL + 'newer'
        
        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return '99.0', NEW_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 1)
        self.assertEqual(len(self.NoUpdate), 0)
        (url, check_time, last_update) = self.UpdateAvailable[0]
        self.assertEqual(url, NEW_URL)
        self.assertEqual(len(called), 1)
        #self.assertEqual(s.get('Update', 'Available'), '1')
        #self.assertEqual(s.get('Update', 'URL'), DOWN_URL)
        self.assertEqual(last_update, '99.0')
        timeb = datetime.strptime(check_time, _DATE_FMT)
        self.assertTrue(timea <= timeb <= timec)
    
    def test_available_recent(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '1')
        d = now()
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        s.set('Update', 'URL', DOWN_URL)
        s.set('Update', 'Version', '99.0')
        
        NEW_URL = DOWN_URL + 'newer'
        
        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return '99.0', NEW_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 1)
        self.assertEqual(len(self.NoUpdate), 0)
        self.assertEqual(self.UpdateAvailable[0][0], DOWN_URL)
        self.assertEqual(len(called), 0)
        #self.assertEqual(s.get('Update', 'Available'), '1')
        #self.assertEqual(s.get('Update', 'URL'), DOWN_URL)
        #self.assertEqual(s.get('Update', 'Version'), '99.0')
        #timeb = datetime.strptime(s.get('Update', 'LastCheck'), _DATE_FMT)
        #self.assertTrue(timea <= timeb <= timec)
        
    def test_just_updated(self):
        s = Settings('nonexistantfile')
        s.set('Update', 'Available', '1')
        d = now()
        s.set('Update', 'LastCheck', d.strftime(_DATE_FMT))
        s.set('Update', 'URL', DOWN_URL)

        called = []
        @monkeypatch_method(UpdateChecker)
        def _get_update_info(self, url):
            called.append(1)
            return meta.VERSION, DOWN_URL

        timea = now()
        u = UpdateChecker(s)
        u.thread.join()
        timec = now()
        
        self.assertEqual(len(self.UpdateAvailable), 0)
        self.assertEqual(len(self.NoUpdate), 1)
        self.assertEqual(len(called), 0)
