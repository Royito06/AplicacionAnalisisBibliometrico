#lang racket
  
(define (cuenta-atras n)

  (if (<= n 0)
      '()
 (cons n (cuenta-atras(- n 1))) 
 )
  
  )
  