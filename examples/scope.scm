; test accessability of variable bindings

(define x 'global)

( define (a x) 
  (list 'a x) )
( define (b)
  (list 'b x) )
( define (c) 0 )
( ( lambda (x) 
    (set! c (lambda () (list 'c x))) )
    'local-lambda )
( define (d x) 
  (list 'd (eval 'x)) )
( define (e x)
  (list 'e (b) ((lambda () (list 'lamba x)))) )
( define (test_environment)
  ( with x 14 
    ( with y 7
      ( with x 3    
        (display (list 'inner_x  x 'inner_y y)) 
        (newline) )
      (display (list 'outer_x  x 'outer_y y)) 
      (newline) ) ) )
; make closure with access functions
(define inc 0)
(define dec 0)
(define get 0)
( with counter 42
  (set! inc (lambda () (set! counter (+ counter 1))))
  (set! dec (lambda () (set! counter (- counter 1))))
  (set! get (lambda () counter)) )  
  
(a 'argument-a)
(b)
(c)
(d 'argument-d)
(e 'argument-e)
(test_environment)
a
(define counter 99)
(get)
(inc)
(inc)
(get)
(dec)
(get)
counter
