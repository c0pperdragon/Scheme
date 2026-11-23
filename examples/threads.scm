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
    ( lambda 
      ()
      (usercode)
      (stop) ) ) )

( define (yield)
  ( let ((executable (dequeue)))
    ( call/cc 
      ( lambda 
        (cc)
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
      (display from)
      (display " ")
      (display to)
      (newline)
      (yield)
      (hanoi store to from (- amount 1)) ) ) )

(display "Solving 3 instances of 'Towers of Hanoi' in parallel")
(newline)
(start (lambda () (hanoi 'X 'Y 'Z 2)))
(start (lambda () (hanoi 'A 'B 'C 3)))
(start (lambda () (hanoi '1 '2 '3 4)))
(finish-all)
(display "Done")
(newline)
