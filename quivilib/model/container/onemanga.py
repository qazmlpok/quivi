from __future__ import with_statement, absolute_import

from quivilib.model.container.base import BaseContainer
from quivilib.thirdparty.path import path as Path

from wx.lib.pubsub import pub as Publisher
from quivilib.thirdparty.onemanga_reader import OMReader
import cStringIO
import urllib2


class OMContainer(BaseContainer):
    
    def __init__(self, sort_order, show_hidden):
        class Dummy(object): pass
        Publisher.sendMessage('request.temp_path', Dummy)
        self.reader = OMReader(Dummy.temp_dir)
        self.path = ''
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)
                
    def _list_paths(self):
        paths = []
        for series in self.reader.series:
            path = Path(series.name + '/')
            last_modified = None
            paths.append((path, last_modified, series))
        return paths[1:]
            
    @property
    def name(self):
        return 'One Manga'
       
    def open_parent(self):
        return self

    def open_container(self, item_index):
        series = self.items[item_index].data
        return OMSeriesContainer(self.sort_order, series, self.show_hidden)
    
    def can_delete(self):
        return False
    
    @property
    def universal_path(self):
        return Path('onemanga:')
    
    @property
    def virtual_files(self):
        return True
    
class OMSeriesContainer(BaseContainer):
    
    def __init__(self, sort_order, series, show_hidden):
        self.series = series
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
        parent = OMContainer(self.sort_order, self.show_hidden)
        parent.selected_item = self.name
        return parent

    def open_container(self, item_index):
        if item_index == 0:
            return self.open_parent()
        episode = self.items[item_index].data
        return OMEpisodeContainer(self.sort_order, episode, self.series, self.show_hidden)
  
    def can_delete(self):
        return False
      
    @property
    def universal_path(self):
        return Path('onemanga:') / self.name
    
    @property
    def virtual_files(self):
        return True
    
class OMEpisodeContainer(BaseContainer):
    
    def __init__(self, sort_order, episode, series, show_hidden):
        self.series = series
        self.episode = episode
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
        parent = OMSeriesContainer(self.sort_order, self.series, self.show_hidden)
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
        return Path('onemanga:') / self.series.name / self.name
    
    @property
    def virtual_files(self):
        return True
