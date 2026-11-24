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
  
(a 'argument-a)
(b)
(c)
(d 'argument-d)
(e 'argument-e)

