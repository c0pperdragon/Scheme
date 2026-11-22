import sys
from collections import deque 

# dictionary to keep symbols
symbols = dict()
# look up the symbol, or create it if not existing yet
def getsymbol(identifier):
    if identifier in symbols:
        return symbols[identifier]
    s = ( len(symbols), identifier)
    symbols[identifier] = s
    return s

# the one unique object (a set) for empty list
Empty = {}

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
        first = Empty
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
                        first = [v, Empty]
                        last = first
                    else:
                        c = [v, Empty]
                        last[1] = c
                        last = c
                        
    elif t=="'":
        return [getsymbol("quote"), [readvalue(), Empty]]
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
    if v==None:
        print("None", end="")
    elif v==True:
        print("#t", end="")
    elif v==False:
        print("#f", end="")
    elif isinstance(v,list):
        print("(", end="")
        writevalue(v[0])
        v=v[1]
        while isinstance(v,list):
            print(" ", end="")
            writevalue(v[0])
            v = v[1]
        if v!=Empty:
            print(" . ", end="")
            writevalue(v)
        print(")", end="")
    elif isinstance(v,float):
        if v.is_integer():
            print(int(v), end="")
        else:
            print(v, end="")        
    elif isinstance(v,tuple):
        print(v[1], end="")
    elif isinstance(v,set):
        print("()", end="")
    else:
        print("?",v,end="")
        
# main program
if len(sys.argv)>1:
    with open(sys.argv[1]) as fp:
        add_to_queue(fp.read())
while True:
    v = readvalue()
    if v==None:
        break;
    writevalue(v) 
    print()

