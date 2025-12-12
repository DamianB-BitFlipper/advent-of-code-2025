---
dev_time: 180
loc: 76
runtime: 0.2
cpu: 99%
peak_memory: 13152
---
# Remarks

Part 1 was trivial, the input was such that there are no loops in the graph and the number of paths from "you" to "out", even on the full input is low enough that a naive BFS solves it.

Part 2 is where it gets more fun. This problem took me three hours, but it was three hours of not the same level of concentration as day 9's three hours. 

Reading the problem, I initially thought that the main insight was that to go from "svr" to "out" via both "dac" and "fft" was just the sum of ("svr" -> "dac") * ("dac" -> "fft") * ("fft" -> "out") and ("svr" -> "fft") * ("fft" -> "dac") * ("dac" -> "out").

Implementing this was easy. Running it showed it was taking too long and too much memory. I needed to be more clever with the algorithm. After some time, I realized a so called "reverse fill" approach. Rather than starting at the source and doing BFS to the destination ("dest"), start at the destination and work ones way backwards.

The gist is as follows: First build a reverse index of the graph. Then start at the dest node and record a path count of 1. The path count is the number of paths to "dest". The initial case is 1 path to itself. 

Then look up all nodes that have "dest" as their child nodes. Remove "dest" from the child node and increment the path count to "dest" for these nodes (initially all 0). Loop on repeat for all new fully resolved nodes (all children have been removed during the looping).

This approach is not incorrect, but not the whole solution. Not all nodes from "dest" back to "source" are going to get fully resolved, so the above loop will stop short.

Then I need to somehow resolve the rest of the graph. This is where, due to sleep deprivation, I spent more time than I should have, and had I simply thought more clearly initially could have saved some effort. I won't document the failed approaches since, in retrospect, they may have been viable and I simply missed one KEY detail, which is why they weren't working.

The approach that worked was to do incremental substitution from the "source" until it had no more children to substitute. On each substitution, add the path count to "dest" of the node being substituted out to source's path count to "dest". This is possible since when building the resolutions above, even if "dest" does have children, they are removed since when constructing a path from "source" to "dest", we stop at "dest".

For example, if "source" has children ["a", "b"], and "a" has one child ["b"] and "b" has one child ["c"] with path count 5 (meaning the reverse step was able to resolve that "c" could reach "dest" in 5 different ways). The forward substitution steps would be:

```
source: (["a", "b"], 0)
source: (["b", "c"], 0)
source: (["c"], 5)
source: ([], 10)
```

So "source" as 10 ways to go to "dest".

There was one gotcha which was a bit tricky to debug because the small input was passing. In earlier attempts, I used a set to represent the children for fast lookup. The issue is that if a substitution substitutes two of the same node, that "2" factor is lost. When I replaced the set with a "Counter" and factored the multiplicative factor in the number of paths, everything worked out.

In fact in hindsight, this may have been the KEY bug that I missed previously that led me to scrap those approaches. The reason I found this bug in this approach is because the logic is so dead simple and correct, that I was certain it was not the algorithm that was wrong.

Looking forward to tomorrow's and (unfortunately) the last problem.
