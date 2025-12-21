---
dev_time: 1200 
loc: 134
runtime: 2048.19
cpu: 313%
peak_memory: 1403824
---
# Remarks

Today's problem was borderline impossible. But since this was the last problem of the Advent of Code 2025, it really made for a solid grand finale. Similarly to previous problems, the formulation was misleadingly simple. By the time I understood the problem's difficulty, it was too late. I was too invested and had to solve this challenge. Essentially it was to implement a feasibility check for tetris-like shape packing (including rotations) in a predefined area; e.g. can these shapes fit in this NxM grid?

I tried FOUR (4) different algorithmic approaches, each with their numerous attempts and failures within, before landing on an approach that was efficient enough. Below I will recount each of the four algorithmic attempts in order and the lessons learned from each.

Attempt 1: Dancing Links

When reading the problem, it screamed DFS search with backtracking. Incidentally, a few weeks ago, I implemented a Sudoku solver which utilized the same backbone structure. There is a clever data structure for solving such problems called Dancing Links, popularized by Donald Knuth. Essentially it reformulates the DFS search as this 2D grid of linked elements. It does not inherently make any optimizations from naive DFS, but the benefit is with this reformulation, it is much easier to see and make these prunings.

At this point of solving the problem, I was overconfident. After all, this was the Part 1 of today's problem and all previous Part 1's were relatively easy. It was the Part 2's that were the challenging ones. So I decided to have some fun and implement Part 1 using the Dancing Links.

Debugging the data structure was tricky since the bulk of the challenge with Dancing Links is getting the initial problem state set up. And this is difficult to debug since you just have to work with small problems, inspect the data structure and look out for any anomalies. Eventually, once the structure was set up, then the solving algorithm could be ported 1:1 from my sudoku solver directly. Incidentally, I discovered a few bugs in my sudoku Dancing Links solver that did not cause any problems then, but did in this context. The corrected Dancing Links solver is somewhere buried in the git history of this repository.

Finally, I implemented it all and it was time to run it on the demo input (not even the full input). For reference, the demo input has two feasible packings and one infeasible packing. With dancing links, the feasible packings were solved, although not as quickly as I would like, then the infeasible one would just hang. Mind you, the demo input had a grid space of 12x5 with 7 shapes to pack. The full input had areas on the order of 40x40 with 80 shapes to pack. When I saw how much dancing links was struggling, I knew this approach would be futile. I did not want to deal with optimizing the linking and unlinking operations of this 2D structure, where the majority of the time was being spent after a quick profile. 

Attempt 2: Bitmaps with DFS

So I scrapped the Dancing Links code entirely, and decided to implement the DFS using more traditional methods. I was still overconfident, but not as much as initially. I decided to have some fun and experiment with using bitmaps in Python. I installed a library `bitarray` which implements bitmap arrays in C with a nice API in Python.

So I reformulated the problem by representing the grid area as a bitarray and each shape as smaller bitarrays. Then when packing a shape, I would OR it in the grid area's bitarray, checking if there are any 1's there indicating a collision. There was a bit of a challenge in that bitarrays are a 1D primitive, so I had to write a convenience class that abstracted the 2D primitives in to 1D native primitives. Additionally the ORing of the shape bitmap needed some attention as well, where two rows of the area bitmap would be `area.width` bits apart. This was some tedious boilerplate, but eventually I implemented a so-called OR-mask for each shape. Given the size of the area it is getting OR'd in to, there would be the correct amount of padding 0s needed so that the OR can be done as a single operation. Then the correct bits would get set in the 1D space that to achieve the 2D OR effect.

I implemented this algorithm using bitmaps, and tried the demo input again. And to my surprise, the infeasible solution still hung! At this point, my overconfidence was shattered and it was time to buckle down and think hard. No more for fun experiments.

The good thing about using bitmaps was that it was already hyper efficient from a memory and mutations perspective. There was not much more efficiency that could be extracted from optimizing in this direction. So I had to move to pruning and simplifying the search space.

The first obvious optimization was to identify that some shapes are rotationally symmetrical. Take the letter 'I'. If one rotates it 180 degrees, it has the same footprint. Therefore, it only makes sense to test its 0 degree and 90 degree configurations. This optimization unfortunately only applied to two of the six shapes, so I knew that it would not be enough to speed up the solver. But it would help nonetheless.

The second less trivial pruning opportunity was realizing that there was a lot of reflective symmetry in this problem since the base grid area is rectangular. One can reformulate this as a mathematical invariant where if a solution exists then three other solutions can be trivially derived from this one. And if no solution exists, then reflection does not help. Take a packing that is fully in the top-left 1st quadrant of the grid area. By reflecting vertically, there is an equivalent reflected solution where the packing is in the top-right quadrant. Also by reflecting horizontally there packing is in the bottom-left quadrant. Lastly by reflecting both horizontally and vertically the packing in in the bottom-right quadrant.

Since this problem is purely interested in feasibility, eliminating this reflective symmetry would cut the search space down by 4 which is massive. I went ahead and implemented this by defining a custom `hash` function for the bitmap arrays with the unique property that any packing of the four possible reflections would yield the same hash value. The was done by understanding the bit representations of each of the four reflections and encoding this in a rotation agnostic manner. I will spare the details, but it essentially I would has a given configuration, then reflect it vertically, horizontally and both and hash those. Then the resulting hash would be the sum of all intermediate hashes. This was implemented efficiently without the need to copy any extra bits.

After I implemented this, I truly believed I had solved Part 1. Part 1 was after all supposed to be trivial to implement. Unfortunately I was baffled when the demo input still took a long time. At least I was managing to prove the invisibility of the 3rd problem of the demo input. But nonetheless when I gave this to the full input, it was hanging. This would not be the solution.

There are two final optimizations that I came up with. The first is the translational symmetry and the second is the the notion of tightly packing. 

The former deals with the idea that if there is a solution that is anchored at position (0,0) and extends left and down 5 units, then this same solution would be valid if it was anchored at (1,0), (2,0), (3,0) ..., etc. for a grid area of 12x5. There are many valid solutions.

The latter is the idea that if a solution exists where not all shapes are touching to form one large shape packing, then the shapes can always be packed more tightly. Conversely if no tight packing exists, then a loose packing will also never exist.

Implementing both of these required a different approach where instead of starting with the grid area predefined as a bitmap, I would start with a bitmap of size 1x1 and every time I add a shape tightly to the existing packing, I would grow the bitmap area to fit the new packing. I would then terminate the packing once it was too big for the problem. Nothing about this code was particularly noteworthy apart from the tedium. I define tightly packing as placing a shape at a position where there is always a filled cell in one of the eight cardinal directions. This is a loose definition of tightly packing since the anchor point of the placed shape is not always guaranteed to be occupied based on the shape's geometry, but it was good enough.

After implementing this approach, it was actually slower than the full grid bitarray approach. This is likely because after every shape placement, the bits need to be shuffled to expand the grid area. This takes time and cannot be done efficiently.

At this point, I was at wits end. I could try to implement the translational and tight packing optimizations in to the full grid bitarray approach, but I lost confidence in this if I was unable to get it to work reasonably by now.

At this point, I turned to sparring with an LLM to come up with a better algorithmic approach. Note that in this problem, all of the code in the final solution is mine. I intentionally just used the LLMs as sparring partners for the challenge and spirit of Advent of Code.

The LLM suggested some neat algorithmic pruning approaches such as the pigeon-hole principle and branch-and-bound. You can read on what these are if they are unfamiliar to you. For branch-and-bound, the knapsack problem can be implemented using this really quite illustratively. But nonetheless, I could not think of a simple enough way to implement either for this algorithm. At this point, my confidence was shattered, and I was taking much more cautious steps.

But these suggestions from the LLM did remind me about day 10 and how I used a integer linear programming to solve it. 

Approach 3: Integer Linear Programming

Under the hood, linear programming solvers do branch-and-cut, which is a sophisticated variant of branch-and-bound. So I thought, if I was able to reformulate this problem as an ILP problem, then the solver would take care of the optimizations.

I proceeded to define a grid of variables and each shape copy would also be its own variables. I did not want to think too much about restricting reflective symmetry and the like. So I formulated the problem in the most naive way hoping the solver would be smart enough. I made these variables binary and then defined summation constraints that prevent two shapes from overlapping. Basically by summing all of the shapes on a given cell, the value should be <= 1. If it is > 2, then two shapes overlap and this solution is incorrect. I also took care of rotations by adding a constraint where for a given shape, only the variables of a particular rotation can be active at one time.

Finally I gave this formation to PuLP, a LP solver, and the demo input was actually solved reasonably quickly. Where the above methods took 20 seconds, the ILP approach took only 2 seconds. 

Then I gave it to the full input, and it hung again!

I did not know what to do. I asked the LLM if there were any glaring optimization issues with my solution. I did point out that I was trying to solve a discrete satisfiablity problem using an LP solver. The LP solvers are made to find optima in a continuous space, not satisfiablity in a a discrete space. However, it did point me to a class of solvers made for this type of problem, the CP-SAT solver (Constraint Programming SAT solver).

Approach 4: CP-SAT

I installed a CP-SAT solver from the Google `or-tools`. And looking at its documentation, I was able to translate the ILP formulation to a CP-SAT formulation. At first I did not encode any optimizations with respect to translational and reflective symmetry. This took some effort since the API of a CP-SAT solver was new to me. It also required a new paradigm of programming more akin to logic-programming. Thinking in this manner was new to me as well.

Eventually, I had the base implementation in CP-SAT ready. Running it on the demo input solved it in 0.6 seconds. Now this was going somewhere. Running it on the full input, I did see a speed up. So I let it run. Each problem from the full set was taking approximately 20 seconds to finish, but it was finishing! Given the full input was 1000 such problems, I was not ready to let my laptop roast for 5.5 hours straight. But given this was working, I started digging deeper to understand how formulate CP-SAT problems effectively and correctly. The challenge with this type of programming is that diagnosing performance issues is tricky since you have to understand the gist of how the solver attacks the problem and then formulate it in a way that lends itself well to the solver's internal mechanisms.

I used the LLM quite a bit as a sparring partner, especially since I was also not used to logic programming. There were a few optimizations that really helped and a few that did not. I will start with the ones that did not help much.

1. Translational symmetry. I added a constraint requiring that the 1st row and 1st column must have a filled in cell. This anchors the shape to these border, thus eliminating any sliding the packing could do.

2. Rotational symmetry. I added a constraint that the packing must be top-left heavy. Ie, the number of occupied cells in the top left quadrant must be greater than all other quadrants. Any reflections would break this constraint, so only one configuration will satisfy it.

3. Permutation symmetry. I gave each anchor cell a unique order number (1:1 mapping) `(x, y, rotation) -> ord_id`. Then `ord_id` I enforced that shape copies of the same shape must be added to the grid in ascending `ord_id`. This was tricky to formulate in a logic manner, but the LLM helped. What this solves is the symmetry in placing shape copy 1 at position (10, 10, rotation=90 degrees) and copy 2 at position (0, 0, rotation=0) versus copy 0 at (0, 0, 0) and copy 1 at (10, 10, 90). In theory this should have eliminated a combinatorial amount of symmetries.

With CP-SAT solvers, it is difficult to know if a given optimization will yield anything, or slow it down. Oftentimes the optimization sounds like a good idea only for you to realize it makes it worse! Probably with practice, one could get better at this, but the solver really is a magic black box.

Now I will outline the two optimizations that did make an outsized impact.

1. Tracking shape counts. Treating each shape copy as its own shape, this balloons the number of variables the solver has to optimize for. One of the patterns I learned is the few the variables, the better it is for the solver. I instead treat each shape as a class of its own. I then add a constraint that this shape must appear N times in the grid. I still have boolean variables that say, one copy of the shape at this position and rotation. But rather than having N amount of these variables, I just have the variables once and require that N of them be active.

2. Storing the grid state explicitly. This is where the LLM sparring really helped. I originally implemented the overlap constraint indirectly by enforcing that the sum of all shape variables must equal the total area. This was a 2D sum since for every cell position in the grid, I would iterate all variables and sum them up. The LLM said that such indirection often prevents the solver from making intelligent branching decisions since it does not have a good notion if a given cell is occupied or not. I do not fully understand the reasoning behind this, but by adding new boolean variables indicating if the cell is occupied or not, then adding a constraint that this variable is `True` if and only if one of the variables there is active, and finally constraining that the sum of these boolean cell variables (1D sum) is equal to the total area, I got a ~10x speed-up. This was shocking to me, but I will take it.

So now, each of the full inputs was taking approximately 3 seconds to complete. At 1000 problems, this would be about 50 minutes of runtime. At this point, I was quite done with the problem. I had sunk at least 20 hours of work in to it, so I decided to run the full input (and pray there were no bugs) on this.

Approximately 40 minutes later, I got my result. I input it in to the Advent of Code site and to my delight, it was the correct answer!

I was then bracing for Part 2, but as it turned out, there was no Part 2. It was just a cute story about how the elves were grateful for my work. They awarded me my second start for free.

