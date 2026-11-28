# Scheme

Small experimental Scheme interpreter written in Python.
Nothing fancy, just to learn the basics.

## Data types

To keep the thing slim, I just try to use a mapping of scheme data types 
to python types without use of classes. 

Scheme             | Python
------------------ | -------------------- 
empty list         | None
#t                 | True
#f                 | False
numeric            | float
symbol             | int
pair               | list: [car, cdr]
built-in function  | function
user function      | list: [λ,[environment,[ [arg1,[arg2,None]] ,[exp1,[exp2,[exp3,None ]]]]]]  
environment        | list: [parent_environment, [symbol . value]]
continuation       | list: [Ω, [generator . returnvalue]]


## Challenges

There are some non-trivial aspects to the scheme evaluator that make the language hard to implement
but very powerful. I managed to get these things working:

* Lexical variable scope
* Evaluate tail-end recursive constructs without recursion
* Continuations with call/cc 

## Restrictions

To keep it simple, I do not implement many of the Scheme libraries, and 
there is only one simple construct to define local variables ("with")
instead of the 3 flavours of "let".
