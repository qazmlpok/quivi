

import sys, unittest, os

import wx
import logging
logging.getLogger().setLevel(logging.DEBUG)


class AllTests(unittest.TestSuite):
    def __init__(self):
        super(AllTests, self).__init__()
        self.loadAllTests()

    def loadAllTests(self):
        for moduleName in self.iter_test_modules():
            # Importing the module is not strictly necessary because
            # loadTestsFromName will do that too as a side effect. But if the 
            # test module contains errors our import will raise an exception
            # while loadTestsFromName ignores exceptions when importing from 
            # modules.
            module = __import__(moduleName)
            self.addTests(unittest.defaultTestLoader.loadTestsFromName(moduleName))
    
    @staticmethod
    def filenameToModuleName(filename):
        #strip '.py'
        filename = filename[:-3]
        module = filename.replace(os.sep, '.')  
        return module
    
    @staticmethod
    def iter_test_modules():
        for root, dirs, files in os.walk('tests'):
            for f in files:
                path =  os.path.join(root, f)
                if f.endswith('.py') and not f.startswith('.') and not f.startswith('__'):
                    yield AllTests.filenameToModuleName(path)
       
    def runTests(self):
        unittest.TextTestRunner(verbosity=1).run(self)
    
if __name__ == '__main__':
    allTests = AllTests()
    allTests.runTests()
