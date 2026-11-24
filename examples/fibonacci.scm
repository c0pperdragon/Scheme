( define (fibonacci n) 
  ( if (< 2 n)
    ( begin
      ( let ((s (fibonacci (- n 1))))
        (cons (+ (car s) (car (cdr s))) s) ) )
    '(1 0) ) )
    
(fibonacci 20)



