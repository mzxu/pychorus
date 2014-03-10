'''
Created on Jan 25, 2014

@author: Anduril, mxu
@target: read config file and generate related test suite pipeline, and let unittest run each of them
'''
import Utils
import unittest
import inspect
import ChorusGlobals
import os
import importlib
import time
from ChorusConstants import ResultStatus, CommonConstants

class TestSuiteManagement:
    '''
    Entry in charge of test suite management: get test suite, run test suite  
    '''
#     testsuites={}
    TESTSUITE_FOLDER = CommonConstants.TESTSUITE_FOLDER
    BASELINE_PATH = CommonConstants.BASELINE_PATH
    runner = []
    def __init__(self):
        
        self.logger = ChorusGlobals.get_logger()
        self.config = ChorusGlobals.get_configinfo()
        ChorusGlobals.init_testresult()
        self.result = ChorusGlobals.get_testresult()
        self.suite_dict = self.get_test_mapping()
        self.filter_test_mapping()
        self.set_scope()
        self.get_testsuites()
        self.set_baselinepath()
        self.get_knownissues()
        ChorusGlobals.set_suitedict(self.suite_dict)
    
    def get_knownissues(self):
        if os.environ.has_key(CommonConstants.KNOWN_ISSUE_KEY):
            known_issue_list = Utils.get_dict_from_json(os.environ[CommonConstants.KNOWN_ISSUE_KEY])
            ChorusGlobals.set_knownissuelist(known_issue_list)
            self.logger.info("Known issue list found in environment variables")
        else:
            ChorusGlobals.set_knownissuelist(None)
            self.logger.debug("No known issue list found in environment variables")
    
    def set_baselinepath(self):
        self.baselinepath = self.BASELINE_PATH
        if self.config.has_key("baseline"):
            paths = self.config["baseline"].split(".")
            for path in paths:
                self.baselinepath.append(path)
        ChorusGlobals.set_baselinepath(self.baselinepath)
    
    def execute_suites(self):
        start_time = time.time()
        for suite in self.suites_in_scope._tests:
            self.runner.append(unittest.TextTestRunner(verbosity=2).run(suite))
        end_time = time.time()
        self.result.time_taken = end_time - start_time
        for suite_result in self.result.suites:
            if self.result.suites[suite_result].status in [ResultStatus.PASSED, ResultStatus.KNOWN_ISSUES]:
                self.result.passed_suites += 1
            elif self.result.suites[suite_result].status == ResultStatus.FAILED:
                self.result.failed_suites += 1
            else:
                self.result.crash_suites += 1
        
    def get_testsuites(self, sortflag=True):
        self.suites_in_scope=unittest.TestSuite()     
        suite_list = sorted(self.suite_dict.keys()) if sortflag else self.suite_dict.keys()
        for suite_name in suite_list:
            case_list = sorted(self.suite_dict[suite_name])
            suite_module = importlib.import_module("%s.%s" % (self.TESTSUITE_FOLDER, suite_name))
            suite_classes = inspect.getmembers(suite_module)
            for class_name, class_obj in suite_classes:
                if class_name == suite_name:
                    suite = unittest.TestSuite(map(class_obj,case_list))
                    suite_in_scope = self.check_suite_scope(suite, suite_name)
                    if suite_in_scope:
                        self.suites_in_scope.addTest(suite_in_scope)
        if not self.suites_in_scope._tests:
            self.logger.warning("No test cases are running in current scope")
        for insuite in self.suite_dict:
            if len(self.suite_dict[insuite])>0:
                self.logger.info("include testsuite %s cases: %s" % (insuite, ",".join(self.suite_dict[insuite])))
        
    def check_suite_scope(self, suite, suite_name):
#        suite_scopes = {}
        cases_not_in_scope = []
        casenames_not_in_scope = []
        for case in suite._tests:
            case_name = case._testMethodName
            if hasattr(suite, "global_scopes"):
                case_scopes = suite.global_scopes
            else:
                case_scopes = case.scopes
#            suite_scopes[case_name] = []
            case_scopes = [item.lower() for item in case_scopes]
            is_in_scope = False
            if "all" in self.scopes:
                is_in_scope = True
#                suite_scopes[case_name] = ["all"]
            else:
                for scope in self.scopes:
                    if scope in case_scopes:
                        is_in_scope = True
#                        suite_scopes[case_name].append(scope)
            if not is_in_scope:
                cases_not_in_scope.append(case)
                if case_name in self.suite_dict[suite_name]:
                    self.suite_dict[suite_name].remove(case_name)
                    casenames_not_in_scope.append(case_name)
        if cases_not_in_scope:
            self.logger.debug("Removing cases not in scope: %s" % ",".join(casenames_not_in_scope))
        else:
            self.logger.info("All cases are included in %s current scope" % suite_name)
        for case in cases_not_in_scope:
            suite._tests.remove(case)
        if not suite._tests:
            del(self.suite_dict[suite_name])
            return None
        return suite
    
    def set_scope(self):
        if self.config.has_key("scope") and self.config["scope"]:
            self.result.scope_info = self.config["scope"]
            self.scopes=[]
            for item in self.config["scope"].split(','):
                self.scopes.append(item.strip().lower())
        else:
            self.scopes = ["all"]
            self.result.scope_info = "all"
        self.logger.info("Scope is set to: %s" % ','.join(self.scopes))
    
    def filter_test_mapping(self):
        self.filter_include_testsuites()
        self.filter_exclude_testsuites()
        self.filter_include_testcases()
        self.filter_exclude_testcases()
    
    def get_test_mapping(self):
        suites_path = Utils.get_filestr([self.TESTSUITE_FOLDER], "")
        suites_filelist = os.listdir(suites_path)
        suites_dict={}
        for suite_file in suites_filelist:
            if suite_file.endswith(".py"):
                suite_name = suite_file[0:suite_file.rfind('.')]
                case_dict = Utils.class_browser("%s.%s" % (self.TESTSUITE_FOLDER,suite_name))
                if case_dict:
                    case_list = []
                    for case in case_dict[suite_name].methods:
                        if case[0:4] == 'test':
                            case_list.append(case)
                    suites_dict[suite_name]=case_list
        if not suites_dict:
            self.logger.warning("No test suites found in TestSuite folder")
        return suites_dict

    def filter_include_testsuites(self):
        include_testsuites = []
        if self.config.has_key("include_testsuite"):
            include_testsuites = self.config["include_testsuite"].split(",")
        if len(include_testsuites)>0:
            origin_suite_dict=Utils.create_entity(self.suite_dict)
            self.suite_dict.clear()
            nomatchsuite = []
            for insuite in include_testsuites:
                if origin_suite_dict.has_key(insuite):
                    self.suite_dict[insuite]=origin_suite_dict[insuite]            
                else:
                    nomatchsuite.append(insuite)
            self.logger.debug("Include test suites: %s" % ",".join(self.suite_dict.keys()))
            if len(nomatchsuite)!=0:
                self.logger.warning("Following include suites: %s are not matched with any suite" % ",".join(nomatchsuite))
        else:
            self.logger.debug("All test suites to be included in configuration")
    
    def filter_exclude_testsuites(self):
        exclude_testsuites = []
        if self.config.has_key("exclude_testsuite"):
            exclude_testsuites = self.config["exclude_testsuite"].split(",")
        if len(exclude_testsuites)>0:
            nomatchsuite = []
            matchsuite = []
            for exsuite in exclude_testsuites:
                if exsuite in self.suite_dict.keys():
                    del self.suite_dict[exsuite]
                    matchsuite.append(exsuite)
                else:
                    nomatchsuite.append(exsuite)
            if len(matchsuite)>0:
                self.logger.debug("Skip test suites: %s" % ",".join(matchsuite))
            if len(nomatchsuite)!=0:
                self.logger.warning("Exlude suite: %s not find " % ",".join(nomatchsuite))
    
    def filter_include_testcases(self):
        include_testcases = []
        matchcase = []
        if self.config.has_key("include_testcase"):
            include_testcases = self.config["include_testcase"].split(",")
        if len(include_testcases)>0:
            origin_suite_dict=Utils.create_entity(self.suite_dict)
            for insuite in self.suite_dict:
                self.suite_dict[insuite]=[]
            nomatchcase = Utils.create_entity(include_testcases)
            for insuite in origin_suite_dict:
                for incase in origin_suite_dict[insuite]:
                    if incase in include_testcases:
                        self.suite_dict[insuite].append(incase)
                        matchcase.append(incase)
                        if incase in nomatchcase:
                            nomatchcase.remove(incase)
            if len(nomatchcase)!=0:
                self.logger.warning("Following include cases: %s are not matched with any case" % ",".join(nomatchcase))
            if len(matchcase)!=0:
                self.logger.debug("Chorus will only run test cases from INCLUDE_TESTCASES: %s" % ",".join(matchcase))
    
    def filter_exclude_testcases(self):
        exclude_testcases = []
        matchcase = []
        if self.config.has_key("exclude_testcase"):
            exclude_testcases = self.config["exclude_testcase"].split(",")
        if len(exclude_testcases)>0:
            nomatchcase = Utils.create_entity(exclude_testcases)
            for excase in exclude_testcases:
                for insuite in self.suite_dict:
                    if excase in self.suite_dict[insuite]:
                        self.suite_dict[insuite].remove(excase)
                        matchcase.append(excase)
                        if excase in nomatchcase:
                            nomatchcase.remove(excase)
            if len(matchcase)>0:
                self.logger.debug("Skip test cases: %s" % ",".join(matchcase))
            if len(nomatchcase)!=0:
                self.logger.warning("Following exclude cases: %s are not matched with any case" % ",".join(nomatchcase))