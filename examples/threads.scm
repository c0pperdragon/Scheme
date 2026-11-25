; simple concurrency library 
(define pending '())

( define (enqueue executable)
  (set! pending (append pending (list executable)))
  '() )

( define (dequeue)
  ( let ((executable (car pending)))
    (set! pending (cdr pending))
    executable ) )

( define (start usercode)
  ( enqueue 
    ( lambda ()
      (usercode)
      (stop) ) ) )

( define (yield)
  ( let ((executable (dequeue)))
    ( call/cc 
      ( lambda (cc)
        (enqueue cc)
        (executable) ) ) ) )

( define (stop)
  ((dequeue)) )

( define (finish-all)
  ( if (not (null? pending)) 
    ( begin
      (yield)
      (finish-all) ) ) )

; simple example usage
( define (hanoi from to store amount)
  ( if (<= amount 0)
    0
    ( begin 
      (hanoi from store to (- amount 1))
      (display (list from to))
      (newline)
      (yield)
      (hanoi store to from (- amount 1)) ) ) )
      
; solve 3 instances of towers of hanoi in parallel
(start (lambda () (hanoi 'X 'Y 'Z 2)))
(start (lambda () (hanoi 'A 'B 'C 3)))
(start (lambda () (hanoi '1 '2 '3 4)))
(finish-all)
