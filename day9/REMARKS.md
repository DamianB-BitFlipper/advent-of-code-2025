---
dev_time: 200
loc: 108
runtime: 40.0
cpu: 98%
peak_memory: 124144
---
# Remarks

This problem was a doozy! The first part was trivial. I solved it in 5 minutes, and I thought that today's challenge would be a breeze. Part 2 was another beast.

The main challenge was identifying an efficient algorithm which determines if a point is inside or outside of a shape enclosure. It took me 4 attempts to find a a correct and efficient (enough) algorithm. Below I have enumerated my attempts and their shortcomings.

1. Take the point and extend rays in all 4 cardinal directions, north, south, east, and west. If all for rays hit an edge of the polygon, then the point is inside of the polygon. This fails when the polygon has a cavity with a bend. Then a point inside of this cavity will have edges in all four cardinal directions, but still be outside.

2. Take the point and extend the same rays. Then for each point along the rays path should also have four edges in all cardinal directions. This solves the problem with a simple L shaped cavity, but an S shaped cavity will suffer from the same shortcoming. Also running all of these iterations is terribly inefficient.

3. Simply store the whole grid space in memory. Start from point (0, 0) which should be outside of the shape and run a full BFS to identify all points outside of the polygon. By nature of the problem, the outside space is fully connected with itself. I validated this approach before implementing it fully thankfully. The main shortcoming were that for the full input, the grid space would have taken ~9GB of RAM which is unacceptable. And there is no guarantee that the BFS to fill the outside space would not have taken forever also.

4. The final algorithm that worked and was efficient enough (with some other clever optimizations) was the "light bouncing" approach. It works as follows: Take the point and first check if it is on the edge of the polygon. If yes, return `True` immediately. If no, begin the light bouncing algorithm. First extend rays in all four cardinal directions. If any ray does not hit an edge, immediately return `False`. If all four hit an edge, let us name the points right before the edge the "reflection" points. Keep track of a `seen` set of points. Add the initial point as well as these reflection points to the `seen` set. For all reflection points not yet seen, continue by sending rays in all four cardinal directions for each reflection point. If not all rays hit an edge, return `False`, etc. Do this in a loop until it either exits by returning `False` or there are no new reflection points to process. In this case, return `True`. The reason this algorithm works is because the polygon has no holes and the invariant that if a point is inside of the shape, all rays will stay inside of the shape. If the point is outside of the shape, at least one ray will be able to "bounce" its way out of the shape's cavities to where it no longer has edges in all four directions of itself.

With this algorithm, then the approach to solve the problem was to:

a) Sort the rectangles from most area to least area.
b) For each rectangle in this order, ensure all points on its four borders are inside of the polygon.
c) Return on the first polygon to pass this criterion.

Note that despite algorithm 4 working an being efficient-ish, it was by no means efficient enough to solve this problem on its own. I had to also employ the following clever optimizations.

1. Memoize (`lru_cache(maxsize=None)`) the method which takes a point and returns the edges in all four cardinal directions or (`None`) if no such edge exists. The insight here is that by nature of the problem, the solution rectangle will be some pair of points from the input set. There are going to be many candidate rectangles that share edges, so the method will be called with the same input point. As the problem is deterministic and stateless once the map has loaded, this method will always return the same result for the same input. So this input <-> result combination can be cached and not recomputed.

2. Store the horizontal edges (hedges) and vertical edges (vedges) of the polygon separately and in sorted order. All hedges consist of two point pairings that share the same Y coordinates. So the hedges can be sorted by this stable Y key from top to bottom. The same approach also applies for the vedges sorting in the X direction. Keeping these edges sorted allows for easy search space pruning of edge candidates to determine if there exists an edge in some cardinal ray direction from a point. For example, given point A, to determine if there is a hedge north of it, it is possible to quickly identify the place in hedges (right bisection point) where all further hedges have greater Y coordinates than A.y and hence are south of it, not north. The same logic applies for the horizontal cardinal directions and the vedges list.

3. When tracing the borders of a candidate rectangle, the naive approach would be to start at the top-left corner and iterate first down, then rightward, then up, then leftward. Remember, for each point on this border, we apply the efficient-ish algorithm 4 from above. The optimization is to yield points randomly on the borders of the candidate rectangle. The insight here is that if a point is inside of the polygon, it is quite likely that its two adjacent neighbors are also inside of the polygon. The randomization jumps around the candidate rectangle and has a higher change of jumping to a border point not in the polygon sooner than the naive trace approach. Both approaches will yield the same result, but I tried to quantitively measure if the randomization indeed helps or simply adds needless overhead. With randomization, the full input problem was solved in approximately 3 minutes and 30 seconds. Without randomization and just tracing the borders, the execution took so long I had to simply kill the program. I was not expecting randomization to play such an enormous role in speeding up the result.

In short, part 2 sounded trivial like problem one. But it turns out that determining whether a point is inside of a closed polygon is white nontrivial. I am sure there must be a smarter algorithm and approach than the one I outlined above. But at least the one above is fully my original creation.

# Implementing with Proper Algorithm

After solving this problem "my way", I decided to look up a proper algorithm to determine if a point is within a polygon. The algorithm "ray-casting" is remarkably simple. Draw a ray from a known point outside of the polygon to your test point. Then count the number of edges this ray intersects. If it intersects an odd number of edges, the test point is inside the polygon. If it is an even number of times, it is outside.

I implemented this by choosing a ray which is always horizontal. That way, I only have to test vertical edge intersections of the polygon. The first implementation, has a small bug where edges would get double counted for all points tested where a ray hits the top of one edge and the bottom of another. The solution is to only track edges as half open, where the bottom of an edge counts, but the top of an edge does not count.

The mental model is instead of picturing a ray intersecting edges, imagine edges stacking. Take all vertical edges of the polygon and fold them in to a 1D line by stacking them with their relative y positions in tact. Then it becomes clear that if a vertical edge stops and then a new vertical edge begins, this should be treated as one continuous vertical line and this meeting point should not get double count. By incorporating the half open edges, the issue gets mitigated.

This solution runs much faster than my solution above.
