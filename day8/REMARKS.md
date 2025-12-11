---
dev_time: 40
loc: 61
runtime: 0.49
cpu: 99%
peak_memory: 70848
---
# Remarks

When I read the problem, I thought I would need some intelligent data structure to not need to compute all of the distances between paired junction boxes. But then I inspected the full input, and it only had 1000 junction boxes, meaning a total of 1e6 pairings. My computer is more than capable of handling this. So I just proceeded to compute the distances as a pairing and using a minheap, pluck out the closes pairings and process them. Once the foundation was build, part 1 and part 2 were pretty trivial.

I'll be sure to revisit this problem and explore any data structure or algorithm for finding the closes N pairs without needing to compute all of the pairings first. I am sure such algorithm exists and would be super interested in learning it! 
