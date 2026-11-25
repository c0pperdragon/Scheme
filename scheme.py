import sys
import types
from collections import deque 
import traceback

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
    
def getvalue(symbol, environment):
    while not (environment is None):
        if symbol in environment[0]:
            return environment[1][environment[0].index(symbol)]
        else:
            environment = environment[2]
    if symbol>=len(globalcontext) or (globalcontext[symbol] is globalcontext):
        raise Exception("Undefined symbol: "+identifiers[symbol])
    return globalcontext[symbol]
    
def setvalue(symbol,v,environment):
    while not (environment is None):
        if symbol in environment[0]:
            environment[1][environment[0].index(symbol)] = v
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
    elif isinstance(v,list):   # pair (a.k.a. cons cell)
        print("(", end="")
        writevalue(v[0])
        v=v[1]
        while isinstance(v,list):
            print(" ", end="")
            writevalue(v[0])
            v = v[1]
        if v!=None:
            print(" . ", end="")
            writevalue(v)
        print(")", end="")
    elif isinstance(v,int):    # symbol
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
                    
# predefined symbols used for syntax
symbol_quote = getsymbol("quote")
symbol_define = getsymbol("define")
symbol_lambda = getsymbol("lambda")
symbol_if = getsymbol("if")
symbol_begin = getsymbol("begin")
symbol_let = getsymbol("let")
symbol_set = getsymbol("set!")

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
    if not isinstance(p0,list):
        raise Exception("Pair expected as argument for 'car'")
    return p0[0]
def builtin_cdr(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'cdr'")
    p0 = arguments[0]
    if not isinstance(p0,list):
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
        while isinstance(l,list):
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
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'eval'")
    r = yield from evaluate(arguments[0], None)
    return r
def builtin_callcc(arguments):
    if len(arguments)!=1:
        raise Exception("Wrong number of arguments for 'call/cc'")
    func = arguments[0]
    if not isinstance(func,tuple):  
        raise Exception("Argument to 'call/cc' must be a non-builtin function")
    cc = { 0: current_generator }
    call = [cc, [ [func, [cc,None]], None ] ]   # (cc (func cc))
    yield evaluate(call, None)  # let dispatcher switch generators to evaluate this
    # when dispatcher switches back to this continuation, resume caller
    return cc[1]

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

# evaluation of a top-level element
# it is only here, that define is allowed
def evaluate_toplevel(v):
    if isinstance(v,list) and v[0] is symbol_define:
        tail = v[1]
        if isinstance(tail,list) and isinstance(tail[1],list):
            p0 = tail[0]
            if isinstance(p0, int):     # define a global symbol
                defineglobalvalue(p0, dispatch_evaluation(tail[1][0]))
                return None
            elif isinstance(p0, list) and isinstance(p0[0],int):   # define a symbol as a function 
                arguments = []
                arem = p0[1]
                while isinstance(arem,list):
                    if not isinstance(arem[0],int):
                        raise Exception("Argument not a symbol")
                    arguments.append(arem[0])
                    arem = arem[1]
                if isinstance(tail[1],list):
                    defineglobalvalue(p0[0], ( arguments, tail[1], None ) )                    
                    return None
        raise Exception("Wrong syntax for 'define'")
    else:
        return dispatch_evaluation(v)
        
# do a complete evaluation execution, providing the bridge to the generator part  
def dispatch_evaluation(v):
    global current_generator
    current_generator = evaluate(v,None)
    try:
        # work through generators as requested by the computation run
        while True:
            current_generator = current_generator.__next__()
    except StopIteration as e:
        return e.value
    
# evaluation using generators to implement continuations
# the environment is either None, or a tuple of 3 elements:
#   list of arguments (symbols)
#   list of parameters (values)
#   link to outer environment, or None
def evaluate(v, environment):
    # to avoid many recusions, some goto's would be very convenient
    # in lack of goto, use some while's to have 2 branch targets
    while True:
        while True: # branch target (reached with 'continue' from everywhere)
            # symbol look-up, either local or global environments
            if isinstance(v,int):
                return getvalue(v,environment)
            # list evaluation
            elif isinstance(v,list):  
                head = v[0]
                tail = v[1]
                # some syntax contructs start with a hardcoded symbol
                if head is symbol_quote:
                    if not (isinstance(tail,list) and tail[1] is None):
                        raise Exception("Wrong syntax for 'quote'")
                    return tail[0]
                elif head is symbol_lambda:   # define a lambda function
                    if not(isinstance(tail,list) and isinstance(tail[1],list)):
                        raise Exception("Wrong syntax for 'lambda'")
                    arguments = []
                    arem = tail[0]
                    while isinstance(arem,list):
                        if not isinstance(arem[0],int):
                            raise Exception("Argument not a symbol")
                        arguments.append(arem[0])
                        arem = arem[1]
                    return ( arguments, tail[1], environment )
                elif head is symbol_if:
                    if not (isinstance(tail,list) and isinstance(tail[1],list)):
                        raise Exception("Wrong syntax for 'if'")
                    v = yield from evaluate(tail[0],environment)
                    if not (v is False):
                        v = tail[1][0]     
                        continue    # proper tail-end recursion
                    elif isinstance(tail[1][1], list):
                        v = tail[1][1][0]  
                        continue    # proper tail-end recursion
                    else:
                        return None
                elif head is symbol_begin:
                    if not isinstance(tail,list):
                        raise Exception("Wrong syntax for 'begin'")
                    v = tail
                    break
                elif head is symbol_let:
                    if not (isinstance(tail,list) and isinstance(tail[1],list)):
                        raise Exception("Wrong syntax for 'let'")
                    varlist = tail[0]
                    parameters = []
                    arguments = []
                    while isinstance(varlist, list):
                        vardef = varlist[0]
                        if not (isinstance(vardef, list) and isinstance(vardef[0],int) and isinstance(vardef[1],list)):
                            raise Exception("Wrong syntax for variable block in 'let'")
                        parameters.append(vardef[0])
                        v = yield from evaluate(vardef[1][0], environment)
                        arguments.append(v)
                        varlist = varlist[1]
                    environment = (parameters, arguments, environment)
                    v = tail[1]
                    break
                elif head is symbol_set:
                    if not (isinstance(tail,list) and isinstance(tail[0],int) and isinstance(tail[1],list)):
                        raise Exception("Wrong syntax for 'set!'")
                    v = yield from evaluate(tail[1][0], environment)   
                    setvalue(tail[0], v, environment)
                    return None
                # some function call                
                else:  
                    func = yield from evaluate(head, environment)
                    arguments = []
                    while isinstance(tail, list):
                        v = yield from evaluate(tail[0],environment)
                        arguments.append(v)
                        tail = tail[1]
                    if isinstance(func,types.FunctionType): # built-in function
                        v = func(arguments)
                        if isinstance(v,types.GeneratorType):
                            v = yield from v
                        return v
                    elif isinstance(func,tuple): # lambda function
                        if len(func[0]) != len(arguments):
                            raise Exception("Number of parameters does not match")
                        environment = func[2]    # use environment of the function definition
                        if len(arguments)>0:  # when having parameters, extend the environment
                            environment = (func[0], arguments, environment)
                        v = func[1]
                        break
                    elif isinstance(func,dict):  # continuation                    
                        if 1 in func: # continuation was already used
                            return func[1]
                        else:
                            func[1] = arguments[0] if len(arguments)>0 else None
                            yield func[0]
                        raise Exception("Generator continued after switching to other generator")
                    else:
                        raise Exception("Calling non-procedure")
            # everything else just evaluates to itself
            else:
                return v
        # this branch target can be reached from inner loop with break
        # here, v must be a list, all elements are evaluated and the last result is the overall result
        while isinstance(v[1],list): # not yet reached the last expression
            yield from evaluate(v[0],environment)
            v = v[1]
        v = v[0]
        continue     # proper tail-end recursion
        
# main program
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
        # traceback.print_tb(e.__traceback__)
