import sys, os
import io
import zipfile
from pathlib import Path
from zipfile import ZipFile as PyZipFile, ZipInfo
from datetime import datetime

from pubsub import pub as Publisher
from quivilib.model.container import Item, ItemType, SortOrder
from quivilib.model.container.base import BaseContainer
from quivilib.model.container.directory import DirectoryContainer
from quivilib.meta import PATH_SEP
from quivilib import tempdir

from typing import Any, Protocol, IO

class CompressedFileFormat(Protocol):
    def __init__(self, container, path: Path) -> None:
        pass
    @staticmethod
    def is_valid_extension(ext) -> bool:
        pass
    def list_files(self) -> list[tuple[Path, datetime]]:
        pass
    def open_file(self, path) -> IO[bytes]:
        pass
    def close(self) -> None:
        pass

def _copy_files(f_read, f_write):
    f_write.write(f_read.read())

def _is_hidden(path) -> bool:
    if sys.platform != 'win32' and path.name.startswith('.'):
        return True
    return False


class ZipFile(CompressedFileFormat):
    #TODO: (3,4) Improve: how to deal with password protected files?
    
    def __init__(self, container, path: Path) -> None:
        self.path = path
        self.file = PyZipFile(path, 'r')
        self.mapping = {}
        for f in self.file.infolist():
            self.mapping[Path(f.filename)] = f
        
    @staticmethod
    def is_valid_extension(ext):
        return ext.lower() in ['.zip', '.cbz']
    
    def list_files(self) -> list[tuple[Path, datetime]]:
        return [(path, datetime(*info.date_time))
                for path,info in self.mapping.items()
                if not info.is_dir()]
        
    def open_file(self, path) -> IO[bytes]:
        encpath: str|ZipInfo
        if path in self.mapping:
            encpath = self.mapping[path]
        else:
            encpath = str(path)
        return io.BytesIO(self.file.read(encpath))

    def close(self) -> None:
        self.file.close()
        self.file = None    # type: ignore[assignment]

class RarFileExternal(CompressedFileFormat):
    @staticmethod
    def is_valid_extension(ext):
        return ext.lower() in ['.rar', '.cbr']

    def __init__(self, container, path: Path) -> None:
        #Import here to delay creation of the temp dir until it's needed.
        import rarfile
        rarfile.HACK_TMP_DIR = tempdir.get_temp_dir()
        from rarfile import RarFile as PyRarFile
        self.path = path
        self.file = PyRarFile(path, 'r')
        #Force an exception if the file is invalid
        self.list_files()
    
    def list_files(self):
        return [(Path(f.filename), datetime(*f.date_time))
                for f in self.file.infolist() 
                if f.filename[-1] not in '\\/']
        
    def open_file(self, path) -> IO[bytes]:
        return io.BytesIO(self.file.read(self.conv_path(path)))

    def close(self) -> None:
        self.file.close()
        self.file = None    # type: ignore[assignment]

    def conv_path(self, path):
        npath = str(path)
        #rarfile doesn't like Windows backslashes
        #Anything else? There's a " 0" file, for example. Might be ".."
        return npath.replace(os.sep, '/')


class CompressedContainer(BaseContainer):
    def __init__(self, path: Path, sort_order: SortOrder, show_hidden: bool) -> None:
        self._path = path.resolve()
        classes: list[type[CompressedFileFormat]] = []
        if ZipFile.is_valid_extension(self._path.suffix):
            classes = [ZipFile, RarFileExternal]
        elif RarFileExternal.is_valid_extension(self._path.suffix):
            classes = [RarFileExternal, ZipFile]
        else:
            assert False, 'Invalid compressed file extension'
        firstExcep: Exception|None = None
        for zipclass in classes:
            try:
                zipfile = zipclass(self, self._path)
                #this will force an exception if it's not the right type of file
                zipfile.list_files()
                break
            except Exception as e:
                if firstExcep is None:
                    firstExcep = e
        if zipfile is None:
            #Report the first error raised (e.g. "Not a zip file"), not the last.
            raise firstExcep
        self.file: CompressedFileFormat = zipfile
            
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', container=self)

    def _list_paths(self) -> list[tuple[Path, datetime|None]]:
        paths: list[tuple[Path, datetime|None]] = []
        for path, last_modified in self.file.list_files():
            if not self.show_hidden and _is_hidden(path):
                continue
            paths.append((path, last_modified))
        paths.insert(0, (Path('..'), None))
        return paths
        
    def close_container(self) -> None:
        if self.file is not None:
            self.file.close()
    
    @property
    def name(self):
        return self._path.name

    def open_parent(self) -> BaseContainer:
        parent = DirectoryContainer(self._path.parent, self._sort_order, self.show_hidden)
        parent.selected_item = self._path
        return parent
    
    def open_container(self, item_index: int) -> BaseContainer:
        item = self.items[item_index]
        if item.typ == ItemType.COMPRESSED:
            temp_file = self._save_container(item)
            return VirtualCompressedContainer(temp_file, item.name, [], [], self._path, self._sort_order, self.show_hidden)
        else:
            return BaseContainer.open_container(self, item_index)
    
    def open_image(self, item_index: int) -> IO[bytes]:
        path = self.items[item_index].path
        img = self.file.open_file(path)
        return img 
    
    @property
    def virtual_files(self):
        return True
    
    @staticmethod
    def is_valid_extension(ext):
        return ZipFile.is_valid_extension(ext) or RarFileExternal.is_valid_extension(ext)
    
    @property
    def path(self) -> Path:
        return self._path
    
    @property
    def universal_path(self) -> Path|None:
        return self.path
    
    def can_delete(self) -> bool:
        return False
    
    def get_item_path(self, item_index: int) -> Path:
        if item_index == 0:
            return BaseContainer.get_item_path(self, item_index)
        return self.path / self.items[item_index].path
    
    def get_item_name(self, item_index):
        return str(self.items[item_index].path)
        
    def _save_container(self, item):
        """Save a container inside this container as a temp file.
        
        @param item: item of the container
        @type item: Item
        @return: temp file path
        @rtype: Path
        """
        ext = item.suffix
        in_file = self.file.open_file(item.path)
        #Must change whenever passwords are supported
        with tempdir.get_temp_file(ext=ext) as out_file:
            _copy_files(in_file, out_file)
            temp_file = out_file.name
        return Path(temp_file)


class VirtualCompressedContainer(CompressedContainer):
    def __init__(self, path: Path, name, parent_names, parent_paths, original_container_path, sort_order: SortOrder, show_hidden: bool):
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
        self._universal_path = Path(PATH_SEP.join([str(self.original_container_path)] +
                                       self.parent_names + [self._name]))
        CompressedContainer.__init__(self, path, sort_order, show_hidden)
        
    def open_container(self, item_index: int) -> BaseContainer:
        item = self.items[item_index]
        if item.typ == ItemType.COMPRESSED:
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
        
    def open_parent(self) -> BaseContainer:
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
        #Works on single-level archives, at least.
        parent.selected_item = self.path
        return parent
        
    @property
    def path(self) -> Path:
        return self.container_path
    
    @property
    def name(self):
        return self._name
    
    def can_delete(self) -> bool:
        return False
    
    @property
    def universal_path(self) -> Path|None:
        return self._universal_path
    
    def get_item_path(self, item_index: int) -> Path:
        if item_index == 0:
            return CompressedContainer.get_item_path(self, item_index)
        return self.container_path / self.items[item_index].path
