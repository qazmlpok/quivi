from __future__ import with_statement, absolute_import

from quivilib.model.container.base import BaseContainer
from quivilib.thirdparty.path import path as Path

from wx.lib.pubsub import pub as Publisher
import cStringIO
import urllib2
import string
from quivilib.control.mangafox_reader import MFReader


class MFContainer(BaseContainer):
    
    def __init__(self, sort_order, show_hidden):
        class Dummy(object): pass
        Publisher.sendMessage('request.temp_path', Dummy)
        self.reader = MFReader(Dummy.temp_dir)
        self.path = ''
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)
                
    def _list_paths(self):
        paths = []
        for letter in self.reader.letters:
            path = Path(letter.name + '/')
            last_modified = None
            paths.append((path, last_modified, letter))
        return paths
            
    @property
    def name(self):
        return 'Manga Fox'
       
    def open_parent(self):
        return self

    def open_container(self, item_index):
        letter = self.items[item_index].data
        return MFLetterContainer(self.sort_order, letter, self.show_hidden)
    
    def can_delete(self):
        return False
    
    @property
    def universal_path(self):
        return Path('mangafox:')
    
    @property
    def virtual_files(self):
        return True
    
class MFLetterContainer(BaseContainer):
    
    def __init__(self, sort_order, letter, show_hidden):
        self.letter = letter
        self.path = ''
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)
                
    def _list_paths(self):
        paths = []
        for serie in self.letter.series:
            path = Path(serie.name + '/')
            paths.append((path, None, serie))
        paths.insert(0, (Path(u'..'), None, None))
        return paths
            
    @property
    def name(self):
        return self.letter.name
       
    def open_parent(self):
        parent = MFContainer(self.sort_order, self.show_hidden)
        parent.selected_item = self.name
        return parent

    def open_container(self, item_index):
        if item_index == 0:
            return self.open_parent()
        serie = self.items[item_index].data
        return MFSeriesContainer(self.sort_order, serie, self.letter, self.show_hidden)
  
    def can_delete(self):
        return False
      
    @property
    def universal_path(self):
        return Path('mangafox:') / self.name
    
    @property
    def virtual_files(self):
        return True
    
class MFSeriesContainer(BaseContainer):
    
    def __init__(self, sort_order, series, letter, show_hidden):
        self.series = series
        self.letter = letter
        self.path = ''
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)
                
    def _list_paths(self):
        paths = []
        for episode in self.series.episodes:
            path = Path(episode.name + '/')
            paths.append((path, None, episode))
        paths.insert(0, (Path(u'..'), None, None))
        return paths
            
    @property
    def name(self):
        return self.series.name
       
    def open_parent(self):
        parent = MFLetterContainer(self.sort_order, self.letter, self.show_hidden)
        parent.selected_item = self.name
        return parent

    def open_container(self, item_index):
        if item_index == 0:
            return self.open_parent()
        episode = self.items[item_index].data
        return MFEpisodeContainer(self.sort_order, episode, self.series, self.letter, self.show_hidden)
  
    def can_delete(self):
        return False
      
    @property
    def universal_path(self):
        return Path('mangafox:') / self.letter.name / self.name
    
    @property
    def virtual_files(self):
        return True
    
class MFEpisodeContainer(BaseContainer):
    
    def __init__(self, sort_order, episode, series, letter, show_hidden):
        self.series = series
        self.episode = episode
        self.letter = letter
        self.path = ''
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)
                
    def _list_paths(self):
        paths = []
        for page in self.episode.pages:
            #TODO: fix this hack, name needs extension
            path = Path(page.name + '.jpg')
            paths.append((path, None, page))
        paths.insert(0, (Path(u'..'), None, None))
        return paths
            
    @property
    def name(self):
        return self.episode.name
       
    def open_parent(self):
        parent = MFSeriesContainer(self.sort_order, self.series, self.letter, self.show_hidden)
        parent.selected_item = self.name
        return parent
    
    def open_image(self, item_index):
        page = self.items[item_index].data 
        url = page.url
        data = urllib2.urlopen(url).read()
        return cStringIO.StringIO(data)

    def can_delete(self):
        return False
    
    @property
    def universal_path(self):
        return Path('mangafox:') / self.letter.name / self.series.name / self.name
    
    @property
    def virtual_files(self):
        return True
