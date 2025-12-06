---
description: Generate a tweet for an AoC day
---

Generate a tweet for Advent of Code 2025 Day $1.

Read the REMARKS.md file at day$1/REMARKS.md to understand:
- How long it took (the `time` frontmatter field, in minutes)
- How many lines of code (the `loc` frontmatter field)
- Any interesting observations or struggles

Read the solution code in day$1/ to identify the core algorithm or approach used.

Write a single tweet (under 280 chars) following this exact style:

Format: "AoC 2025 Day $1: [approach/algorithm] [was/took] [casual commentary]. [optional comparison to other days or personal reflection]. [time] min, [loc] LoC. [github url]"

Examples of the desired style:
- "AoC 2025 Day 4: grid sweeps was pretty easy. Honestly I was expecting a harder problem given yesterday's problem. 29 min, 47 LoC."
- "AoC 2025 Day 3: Required linearized DFS algorithm. Took 68 min and 55 LoC. I feel like this years problems are harder than last years."
- "AoC 2025 Day 2: trying too hard to use modulos until I realized that repetition checking with strings simplified everything. 22 min, 46 LoC."
- "Advent of Code 2025 Day 1: brute force ftw. Part 1 used mod math, but part 2 was much simpler (after too much time wasted handling edge cases intelligently) to brute force. 57m, 43 LoC."

Key style points:
- Start with "AoC 2025 Day $1:" (can use "Advent of Code" for Day 1)
- Name the algorithm/approach casually (e.g., "grid sweeps", "brute force", "DFS")
- Include honest personal commentary about difficulty, mistakes made, or realizations
- Compare to previous days if relevant
- End with stats: "[time] min, [loc] LoC" format
- Always include the GitHub URL on its own line at the end: https://github.com/DamianB-BitFlipper/advent-of-code-2025/tree/main/day$1

Do NOT:
- Use hashtags
- Use emojis
- Sound enthusiastic or salesy
- Use words like "excited", "amazing", "journey", "dive in"

Before outputting the final tweet, reason through:
1. What was the author's actual experience/feeling from REMARKS.md?
2. What mistakes or realizations did they have?
3. How did this day compare to previous days (if mentioned)?
4. Draft 2-3 tweet variations matching the example style
5. Evaluate each variation for character count and natural tone

Finally, output the best tweet clearly labeled as "Suggested tweet:" followed by just the tweet text (including the GitHub URL on its own line).
