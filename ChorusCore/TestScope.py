'''
Created on Jan 25, 2014

@author: mxu
@target: give a scope class, and let user to inherit and change it.
'''
class Scope:    
    All = "all"
    Smoke = "smoke"
    Sanity = "sanity"
    Regression = "regression"
    
def setscope(*scopes):
    def register_wrapper(obj):
        '''
        If obj is class, set the local(case level) scope, otherwise set the global scope
        '''
        scope_list = []
        for scope in scopes[::-1]:
            scope_list.append(scope)
        if type(obj).__name__ == "function":
            obj._scopes = scope_list
        else:
            obj.global_scopes = scope_list         
        return obj
    return register_wrapper