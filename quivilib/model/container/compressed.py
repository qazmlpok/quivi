

from quivilib.model.container import Item
from quivilib.model.container.base import BaseContainer
from quivilib.model.container.directory import DirectoryContainer
from pathlib import Path

from wx.lib.pubsub import pub as Publisher
from quivilib.meta import PATH_SEP

import sys
import zipfile
from zipfile import ZipFile as PyZipFile
import io
from datetime import datetime

if sys.platform == 'win32':
    from quivilib.thirdparty.UnRAR import Archive
else:
    from quivilib.thirdparty.rarfile import RarFile as PyRarFile



def _copy_files(f_read, f_write):
    f_write.write(f_read.read())

def _is_hidden(path):
    if sys.platform != 'win32' and path.startswith('.'):
        return True
    return False


class ZipFile(object):
    #TODO: (3,4) Improve: how to deal with password protected files?
    
    def __init__(self, container, path):
        self.path = path
        self.file = PyZipFile(path, 'r')
        #Note - mapping is no longer used atm, due to _convert_filename being dummied out.
        self.mapping = {}
        
    @staticmethod
    def is_valid_extension(ext):
        return ext.lower() in ['.zip', '.cbz']
    
    def list_files(self):
        return [(Path(self._convert_filename(f.filename)),
                 datetime(*f.date_time))
                for f in self.file.infolist()
                if f.filename[-1] not in '\\/']
        
    def open_file(self, path):
        if path in self.mapping:
            encpath = self.mapping[path]
        else:
            encpath = str(path)
        return io.BytesIO(self.file.read(encpath))
    
    def _convert_filename(self, path):
        #zipfile decodes utf-8, but not cp437
        #try:
        #    decpath = path.decode('cp437')
        #    self.mapping[decpath] = path
        #    return decpath
        #except UnicodeDecodeError:
        #    decpath = path.decode('ascii', 'ignore')
        #    self.mapping[decpath] = path
        #    return decpath
        #TODO: Determine if anything still needs to be done here; python3 is a lot better with Unicode.
        return path



class RarFile(object):
    def __init__(self, container, path):
        self.path = path
    
    @staticmethod
    def is_valid_extension(ext):
        return ext.lower() in ['.rar', '.cbr']
    
    def list_files(self):
        archive = Archive(str(self.path))
        try:
            return [(Path(f.filename), datetime(*f.datetime[0:6]))
                 for f in archive.iterfiles()]
        finally:
            archive.close()
    
    def open_file(self, path):
        archive = Archive(str(self.path))
        try:
            for f in archive.iterfiles():
                if f.filename == path:
                    stream = f.open('rb')
                    try:
                        string = stream.read()
                        fstr = io.BytesIO(string)
                    finally:
                        stream.close()
                    return fstr
        finally:
            archive.close()



class RarFileExternal(RarFile):
        
    def __init__(self, container, path):
        self.path = path
        self.file = PyRarFile(path, 'r')
    
    def list_files(self):
        return [(Path(f.filename), datetime(*f.date_time))
                for f in self.file.infolist() 
                if f.filename[-1] not in '\\/']
        
    def open_file(self, path):
        return io.BytesIO(self.file.read(path))




class CompressedContainer(BaseContainer):
    def __init__(self, path, sort_order, show_hidden):
        self._path = path.resolve()
        RarCls = RarFile if sys.platform == 'win32' else RarFileExternal
        classes = []
        if ZipFile.is_valid_extension(self._path.suffix):
            classes = [ZipFile, RarCls]
        elif RarFile.is_valid_extension(self._path.suffix):
            classes = [RarCls, ZipFile]
        else:
            assert False, 'Invalid  compressed file extension'
        try:
            self.file = classes[0](self, self._path)
            #this will force an exception if it's not the right type of file
            self.file.list_files()
        except:
            self.file = classes[1](self, self._path)
            #this will force an exception if it's not the right type of file
            self.file.list_files()
            
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', self)

    def _list_paths(self):
        paths = []
        for path, last_modified in self.file.list_files():
            data = None
            if not self.show_hidden and _is_hidden(path):
                continue
            paths.append((path, last_modified, data))
        paths.insert(0, (Path('..'), None, None))
        return paths
    
    @property
    def name(self):
        return self._path.name

    def open_parent(self):
        parent = DirectoryContainer(self._path.parent, self._sort_order, self.show_hidden)
        parent.selected_item = self._path
        return parent
    
    def open_container(self, item_index):
        item = self.items[item_index]
        if item.typ == Item.COMPRESSED:
            temp_file = self._save_container(item)
            return VirtualCompressedContainer(temp_file, item.name, [], [], self._path, self._sort_order, self.show_hidden)
        else:
            return BaseContainer.open_container(self, item_index)
    
    def open_image(self, item_index):
        path = self.items[item_index].path
        img = self.file.open_file(path)
        return img 
    
    @property
    def virtual_files(self):
        return True
    
    @staticmethod
    def is_valid_extension(ext):
        return ZipFile.is_valid_extension(ext) or RarFile.is_valid_extension(ext)
    
    @property
    def path(self):
        return self._path
    
    @property
    def universal_path(self):
        return self.path
    
    def can_delete(self):
        return False
    
    def get_item_path(self, item_index):
        if item_index == 0:
            return BaseContainer.get_item_path(self, item_index)
        return self.path / self.items[item_index].path
    
    def get_item_name(self, item_index):
        return self.items[item_index].path.name
        
    def _save_container(self, item):
        """Save a container inside this container as a temp file.
        
        @param item: item of the container
        @type item: Item
        @return: temp file path
        @rtype: Path
        """
        ext = item.suffix
        class Dummy(object): pass
        o = Dummy()
        o.temp_path = None
        Publisher.sendMessage('request.temp_path', o)
        temp_file = o.temp_path + ext
        in_file = self.file.open_file(item.path)
        #Must change whenever passwords are supported
        with temp_file.open('wb') as out_file:
            _copy_files(in_file, out_file)
        return temp_file
    
    

class VirtualCompressedContainer(CompressedContainer):
    def __init__(self, path, name, parent_names, parent_paths, original_container_path, sort_order, show_hidden):
        """Create a VirtualCompressedContainer (a compressed file inside another
        compressed file).
        
        @param path: physical path of the file (will be a in a temp dir with a random name)
        @type path: Path
        @param name: file name of the container (as originally inside the parent)
        @type name: unicode
        @param parent_names: names of parent containers
        @type parent_names: list(unicode)
        @param parent_paths: physical paths of parent containers
        @type parent_paths: list(Path)
        @param original_container_path: path of the first 'real' ancestor of the container
            (the first which is not in a temp dir)
        @type original_container_path: Path
        """
        self._name = name
        self.parent_names = parent_names
        self.parent_paths = parent_paths
        self.original_container_path = original_container_path
        self.parent_path = self.original_container_path
        for parent_name in self.parent_names:
            self.parent_path /= parent_name
        #: container_path contains the 'virtual' path of the container
        #: (e.g. C:/foo.zip/bar.rar/foobar.zip)
        self.container_path = self.parent_path / self._name
        self._universal_path = Path(PATH_SEP.join([self.original_container_path] +
                                       self.parent_names + [self._name]))
        CompressedContainer.__init__(self, path, sort_order, show_hidden)
        
    def open_container(self, item_index):
        item = self.items[item_index]
        if item.typ == Item.COMPRESSED:
            temp_file = self._save_container(item)
            parent_names = self.parent_names[:]
            parent_names.append(self.name)
            parent_paths = self.parent_paths[:]
            parent_paths.append(self._path)
            return VirtualCompressedContainer(temp_file, item.name, parent_names,
                                              parent_paths, self.original_container_path,
                                              self._sort_order, self.show_hidden)
        else:
            return BaseContainer.open_container(self, item_index)
        
    def open_parent(self):
        parent = None
        if len(self.parent_names) == 0:
            parent = CompressedContainer(self.original_container_path, self.sort_order, self.show_hidden)
        else:
            parent_names = self.parent_names[:]
            parent_name = parent_names.pop()
            parent_paths = self.parent_paths[:]
            parent_path = parent_paths.pop()
            parent = VirtualCompressedContainer(parent_path, parent_name, parent_names,
                                                parent_paths, self.original_container_path,
                                                self._sort_order, self.show_hidden)
        #TODO: (2,2) Test: test if this works
        parent.selected_item = self.path
        return parent
        
    @property
    def path(self):
        return self.container_path
    
    @property
    def name(self):
        return self._name
    
    def can_delete(self):
        return False
    
    @property
    def universal_path(self):
        return self._universal_path
    
    def get_item_path(self, item_index):
        if item_index == 0:
            return CompressedContainer.get_item_path(self, item_index)
        return self.container_path / self.items[item_index].path
