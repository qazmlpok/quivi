

import sys, unittest, os, shutil

import wx
import logging
logging.getLogger().setLevel(logging.DEBUG)


class AllTests(unittest.TestSuite):
    def __init__(self):
        super(AllTests, self).__init__()
        self.createImages()
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
            
    def createImages(self):
        """ Makes a bunch of copies of python.png.
        Probably not the best approach but I'd still prefer this over putting that much junk into git.
        """
        src = os.path.join('tests', 'python.png')
        order = os.path.join('tests', 'Order')
        nested_1 = os.path.join('tests', 'Order_nested', 'c1')
        nested_2 = os.path.join('tests', 'Order_nested', 'c2')
        os.makedirs(order, exist_ok = True)
        os.makedirs(nested_1, exist_ok = True)
        os.makedirs(nested_2, exist_ok = True)
        
        order_files = ['1.png', '10.png', '10a.png', '11.png', '11a.png', '1a.png', '2.png', '2a.png', '8.png', '8a.png', '9.png', '9a.png', 'a10.png', 'a11.png', 'a9.png']
        c_files = ['1.png', '10.png', '11.png', '2.png', '8.png', '9.png',]
        for f in order_files:
            shutil.copyfile(src, os.path.join(order, f))
        for f in c_files:
            shutil.copyfile(src, os.path.join(nested_1, f))
            shutil.copyfile(src, os.path.join(nested_2, f))
        #This needs to be a zip.
        shutil.make_archive(os.path.join('tests', 'Order_nested'), 'zip', os.path.join('tests', 'Order_nested'))
    
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
