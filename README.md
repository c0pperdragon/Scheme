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
lambda             | tuple: (arguments, list of expressions, environment)
continuation       | dict

## Challenges

There are some non-trivial aspects to the scheme evaluator that make the language hard to implement
but very powerful. I managed to get these things working:

* Lexical variable scope
* Evaluate tail-end recursive constructs without recursion
* Continuations with call/cc 

