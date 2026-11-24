import sys
import types
import traceback
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
        writevalue(v(0))
        writevalue(v(1))
    else:                      # unknown
        print("?",v, end="")
                
# global data storage for symbol values
globalcontext = []               

def getglobalvalue(symbol):
    if symbol>=len(globalcontext):
        raise Exception("Undefined symbol: "+identifiers[symbol])
    v = globalcontext[symbol]
    if v is globalcontext:
        raise Exception("Undefined symbol: "+identifiers[symbol])
    return v
    
def setglobalvalue(symbol,v):
    while symbol>=len(globalcontext):
        globalcontext.append(globalcontext)  # use the dictionary itself to denote undefined value
    globalcontext[symbol] = v
    
# predefined symbols used for syntax
symbol_quote = getsymbol("quote")
symbol_define = getsymbol("define")
symbol_lambda = getsymbol("lambda")
symbol_if = getsymbol("if")
symbol_begin = getsymbol("begin")
symbol_let = getsymbol("let")
symbol_set = getsymbol("set!")
symbol_eval = getsymbol("eval")

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
    
    
setglobalvalue(getsymbol("null?"), builtin_null)
setglobalvalue(getsymbol("car"), builtin_car)
setglobalvalue(getsymbol("cdr"), builtin_cdr)
setglobalvalue(getsymbol("cons"), builtin_cons)
setglobalvalue(getsymbol("list"), builtin_list)
setglobalvalue(getsymbol("+"), builtin_plus)
setglobalvalue(getsymbol("-"), builtin_minus)
setglobalvalue(getsymbol("<"), builtin_less)

# evaluation of a top-level element
# it is only here, that define is allowed
def evaluate_toplevel(v):
    if isinstance(v,list) and v[0] is symbol_define:
        tail = v[1]
        if isinstance(tail,list) and isinstance(tail[1],list):
            p0 = tail[0]
            if isinstance(p0, int):     # define a global symbol
                setglobalvalue(p0, evaluate(tail[1][0], None))
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
        return evaluate(v, None)

# simple evaluation (no continuations yet)
# the environment is either None, or a tuple of 3 elements:
#   list of arguments (symbols)
#   list of parameters (values)
#   link to outer environment, or None
def evaluate(v, environment):
    global recursiondepth
    global highestrecursiondepth
    recursiondepth=recursiondepth+1
    highestrecursiondepth = max(highestrecursiondepth,recursiondepth)
    res=evaluate2(v, environment)
    recursiondepth=recursiondepth-1
    return res
    
def evaluate2(v, environment):
    # use loop to avoid recursion in some cases. each iteration will always either
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
        
        elif isinstance(v,list):  
            head = v[0]
            tail = v[1]
            # some syntax contructs start with a hardcoded symbol
            if head is symbol_quote:
                if isinstance(tail,list) and tail[1] is None:
                    return tail[0]
                raise Exception("Wrong syntax for 'quote'")
            elif head is symbol_define:
                raise Exception("Can only define at top level")
            elif head is symbol_lambda:   # define a lambda function
                if isinstance(tail,list) and isinstance(tail[1],list):
                    arguments = []
                    arem = tail[0]
                    while isinstance(arem,list):
                        if not isinstance(arem[0],int):
                            raise Exception("Argument not a symbol")
                        arguments.append(arem[0])
                        arem = arem[1]
                    if isinstance(tail[1], list):
                        return ( arguments, tail[1], environment )
                raise Exception("Wrong syntax for 'lambda'")
            elif head is symbol_if:
                if not (isinstance(tail,list) and isinstance(tail[1],list)):
                    raise Exception("Wrong syntax for 'if'")
                if not (evaluate(tail[0],environment) is False):
                    v = tail[1][0]
                    continue
                elif isinstance(tail[1][1], list):
                    v = tail[1][1][0]
                    continue
                else:
                    return None
            elif head is symbol_begin:
                if isinstance(tail,list):
                    while isinstance(tail[1],list): # not yet reached the last expression
                        evaluate(tail[0],environment)
                        tail = tail[1]
                    v = tail[0]   # evaluate last without recursion
                    continue
                else:
                    raise Exception("Wrong syntax for 'begin'")
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
                    arguments.append(evaluate(vardef[1][0], environment))
                    varlist = varlist[1]
                environment = (parameters, arguments, environment)
                tail = tail[1]
                while isinstance(tail[1],list): # not yet reached the last expression
                    evaluate(tail[0],environment)
                    tail = tail[1]
                # do tail-end recursion
                v = tail[0]
                continue
            elif head is symbol_set:
                if not (isinstance(tail,list) and isinstance(tail[0],int) and isinstance(tail[1],list)):
                    raise Exception("Wrong syntax for 'set!'")
                # symbol lookup in local environments
                sym = tail[0]
                ev = environment
                while not (ev is None):
                    if sym in ev[0]:
                        ev[1][ev[0].index(sym)] = evaluate(tail[1][0], environment)
                        return None
                    else:
                        ev = ev[2]
                # check in global environment and raise exception if undefined
                getglobalvalue(sym)
                setglobalvalue(sym, evaluate(tail[1][0], environment))
                return None
            elif head is symbol_eval:
                if not (isinstance(tail,list) and tail[1] is None):
                    raise Exception("Wrong syntax for 'eval'")
                return evaluate(evaluate(tail[0], environment), None)
            # some function call                
            else:  
                func = evaluate(head, environment)
                arguments = []
                while isinstance(tail, list):
                    arguments.append(evaluate(tail[0],environment))
                    tail = tail[1]
                if isinstance(func,types.FunctionType): # built-in function
                    return func(arguments)
                elif isinstance(func,tuple): # lambda function
                    if len(func[0]) != len(arguments):
                        raise Exception("Number of parameters does not match")
                    environment = func[2]    # use environment of the function definition
                    if len(arguments)>0:  # when having parameters, extend the environment
                        environment = (func[0], arguments, environment)
                    # evaluate all expressions in function and return result of last                    
                    tail = func[1]
                    while isinstance(tail[1],list): # not yet reached the last expression
                        evaluate(tail[0],environment)
                        tail = tail[1]
                    # do tail-end recursion
                    v = tail[0]
                    continue
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
        recursiondepth=0
        highestrecursiondepth=0
        r = evaluate_toplevel(v)
        print("Recursion:",recursiondepth,highestrecursiondepth)
        if r is None and isinstance(v,list) and v[0] is symbol_define:
            pass    # do not write result of define
        else:
            writevalue(r)
            print()
    except Exception as e:
#        traceback.print_tb(e.__traceback__)
        print(e)    
