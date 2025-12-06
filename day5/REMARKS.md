---
time: 73
loc: 63
---
# Remarks

It seems like the days of brute forcing your way thought Advent of Code are over. I implemented part 1 in the naive brute force method, but it was taking too long for the full input. So I decided to implement a compacted range logic. I never got the chance to utilize the `sortedcontainers` package, and I found this problem to be a suitable use case, especially because of the `bisect_left` and `bisect_right` properties. Once part 1 was solved "properly", part 2 was trivial.
