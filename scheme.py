import sys
import types
from collections import deque 

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

def getglobalvalue(symbol):
    if symbol>=len(globalcontext):
        raise Exception("Undefined symbol: "+identifiers[symbol])
    v = globalcontext[symbol]
    if v is globalcontext:
        raise Exception("Undefined symbol: "+identifiers[symbol])
    return v
    
def setglobalvalue(symbol,v):
    while symbol>=len(globalcontext):
        globalcontext.append(globalcontext)  # use the list itself to denote undefined value
    globalcontext[symbol] = v

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

setglobalvalue(getsymbol("null?"), builtin_null)
setglobalvalue(getsymbol("car"), builtin_car)
setglobalvalue(getsymbol("cdr"), builtin_cdr)
setglobalvalue(getsymbol("cons"), builtin_cons)
setglobalvalue(getsymbol("list"), builtin_list)
setglobalvalue(getsymbol("append"), builtin_append)
setglobalvalue(getsymbol("+"), builtin_plus)
setglobalvalue(getsymbol("-"), builtin_minus)
setglobalvalue(getsymbol("<"), builtin_less)
setglobalvalue(getsymbol("<="), builtin_lessequal)
setglobalvalue(getsymbol(">"), builtin_greater)
setglobalvalue(getsymbol(">="), builtin_greaterequal)
setglobalvalue(getsymbol("not"), builtin_not)
setglobalvalue(getsymbol("display"), builtin_display)
setglobalvalue(getsymbol("newline"), builtin_newline)
setglobalvalue(getsymbol("eval"), builtin_eval)
setglobalvalue(getsymbol("call/cc"), builtin_callcc)
setglobalvalue(getsymbol("call-with-current-continuation"), builtin_callcc)

# evaluation of a top-level element
# it is only here, that define is allowed
def evaluate_toplevel(v):
    if isinstance(v,list) and v[0] is symbol_define:
        tail = v[1]
        if isinstance(tail,list) and isinstance(tail[1],list):
            p0 = tail[0]
            if isinstance(p0, int):     # define a global symbol
                setglobalvalue(p0, dispatch_evaluation(tail[1][0]))
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
                    setglobalvalue(p0[0], ( arguments, tail[1], None ) )                    
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
    # use loop to avoid recursion in many cases. each iteration will always either
    # return from the function (with a value or an exception) or explicitely continue the loop
    while True:
        # symbol look-up, either local or global environments
        if isinstance(v,int):    
            ev = environment
            while not (ev is None):
                if v in ev[0]:
                    return ev[1][ev[0].index(v)]
                else:
                    ev = ev[2]
            return getglobalvalue(v)
        # list evaluation
        elif isinstance(v,list):  
            head = v[0]
            tail = v[1]
            # some syntax contructs start with a hardcoded symbol
            if head is symbol_quote:
                if not (isinstance(tail,list) and tail[1] is None):
                    raise Exception("Wrong syntax for 'quote'")
                return tail[0]
            elif head is symbol_define:
                raise Exception("Can only define at top level")
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
                r = yield from evaluate(tail[0],environment)
                if not (r is False):
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
                while isinstance(tail[1],list): # not yet reached the last expression
                    yield from evaluate(tail[0],environment)
                    tail = tail[1]
                v = tail[0]  
                continue     # proper tail-end recursion
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
                    r = yield from evaluate(vardef[1][0], environment)
                    arguments.append(r)
                    varlist = varlist[1]
                environment = (parameters, arguments, environment)
                tail = tail[1]
                while isinstance(tail[1],list): # not yet reached the last expression
                    yield from evaluate(tail[0],environment)
                    tail = tail[1]
                v = tail[0]  
                continue      # proper tail-end recursion
            elif head is symbol_set:
                if not (isinstance(tail,list) and isinstance(tail[0],int) and isinstance(tail[1],list)):
                    raise Exception("Wrong syntax for 'set!'")
                v = yield from evaluate(tail[1][0], environment)   # do evaluation, no matter if symbol can be set
                # symbol lookup in local environments
                sym = tail[0]
                ev = environment
                while not (ev is None):
                    if sym in ev[0]:
                        ev[1][ev[0].index(sym)] = v
                        return v
                    else:
                        ev = ev[2]
                getglobalvalue(sym)   # check for existance (raise exception otherwise)
                setglobalvalue(sym, v)
                return v
            # some function call                
            else:  
                func = yield from evaluate(head, environment)
                arguments = []
                while isinstance(tail, list):
                    r = yield from evaluate(tail[0],environment)
                    arguments.append(r)
                    tail = tail[1]
                if isinstance(func,types.FunctionType): # built-in function
                    r = func(arguments)
                    if isinstance(r,types.GeneratorType):
                        r = yield from r
                    return r
                elif isinstance(func,tuple): # lambda function
                    if len(func[0]) != len(arguments):
                        raise Exception("Number of parameters does not match")
                    environment = func[2]    # use environment of the function definition
                    if len(arguments)>0:  # when having parameters, extend the environment
                        environment = (func[0], arguments, environment)
                    tail = func[1]
                    while isinstance(tail[1],list): # not yet reached the last expression
                        yield from evaluate(tail[0],environment)
                        tail = tail[1]
                    v = tail[0]
                    continue     # proper tail-end recursion
                elif isinstance(func,dict):  # continuation                    
                    if 1 in func: # continuation was already used
                        return func[1]
                    else:
                        if len(arguments)>0:
                            func[1] = arguments[0]  # keep as result for later return
                        else:
                            func[1] = None
                        yield func[0]
                    raise Exception("Generator continues after switching to other generator")
                else:
                    raise Exception("Calling non-procedure")
        # eveything else just evaluates to itself
        else:
            return v
        
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
