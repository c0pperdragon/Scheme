( define (fibonacci n) 
  ( if (< n 2)
    '(1 0)
    ( with s (fibonacci (- n 1))
      (cons (+ (car s) (car (cdr s))) s) ) ) )
    
(fibonacci 20)
