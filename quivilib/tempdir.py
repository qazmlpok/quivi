# -*- coding: utf-8 -*-

#Acts as a singleton to manage a single temp directory for the application
#Use get_temp_file to request a new temp file (via the tempfile module)
#Call delete_tempdir on program close.

from pathlib import Path

import tempfile
import sys

#Using singleton recipe from https://stackoverflow.com/a/35904211/2712047

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it 
this.tempdir = None

def get_temp_file(*, ext=None):
    """
    Return a temporary file, stored within the application tempdir.
    The tempdir is created if it doesn't already exist.
    """
    if this.tempdir is None:
        #Delay creation until the first file is requested. Cuts down on unnecessary temp dir creation.
        _create_tempdir()
    assert this.tempdir is not None
    return tempfile.NamedTemporaryFile(suffix=ext, dir=this.tempdir, delete=False)
    
def _create_tempdir():
    temp_dir = tempfile.mkdtemp(prefix='quivi_')
    this.tempdir = Path(temp_dir)

#TODO: This solves the message passing, but the deletion fails because the temp file is still
#in use on program close. This may be a legacy bug.
def delete_tempdir():
    if this.tempdir is not None:
        for filepath in this.tempdir.iterdir():
            try:
                #Assumption: nested directories will never be added to the temp folder
                filepath.unlink()
            except Exception as e:
                pass
        try:
            this.tempdir.rmdir()
        except Exception as e:
            pass
        
        this.tempdir = None
