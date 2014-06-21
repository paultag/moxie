square = (x) -> x * x

math =
  root:   Math.sqrt
  square: square
  cube:   (x) -> x * square x
