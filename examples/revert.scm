; tail-end recursive implementation of reverting a list

( define (revert l) 
  (revert2 '() l) )
    
( define (revert2 collected l)
  ( if (null? l)
    collected
    (revert2 (cons (car l) collected) (cdr l)) ) )
    
(revert '(a b c d e f g h i j k l m n o p q r s t u v w x y z))

