'''
Created on Dec 28, 2013

@author: Anduril
'''
import sys,os
import optparse
from ChorusCore.ProjectConfiguration import ProjectConfiguration
from ChorusCore.ProjectExecution import RunTest
from ChorusCore.LogServer import Level
class MyProject(ProjectConfiguration):
    '''default initialization, can be reloaded'''
#     def __init__(self,options):
#         ProjectConfiguration.__init__(self, options)
    
    def __init__(self,options):
        self.options=options
        self.set_output_folder()
        self.set_configfile()
        self.set_logserver(level=Level.debug, colorconsole = False)
        self.logserver.add_filehandler(level=Level.error,
                                       filepath=self.outputdir,filename="error.log")
        self.logserver.add_filehandler(level=Level.info,
                                       filepath=self.outputdir,filename="info.log")
        
    def start_test(self): 
        RunTest()
        
#     def close_test(self):
#         self.close_logserver()
                
# class MyTest(RunTest):
#     '''default initialization, can be reloaded'''
# #     def __init__(self):
# #         RunTest.__init__(self)
#     
#     def __init__(self):
#         self.InitRunName()
#         self.InitTestSuite()
#         self.InitBaselines()
#         self.result=self.RunSuites()
# #         self.RunCrashSuites()
#         self.GenerateReport()
#         self.CheckFailures()

if __name__ == '__main__':
    current_dir_abs = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.dirname(current_dir_abs)
    chorus_dir = current_dir_abs+"/ChorusCore"
    sys.path.append(current_dir_abs)
    sys.path.append(chorus_dir)
    sys.path.append(parent_dir)
       
    parser = optparse.OptionParser()
    parser.add_option("-c","--config",dest="configfile",
                      help="config file name, e.g: test.cfg")
    parser.add_option("-p","--path",dest="configpath",
                      default="",
                      help="config file path, default: Config/, e.g. test")
    parser.add_option("-o","--output",dest="outputpath",
                      default="",
                      help="output file path, default: Output/, e.g: Output")
    options, args = parser.parse_args()
    
    if not options.configfile:
        sys.exit("No config file specified! Aborted.")
    
    init=MyProject(options)
    init.start_test()
#     init.close_test()
    
    

