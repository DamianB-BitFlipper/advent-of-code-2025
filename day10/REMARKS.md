---
dev_time: 330
loc: 71
runtime: 2.73
cpu: 90%
peak_memory: 21856
---
# Remarks

Part 2 today was actually insane. I did not think it could get any harder than yesterday's part 2, but it did! It took me 3 distinct structural overhauls to solve, and I had to venture deep in to theoretical topics. Part 1 was also difficult, but manageable.

For Part 1, it was rather obvious to me that the approach would be a BFS through the button press search space to get to the target indicator positions. My first attempt worked flawlessly for the small input. But for the large input, it took too long. 

After inspecting the states, I came to the realization (which in retrospect is quite obvious), that once an indicator state repeats, there is no more need to try to continue searching deeper in to this state. 

The invariant is that if it repeats, then a previous path of button presses reached the same state, but in fewer presses. Once I added a `seen` set, the algorithm ran quickly and passed Part 1.

When I read Part 2, it at first seemed like a slight variation to Part 1 and that with a few small tweaks, I would get the solution. In fact, I was so confident, I thought that it was odd that Part 1 would be more difficult than Part 2. But boy was I WRONG.

My first approach was a similar BFS, but instead of a `seen` set, I would check if any joltage surpassed the target joltage and stop the branch's search there. That worked for the small input, but was taking impossibly long for even the first machine of the full input. 

Looking at that machine's definition, I found it odd that it was not massive, but actually reasonably small in side. So I looked deeper at my BFS algorithm to see if I could prune the search space even further. I did find a number of pruning approaches that did narrowed down the search space.

1. Add the intermediate joltage configurations to a `seen` set. The idea being that if we have seen the current joltage configuration before, there must be a path with less button presses.

2. Sort the button presses and add those to a `seen` set. The idea being that pressing button 3, then 2, then 3 again. That is the same as pressing 2 then 3 then 3. By sorting the press sequences, they would get them in a stable ordering, and we can prune like so.

After implementing these, the first machine of the full input was taking forever still. On top of that, I noticed that for the first machine, the memory consumption would increase steadily on my machine to 20% of RAM before I'd kill it. Clearly this was not on the right path.

So I took a step back and thought, ok BFS may not be it, then maybe DFS. I thought I could position the algorithm to press the buttons with the greatest impact first (ie: the button which adds the most joltages to the joltage configuration). Then DFS down this path. At some point it would overshoot, backtrack and try the 2nd most impactful button, etc.

I implemented this for the small input, and it did find a combination of button presses that made the joltages reach their targets, but this was not the minimum number of presses. Instead of drilling down the DFS path, I reverted back to BFS since I knew this was not it.

Back in BFS, I though I might need to be more clever. I tried instead of adding to a deque for traditional BFS, the queue would be a sorted list where the states with the smallest distance to the target joltage configuration would be at the front and those further away would be at the end. I was hoping we'd pick more "winning" configuration this way when doing the search (though this breaks from BFS and may not have produce the minimum number of button presses similarly to the DFS approach above). In short, this optimization was too slow as well.

At this point, I broke out the trusty cpu and memory profilers. I diagnosed that the majority of the time spent on the execution was in stupid memory copies and incrementing joltages. So I decided to bust out the big guns and encode EVERYTHING in bitmaps.

The approach was as follows:

I noticed that the largest joltage value in the full input was 266. Sadly higher than the 255 byte boundary, but not an issue. So I would represent the joltages as 9 bit numbers, followed by 1 bit of padding set to 0. The logic for the padding will become clear later. Then the buttons would be encoded as 0b0000000010 (eight 0s, one 1, then the same padding bit) over the joltage index where they should be affecting and 0s elsewhere.

Then the logic here would be all of the joltage bits would be concatenated in to one large number as well as the button bits. By nature of bits adding and there not being any overflow, what used to be a for loop to compute the next joltage configuration given a current configuration and button press is now an addition: `next_joltage_bits = cur_joltage_bits + button_bits`.

The padding is a neat trick to determine if the joltage configuration exceeded the target joltage configuration for pruning purposes. I would do `target_joltage_bits - next_joltage_bits`. If the target joltage bits are all greater for each section than the current joltage bits, then the subtraction will not underflow in to the padding bit. If at any place, the current joltage bits are greater than the target joltage bits, the subtraction would underflow, flipping the padding bit from a 0 to a 1. Then with a simple joltage padding mask and a logical AND, I can determine if any padding bits flipped and consequently if the current joltage is greater than the target joltage.

After implementing this, the large input was STILL taking too long and eating my memory. I then aggressively also rewrote the button press trackers to be bitmaps too. Similarly there would be 10 bits per button all concatenated, this time per button index. On a button press, it would add a 1 to the binary section of the button count. Then there would be a helper function which would decompose this binary bitmap in to a total sum of button presses. 

After implementing this, the memory was more in check and the program did run notably faster. I let it run on the firs machine for 10 minutes, still with no result. At this point, I was at wits end on how to proceed. I had NO new ideas.

I stepped back from the problem. When I returned to the problem, I had a true light bulb moment! I scrapped the BFS approach fully. Instead I would treat the buttons and target joltage configuration as a system of linear equations to solve. I knew it was possible to solve a system of linear equations using some linear algebra. I had to brush up on this and read over the process called Gaussian Elimination.

In short, this is a process where you represent the system of equations as a matrix (so called an augmented matrix) and reorganize/scale the rows to get a diagonal of 1s where everything under the 1s is a 0. If you cannot modify the matrix to this state, that either mean there are many solutions or no solutions. I was hoping (incorrectly) that the creators of this problem chose button and joltage combinations that always yield one solution. Of course, if I thought back to my DFS approach, there were multiple solutions to the first machine of the small input. But I didn't make this connection.

I then proceeded to implement my own Gaussian Elimination algorithm using numpy and computing the matrices by hand for the first machine of the full input. In fact, this machine has only one solution. But when I ran on the demo input, it failed because of the fact there are multiple solutions. 

What this meant is that I would have to use the augmented matrix with free variables, and try all possible discrete integer values of the free variables that yield the minimum button sum. This is NOT something I wanted to code.

Fortunately, thinking this problem as a system of linear equations reminded me of linear programming. In fact, the linear equations are the constraints of the linear program and the expression to optimize is the sum of the button presses, which should be minimized.

So I threw away my Gaussian Elimination and `numpy` code. Instead, I installed a python library (`pulp`) that is able to solve discrete integer linear programs. I expressed the machine's configuration as a linear program (which was not too difficult to do). Then set the optimization expression and told it to minimize it. 

To my surprise (at this point, I had low expectations), the result to the first machine of the full input came out after a fraction of a second. I could not believe my eyes that the problem that would run practically indefinitely and consume gigabytes of memory was solved so effortlessly. 

I then ran this program on the full input of machines and some 3 seconds later, I got a number which when entered into the Advent of Code site was the correct answer!

Phew. That was a hard problem.
