---
dev_time: 58
loc: 57
runtime: 0.02
cpu: 95%
peak_memory: 12304
---
# Remarks

Part 1 was trivial to solve. I decided to represent the grid as a class, but this was not necessary. For part 2, I did the naive (and harder) approach of keeping track of all paths, splitting paths as the pipes split. This worked for the smaller input, but was too inefficient for the full input. Then I realized I just needed the count, so I replaced tracking the full paths with just tracking the number of paths at a given index thus far. I should have thought of this approach honestly first, since it was both easier to reason able and considerably more efficient. 
