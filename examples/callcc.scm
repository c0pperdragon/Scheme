; use call/cc to break out of deep nesting

( define fibocc 0)
( define timer 0)

( define (fibo n)
  (set! timer (+ timer 1))
  ( if (>= timer 10000)
    (fibocc (list 'timeout timer))
    ( if (< n 2)
      1
      (+ (fibo (- n 1)) (fibo (- n 2))) ) ) )
    
( define (runfibo5 cc)
  (set! fibocc cc)
  (set! timer 0)
  (fibo 4) )
  
( define (runfibo20 cc)
  (set! fibocc cc)
  (set! timer 0)
  (fibo 20) )
  
(call/cc runfibo5)
(call/cc runfibo20)
(fibocc 'after_completion)
