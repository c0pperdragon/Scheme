import sys
import types
from collections import deque 
import traceback

def main():
    if len(sys.argv)>1:
        with open(sys.argv[1]) as fp:
            for line in fp:
                add_to_buffer(line)
    while True:
        v = readvalue()
        if v==None:
            break;
        try:
            r = evaluate_toplevel(v)
            if not (r is None):
                writevalue(r)
                print()
        except Exception as e:
            print(e)    
            traceback.print_tb(e.__traceback__)

# convenience 
def PAIR(v):        # is something a scheme pair?
    return isinstance(v,list)
def SYMBOL(v):        # is something a scheme symbol? 
    return isinstance(v,int)

# dictionary to keep symbols
symbols = dict()  # identifier -> int
identifiers = []  # int -> identifier

# look up the symbol, or create it if not existing yet
def getsymbol(identifier):
    if identifier in symbols:
        return symbols[identifier]
    s = len(identifiers)
    symbols[identifier] = s
    identifiers.append(identifier)
    return s

# global data storage for symbol values
globalcontext = []  # int -> value 

def defineglobalvalue(symbol, v):
    while len(globalcontext)<=symbol:
        globalcontext.append(globalcontext)
    globalcontext[symbol] = v

# accessing variables from the current/parent environment or global storage
def getvalue(symbol, environment):
    while not (environment is None):
        if symbol is environment[0]:
            return environment[1]
        else:
            environment = environment[2]
    if symbol>=len(globalcontext) or (globalcontext[symbol] is globalcontext):
        raise Exception("Undefined symbol: "+identifiers[symbol])
    return globalcontext[symbol]
    
def setvalue(symbol,v,environment):
    while not (environment is None):
        if symbol is environment[0]:
            environment[1] = v
            return
        else:
            environment = environment[2]
    if symbol>=len(globalcontext) or (globalcontext[symbol] is globalcontext):
        raise Exception("Undefined symbol: "+identifiers[symbol])
    globalcontext[symbol]=v

# facility to read scheme data from the input
readbuffer = deque()     # buffers the input broken into strings

def add_to_buffer(line):
    if ";" in line:
        line = line[:line.index(";")]
    tokens = line.replace("("," ( ").replace(")"," ) ").replace("'"," ' ").split()
    readbuffer.extend(tokens)
        
def readvalue():
    if len(readbuffer)<1:
        return None        
    t = readbuffer.popleft()
    
    if t==")": 
        raise Exception("Unexpected ')'")
    if t==".": 
        raise Exception("Unexpected '.'")
    
    if t=="(":
        first = None
        last = None
        dotfound = False
        while True:
            if len(readbuffer)<=0:
                raise Exception("Unexpected EOF inside list")
            t = readbuffer[0]           
            if t==")":
                readbuffer.popleft()
                return first
            elif t==".":
                readbuffer.popleft()
                dotfound = True
            else:
                v = readvalue()
                if dotfound:
                    if last!=None:
                        last[1]=v
                else:
                    if last==None:
                        first = [v, None]
                        last = first
                    else:
                        c = [v, None]
                        last[1] = c
                        last = c
                        
    elif t=="'":
        return [getsymbol("quote"), [readvalue(), None]]
    elif t=="#f":
        return False;
    elif t=="#t":
        return True;
    else:
        try:
            return float(t)
        except ValueError:
            return getsymbol(t)    

# write objects in scheme style
def writevalue(v):
    if v is None:  # empty list
        print("()", end="")
    elif v is True:
        print("#t", end="")
    elif v is False:
        print("#f", end="")
    elif PAIR(v):      # list or dotted pair
        print("(", end="")
        writevalue(v[0])
        v=v[1]
        while PAIR(v):
            print(" ", end="")
            writevalue(v[0])
            v = v[1]
        if v!=None:
            print(" . ", end="")
            writevalue(v)
        print(")", end="")
    elif SYMBOL(v):    # symbol
        print(identifiers[v], end="")
    elif isinstance(v,float):   # numeric
        if v.is_integer():
            print(int(v), end="")
        else:
            print(v, end="")        
    elif isinstance(v,types.FunctionType):  # built-in function
        print("#B", end="")
        print(hash(v), end="")
    elif isinstance(v,tuple):  # lambda function
        print("#L", end="")
        print(v[0], end="")
    elif isinstance(v,dict):  # continuation
        print("#C", end="")
        print(hash(v), end="")
    else:                      # unknown
        print("?",v, end="")
                    

# built-in functions
def builtin_null(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'null?'")   
    if arguments[0] is None:
        return True
    else:
        return False
def builtin_car(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'car'")
    p0 = arguments[0]
    if not PAIR(p0):
        raise Exception("Pair expected as argument for 'car'")
    return p0[0]
def builtin_cdr(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'cdr'")
    p0 = arguments[0]
    if not PAIR(p0):
        raise Exception("Pair expected as argument for 'cdr'")
    return p0[1]
def builtin_cons(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for 'cons'")
    return arguments;
def builtin_list(arguments):
    list = None
    for a in reversed(arguments):
        list = [a,list]
    return list;
def builtin_append(arguments):
    if len(arguments)<1:
        raise Exception("Wrong number of arguments for 'append'")        
    totallist = None
    last = None
    for a in arguments[:-1]:
        l = a
        while PAIR(l):
            e = [l[0], None]
            l = l[1]                
            if totallist is None:
                totallist = e
            else:
                last[1] = e
            last = e
    if totallist is None:
        return arguments[-1]
    else:
        last[1] = arguments[-1]
        return totallist
def builtin_plus(arguments):
    sum = 0
    for x in arguments:
        if not isinstance(x,float):
            raise Exception("Number expected for '+'")
        sum = sum+x
    return sum    
def builtin_minus(arguments):
    if len(arguments)<1:
        raise Exception("At least one argument expected for '-'")
    sum = None
    for x in arguments:
        if not isinstance(x,float):
            raise Exception("Number expected for '-'")
        if sum is None:
            sum = x
        else:
            sum = sum-x
    return sum
def builtin_less(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for '<'")
    if not (isinstance(arguments[0],float) and isinstance(arguments[1],float)):
        raise Exception("Need numbers for '<'")
    return arguments[0] < arguments[1]
def builtin_lessequal(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for '<='")
    if not (isinstance(arguments[0],float) and isinstance(arguments[1],float)):
        raise Exception("Need numbers for '<='")
    return arguments[0] <= arguments[1]
def builtin_greater(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for '>'")
    if not (isinstance(arguments[0],float) and isinstance(arguments[1],float)):
        raise Exception("Need numbers for '>'")
    return arguments[0] > arguments[1]
def builtin_greaterequal(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for '>='")
    if not (isinstance(arguments[0],float) and isinstance(arguments[1],float)):
        raise Exception("Need numbers for '>='")
    return arguments[0] >= arguments[1]
def builtin_not(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'not")
    if arguments[0] is False:
        return True
    else:
        return False
def builtin_display(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'display'")
    writevalue(arguments[0])
def builtin_newline(arguments):
    if len(arguments)!=0:
        raise Exception("Wrong number of arguments for 'newline'")
    print()
def builtin_eval(arguments): 
    raiseException("'eval' needs to be implemented in evaluation engine")
def builtin_callcc(arguments):
    raiseException("'call/cc' needs to be implemented in evaluation engine")

defineglobalvalue(getsymbol("null?"), builtin_null)
defineglobalvalue(getsymbol("car"), builtin_car)
defineglobalvalue(getsymbol("cdr"), builtin_cdr)
defineglobalvalue(getsymbol("cons"), builtin_cons)
defineglobalvalue(getsymbol("list"), builtin_list)
defineglobalvalue(getsymbol("append"), builtin_append)
defineglobalvalue(getsymbol("+"), builtin_plus)
defineglobalvalue(getsymbol("-"), builtin_minus)
defineglobalvalue(getsymbol("<"), builtin_less)
defineglobalvalue(getsymbol("<="), builtin_lessequal)
defineglobalvalue(getsymbol(">"), builtin_greater)
defineglobalvalue(getsymbol(">="), builtin_greaterequal)
defineglobalvalue(getsymbol("not"), builtin_not)
defineglobalvalue(getsymbol("display"), builtin_display)
defineglobalvalue(getsymbol("newline"), builtin_newline)
defineglobalvalue(getsymbol("eval"), builtin_eval)
defineglobalvalue(getsymbol("call/cc"), builtin_callcc)
defineglobalvalue(getsymbol("call-with-current-continuation"), builtin_callcc)

# predefined symbols used for syntax
symbol_quote = getsymbol("quote")
symbol_define = getsymbol("define")
symbol_lambda = getsymbol("lambda")
symbol_if = getsymbol("if")
symbol_begin = getsymbol("begin")
symbol_with = getsymbol("with")
symbol_set = getsymbol("set!")

    
# toolbox function to create a scheme function object
def create_function(parameterlist, code, environment):
    parameters = []
    while PAIR(parameterlist):
        if not SYMBOL(parameterlist[0]):
            raise Exception("Parameter not a symbol")
        parameters.append(parameterlist[0])
        parameterlist = parameterlist[1]
    if not PAIR(code):
        raise Exception("Function body must not be empty")
    return ( parameters, code, environment )                     

# evaluation of a top-level element
# it is only here, that define is allowed
def evaluate_toplevel(v):
    if PAIR(v) and v[0] is symbol_define:
        tail = v[1]
        if PAIR(tail) and PAIR(tail[1]):
            p0 = tail[0]
            if SYMBOL(p0):     # define a global symbol
                defineglobalvalue(p0, evaluate(tail[1][0]))
                return None
            elif PAIR(p0) and SYMBOL(p0[0]):   # define a symbol as a function 
                defineglobalvalue(p0[0], create_function( p0[1], tail[1], None))
                return None
            else:
                raise Exception("Wrong syntax for 'define'")
    else:
        return evaluate(v)
        
        
# evaluation implementation that uses generator functions  
def evaluate_with_generators(v):
    global current_generator
    current_generator = ev_g(v,None)
    try:
        # work through generators as requested by the computation run
        while True:
            current_generator = current_generator.__next__()
    except StopIteration as e:
        return e.value
    
# evaluation using generators to implement the state machine
# the environment is either None, or a tuple of 3 elements:
#   list of arguments (symbols)
#   list of parameters (values)
#   link to outer environment, or None
def ev_g(v, environment):
    # to avoid many recursions, some goto's would be very convenient
    # in lack of goto, use a loop and many continues 
    while True:
        # symbol look-up, either local or global environments
        if SYMBOL(v):
            return getvalue(v,environment)
        # list evaluation
        elif PAIR(v):  
            head = v[0]
            tail = v[1]
            # some syntax contructs start with a hardcoded symbol
            if head is symbol_quote:
                if not PAIR(tail):
                    raise Exception("Wrong syntax for 'quote'")
                return tail[0]
            elif head is symbol_lambda:   # define a lambda function
                if not(PAIR(tail) and PAIR(tail[1])):
                    raise Exception("Wrong syntax for 'lambda'")
                return create_function(tail[0], tail[1], environment)
            elif head is symbol_begin:
                if not PAIR(tail):
                    raise Exception("Wrong syntax for 'begin'")
                v = tail
                pass     # no return/continue: evaluate the whole list
            elif head is symbol_if:
                if not (PAIR(tail) and PAIR(tail[1])):
                    raise Exception("Wrong syntax for 'if'")
                v = yield from ev_g(tail[0],environment)
                if not (v is False):
                    v = tail[1][0]     
                    continue    # proper tail-end recursion
                elif PAIR(tail[1][1]):
                    v = tail[1][1]  
                    pass     # evalute the whole trailing list 
                else:
                    return None
            elif head is symbol_set:
                if not (PAIR(tail) and SYMBOL(tail[0]) and PAIR(tail[1])):
                    raise Exception("Wrong syntax for 'set!'")
                v = yield from ev_g(tail[1][0], environment)   
                setvalue(tail[0], v, environment)
                return None
            elif head is symbol_with:
                if not (PAIR(tail) and SYMBOL(tail[0]) and PAIR(tail[1]) and PAIR(tail[1][1]) ):
                    raise Exception("Wrong syntax for 'with'")
                v = yield from ev_g(tail[1][0], environment)
                environment = (tail[0], v, environment)
                v = tail[1][1]
                pass     # no return/continue: evaluate the whole list
            # other functions evaluate all parameters before the call                
            else:  
                func = yield from ev_g(head, environment)
                arguments = []
                while PAIR(tail):
                    v = yield from ev_g(tail[0],environment)
                    arguments.append(v)
                    tail = tail[1]
                if func is builtin_eval:    # built-in functions with special handling
                    if len(arguments)!=1:
                        raise Exeption("'eval' expects 1 argument")
                    v = arguments[0]
                    continue
                elif func is builtin_callcc:
                    if len(arguments)!=1:
                        raise Exception("Wrong number of arguments for 'call/cc'")
                    cc = { 0: current_generator }
                    call = [cc, [ [arguments[0], [cc,None]], None ] ]   # (cc (func cc))
                    yield ev_g(call, None)  # let dispatcher switch generators to evaluate this
                    return cc[1]
                elif isinstance(func,types.FunctionType): # built-in function
                    return func(arguments)
                elif isinstance(func,tuple): # lambda function
                    if len(func[0]) != len(arguments):
                        raise Exception("Number of parameters does not match")
                    environment = func[2]    # use environment of the function definition
                    for i in range(len(arguments)): # when having parameters, extend the environment
                        environment = (func[0][i], arguments[i], environment)
                    v = func[1]  
                    pass    # no return/continue: evaluate the whole list
                elif isinstance(func,dict):  # return to continuation                    
                    if 1 in func: # continuation was already used
                        return func[1]
                    else:
                        func[1] = arguments[0] if len(arguments)>0 else None
                        yield func[0]
                        return None
                else:
                    raise Exception("Calling non-procedure")
            # this position can be reached from the big list evaluation if-clause
            # by just falling out at the end without continue or return.
            # here, v must be a list, all elements are evaluated and the last result is the overall result
            while PAIR(v[1]): # not yet reached the last expression
                yield from ev_g(v[0],environment)
                v = v[1]
            v = v[0]
            continue     # proper tail-end recursion
        # everything else just evaluates to itself
        else:
            return v


# implementation with an explicit stack, completely contained in a single function
def evaluate_without_recursion(v):
    environment = None 
    s = [0]  # stack structure used by operations to know where to continue  
    l = 1    # simulate goto (as python does not have it)
    while l>0:  # run until hitting the prepared '0' on the stack
        if l==1:     # evaluate v and continue according to stack after that
            # symbol look-up, either local or global environments
            if SYMBOL(v):
                v = getvalue(v,environment)
                l = s.pop()
                continue                
            # list evaluation
            elif PAIR(v):  
                head = v[0]
                tail = v[1]
                # some syntax contructs start with a hardcoded symbol
                if head is symbol_quote:
                    if not PAIR(tail):
                        raise Exception("Wrong syntax for 'quote'")
                    v = tail[0]
                    l = s.pop() 
                    continue
                elif head is symbol_lambda:   # define a lambda function
                    if not(PAIR(tail) and PAIR(tail[1])):
                        raise Exception("Wrong syntax for 'lambda'")
                    v = create_function(tail[0], tail[1], environment)
                    l = s.pop()
                    continue
                elif head is symbol_begin:
                    if not PAIR(tail):
                        raise Exception("Wrong syntax for 'begin'")
                    v = tail
                    l = 2
                    continue
                elif head is symbol_if:   # if-clause 
                    if not (PAIR(tail) and PAIR(tail[1])):
                        raise Exception("Wrong syntax for 'if'")
                    s.append(tail[1]) # list containing the true and false branches
                    s.append(2)       # where to continue after evaluating condition
                    v = tail[0]       # the condition needs to be evaluated first
                    l = 4
                    continue                    
                elif head is symbol_set:
                    if not (PAIR(tail) and SYMBOL(tail[0]) and PAIR(tail[1])):
                        raise Exception("Wrong syntax for 'set!'")
                    s.append(tail[0])  # the symbol that needs to be set
                    s.append(5)        # where to continue after evaluation
                    v = tail[1][0]
                    l = 1
                    continue
                elif head is symbol_with:
                   if not (PAIR(tail) and SYMBOL(tail[0]) and PAIR(tail[1]) and PAIR(tail[1][1]) ):
                    raise Exception("Wrong syntax for 'with'")
##                    varlist = tail[0]
##                    parameters = []
##                    arguments = []
##                    while isinstance(varlist, list):
##                        vardef = varlist[0]
##                        if not (isinstance(vardef, list) and isinstance(vardef[0],int) and isinstance(vardef[1],list)):
##                            raise Exception("Wrong syntax for variable block in 'let'")
##                        parameters.append(vardef[0])
##                        v = yield from ev_g(vardef[1][0], environment)
##                        arguments.append(v)
##                        varlist = varlist[1]
##                    environment = (parameters, arguments, environment)
##                    v = tail[1]
##                    break    # evaluate the whole list
                # other functions evaluate all parameters before the call                
                else:  
                    raise Exception("not implemented")
                    
            # everything else just evaluates to itself
            else:
                l = s.pop()
                continue
                        
        elif l==2:     # evaluate all elements of a list in sequence, the last returns its value
            if PAIR(v[1]):    # not yet reached the last expression                    
                s.append(v[1])  # memorize remainder of the list to evaluate
                s.append(3)     # where to continue after evaluation
                v = v[0]        # what to evaluate
                l = 1
                continue
            else:   # last expression
                v = v[0]
                l = 1
                continue     # proper tail-end recursion                    
        elif l==3:   # after evaluation of a list item
            v = s.pop()
            l = 2
            continue                
        elif l==4:   # second part of if
            tail = s.pop()                                    
            if not (v is False):
                v = tail[0]     
                l = 1
                continue    # proper tail-end recursion
            elif PAIR(tail[1]):
                v = tail[1][0]  
                l = 1
                continue    # proper tail-end recursion
            else:
                v = None    # evaluates to None if condition is false and no else branch
                l = s.pop()  
                continue
        elif l==5:   # second part of set!
            sym = s.pop()
            setvalue(sym,v,environment)
            l = s.pop()
            continue
     # after encountering '0' on the continuation stack       
    return v
    

# decide on an evaluation engine
evaluate = evaluate_with_generators  
main()
