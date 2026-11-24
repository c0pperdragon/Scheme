# Scheme

Small experimental Scheme interpreter written in Python.
Nothing fancy, just to learn the basics.

## Data types

To keep the thing slim, I just try to use a simple mapping of scheme data types 
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
