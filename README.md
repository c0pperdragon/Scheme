# Scheme

Small experimental Scheme interpreter written in Python.
Nothing fancy, just to learn the basics.

## Data types

To keep the thing slim, I just try to use a simple mapping of scheme data types 
to python types without use of classes. 

Scheme             | Python
------------------ | -------------------- 
None               | None
#t                 | True
#f                 | False
numeric            | float
CONS cell          | list: [car, cdr]
empty list         | set: {} 
symbol             | tuple: (index,name)
built-in function  | function
