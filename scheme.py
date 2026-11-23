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

def add_to_queue(string):
    tokens = string.replace("("," ( ").replace(")"," ) ").replace("'"," ' ").split()
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
symbol_define = getsymbol("define")
symbol_quote = getsymbol("quote")
symbol_lambda = getsymbol("lambda")
symbol_if = getsymbol("if")
symbol_begin = getsymbol("begin")
symbol_let = getsymbol("let")

# built-in functions
def builtin_cons(arguments):
    if len(arguments)!=2:
        raise Exception("Wrong number of arguments for 'cons'")
    return arguments;
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
    
setglobalvalue(getsymbol("cons"), builtin_cons)
setglobalvalue(getsymbol("car"), builtin_car)
setglobalvalue(getsymbol("cdr"), builtin_cdr)
setglobalvalue(getsymbol("+"), builtin_plus)
setglobalvalue(getsymbol("-"), builtin_minus)
setglobalvalue(getsymbol("<"), builtin_less)

# simple evaluation (no tail-end recursion and no continuations yet)
# the environment is either None, or a tuple of 3 elements:
#   list of arguments (symbols)
#   list of parameters (values)
#   link to outer environment, or None
def evaluate(v, environment):
    if isinstance(v,int):    # symbol look-up
        # search through stack of environments
        ev = environment
        while not (ev is None):
            try:
                idx = ev[0].index(v)
                return ev[1][idx]
            except ValueError:
                ev = ev[2]
        # if not found use global value
        return getglobalvalue(v)
    
    elif isinstance(v,list):  # list
        head = v[0]
        remainder = v[1]
        if head is symbol_define:
            if isinstance(remainder,list) and isinstance(remainder[1],list):
                p0 = remainder[0]
                if isinstance(p0, int):     # define just a symbol
                    setglobalvalue(p0, evaluate(remainder[1][0], environment))
                    return None
                elif isinstance(p0, list) and isinstance(p0[0],int):   # define a symbol as a function 
                    arguments = []
                    arem = p0[1]
                    while isinstance(arem,list):
                        if not isinstance(arem[0],int):
                            raise Exception("Argument not a symbol")
                        arguments.append(arem[0])
                        arem = arem[1]
                    setglobalvalue(p0[0], ( arguments, remainder[1] ) )                    
                    return None
            raise Exception("Wrong syntax for 'define'")
        elif head is symbol_quote:
            if isinstance(remainder,list) and remainder[1] is None:
                return remainder[0]
            raise Exception("Wrong syntax for 'quote'")
        elif head is symbol_if:
            if not (isinstance(remainder,list) and isinstance(remainder[1],list)):
                raise Exception("Wrong syntax for 'if'")
            if not (evaluate(remainder[0],environment) is False):
                return evaluate(remainder[1][0], environment)
            elif isinstance(remainder[1][1], list):
                return evaluate(remainder[1][1][0], environment)
            else:
                return None
        elif head is symbol_begin:
            last = None
            while isinstance(remainder,list):
                last = evaluate(remainder[0],environment)
                remainder = remainder[1]
            return last
        elif head is symbol_let:
            if not (isinstance(remainder,list) and isinstance(remainder[1],list)):
                raise Exception("Wrong syntax for 'let'")
            varlist = remainder[0]
            parameters = []
            arguments = []
            while isinstance(varlist, list):
                vardef = varlist[0]
                varlist = varlist[1]
                if not (isinstance(vardef, list) and isinstance(vardef[0],int) and isinstance(vardef[1],list)):
                    raise Exception("Wrong syntax for variable block in 'let'")
                parameters.append(vardef[0])
                arguments.append(evaluate(vardef[1][0], environment))
            ev = (parameters, arguments, environment)
            expressionlist = remainder[1]
            last = None
            while isinstance(expressionlist, list):
                last = evaluate(expressionlist[0], ev)
                expressionlist = expressionlist[1]
            return last        
        else:  # some function call
            func = evaluate(head, environment)
            arguments = []
            while isinstance(remainder, list):
                arguments.append(evaluate(remainder[0],environment))
                remainder = remainder[1]
            if isinstance(func,types.FunctionType): # built-in function
                return func(arguments)
            elif isinstance(func,tuple): # lambda function
                if len(func[0]) != len(arguments):
                    raise Exception("Number of parameters does not match")
                # create new environment for evaluation
                ev = (func[0], arguments, environment)
                # evaluate all expressions in function and return result of last
                body = func[1]
                result = None
                while isinstance(body, list):
                    result = evaluate(body[0], ev)
                    body = body[1]
                return result                    
            else:
                raise Exception("Calling non-procedure")
    elif v is None:
        raise Exception("Can not evaluate empty list")
    else:
        return v
        
# main program
if len(sys.argv)>1:
    with open(sys.argv[1]) as fp:
        add_to_queue(fp.read())
while True:
    v = readvalue()
    if v==None:
        break;
    try:
        r = evaluate(v, None)
        if r is None and isinstance(v,list) and v[0] is symbol_define:
            pass    # do not write result of define
        else:
            writevalue(r)
            print()
    except Exception as e:
#        traceback.print_tb(e.__traceback__)
        print(e)    
