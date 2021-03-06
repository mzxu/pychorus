'''
Created on Feb 23, 2014

@author: Anduril
@target: to give a better shell of unittest in order to provide pretty HTML report
'''
import unittest,time
import Utils
import ChorusGlobals
from ChorusConstants import LEVELS, LOGIC, IMAGELOGIC, TYPES, ResultStatus, AssertionResult

class MyTestCase(unittest.TestCase):
    '''
    Inherit from python's unittest.TestCase
    override the setUp, setUpClass, tearDown, tearDownClass methold    
    '''
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)     
        if hasattr(getattr(self, methodName), '_scopes'):          
            self.scopes = getattr(self, methodName)._scopes
        else:
            self.scopes = ["all"]
        self.executed_cases = []
    
    def init_assertions(self, name):
        assertions = self.result.cases[self._testMethodName].assertions
        if not assertions.has_key(name):
            assertions[name] = AssertionResult(name)
        return assertions[name]
    
    def assertBool(self, name, content, levels = LEVELS.Normal):
        if content is True:
            content = 'True'
        elif content is False:
            content = 'False'
        elif content != 'True' and content != 'False':
            content = 'False'
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Bool, logic = LOGIC.Equal)
    
    def assertData(self, name, content, levels = LEVELS.Normal):
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Data, logic = LOGIC.Equal)
    
    def assertDataOnFly(self, name, data1, data2, levels = LEVELS.Normal):
        assertion_result = self.init_assertions(name)
        assertion_result.onfly_flag = True
        assertion_result.baseline = data1
        assertion_result.baseline_status = True
        self.vm.checkpoint(self, name, data2, level = levels, cptype = TYPES.Data, logic = LOGIC.Equal)
    
    def assertHTTPResponse(self, name, response, levels = LEVELS.Normal, logic = LOGIC.Equal):
        assertion_result = self.init_assertions(name)
        assertion_result.detail["api"] = response
        self.vm.checkpoint(self, name, response.result, level = levels, cptype = TYPES.Data, logic = logic)
    
    def assertImageData(self, name, imagedata, levels = LEVELS.Normal, image_logic = IMAGELOGIC.Full, imagetype = "jpg"):
        self.vm.save_image(self, name, imagedata, imagetype)
        content = {
                    "image_name":self._testMethodName+"_"+name,
                    "image_type":imagetype
                   }
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Image, logic = image_logic)
    
    def assertScreenShot(self, name, driver, levels = LEVELS.Normal, image_logic = IMAGELOGIC.Full, imagetype = "png", elements = None, coordinates = None):
        self.vm.save_screenshot(self, name, driver, elements, coordinates, imagetype)
        content = {
                    "image_name":self._testMethodName+"_"+name,
                    "image_type":imagetype
                   }
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Image, logic = image_logic)
    
    def assertText(self, name, content, levels = LEVELS.Normal, logic = LOGIC.Equal):
        self.vm.checkpoint(self, name, str(content), level = levels, cptype = TYPES.Text, logic = logic)
    
    def setUp(self):
        '''
        setUp is executed every time before run a test case
        you can do some initial work here
        '''
        self.startTime = time.time()
        unittest.TestCase.setUp(self)
        
    @classmethod
    def setUpClass(cls):        
        '''
        setUpClass is executed every time before run a test suite
        '''
        cls.suite_starttime = time.time()
        cls.logserver = ChorusGlobals.get_logserver()
        cls.logserver.flush_console()
        super(MyTestCase,cls).setUpClass()
        cls.logger = ChorusGlobals.get_logger()
        cls.suite_name = Utils.get_current_classname(cls)
        from VerificationManagement import VerificationManagement
        cls.vm = VerificationManagement()
        cls.result = cls.vm.check_suitebaseline(cls.suite_name)
        cls.timestamp = Utils.get_timestamp()
        cls.config = ChorusGlobals.get_configinfo()
        cls.parameters = ChorusGlobals.get_parameters()

    def tearDown(self):
        '''
        tear down is executed after each case has finished, 
        you can do some clean work here, including
        1.check if crash happens, 
        2.analyze failed/passed actions, 
        3.store the case level test result 
        '''
        self.logserver.flush_console()
        if self._resultForDoCleanups.failures:
            self.parse_unittest_assertionerror()
        if self._resultForDoCleanups.errors:
            self.parse_crasherror()
        self.endTime = time.time()
        if self.result.cases.has_key(self._testMethodName):
            self.result.cases[self._testMethodName].time_taken = self.endTime-self.startTime
            if self.result.cases[self._testMethodName].status == ResultStatus.FAILED:
                self.result.failed_cases += 1
            elif self.result.cases[self._testMethodName].status in [ResultStatus.PASSED, ResultStatus.KNOWN_ISSUES]:
                self.result.passed_cases += 1
        unittest.TestCase.tearDown(self)
        
    @classmethod
    def tearDownClass(cls): 
        '''
        tearDownClass is executed after each suite has finished, 
        you can do some clean work here, including
        1.generate baseline, 
        '''
        super(MyTestCase,cls).tearDownClass()
        cls.vm.generate_baseline(cls.result)
        cls.logserver.flush_console()
        cls.suite_endtime = time.time()
        cls.result.time_taken = cls.suite_endtime - cls.suite_starttime
        
    def parse_unittest_assertionerror(self):
        try:
            error_message = self._resultForDoCleanups.failures[0][1]
            error_type, error_content, error_line_info = self.parse_error(error_message)
            self.result.cases[self._testMethodName].status = ResultStatus.FAILED
            self.result.cases[self._testMethodName].statusflag = False
            self.result.statusflag = False
            self.result.unknownflag = True
            if self.result.status != ResultStatus.CRASHED:
                self.result.status = ResultStatus.FAILED
            self.result.cases[self._testMethodName].fail_message={"type":error_type,
                                                                  "content":error_content,
                                                                  "line_info":error_line_info}
            self.result.cases[self._testMethodName].failed_assertions += 1
            self.logger.error("AssertionError: "+" - ".join([error_type, error_content, error_line_info]))
            self._resultForDoCleanups.failures = []
        except Exception, e:
            self.logger.critical("parsing assertion error failed by errors '%s'" % e)
            
    def parse_crasherror(self):
        try:
            error_message = self._resultForDoCleanups.errors[0][1]
            error_type, error_content, error_line_info = self.parse_error(error_message)
            self.result.cases[self._testMethodName].status = ResultStatus.CRASHED
            self.result.cases[self._testMethodName].statusflag = False
            self.result.status = ResultStatus.CRASHED
            self.result.statusflag = False
            self.result.unknownflag = True
            self.result.cases[self._testMethodName].fail_message={"type":error_type,
                                                                  "content":error_content,
                                                                  "line_info":error_line_info}
            self.result.crash_cases += 1
            self.logger.critical("CrashError: "+" - ".join([error_type, error_content, error_line_info]))
            self._resultForDoCleanups.errors = []
        except Exception, e:
            self.logger.critical("parsing crash error failed by errors '%s'" % e)
    
    def parse_error(self, msg):
        temp_msgs = msg.strip().split("\n")
        temp_msgs2 = temp_msgs[-1].split(":")
        error_type = temp_msgs2[0].strip()
        error_content = temp_msgs2[1].strip()
        error_line_info = "\n"+"\n".join(temp_msgs[1:-1]).strip()
        return error_type, error_content, error_line_info