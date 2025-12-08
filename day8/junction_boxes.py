import heapq
import operator
import re
from collections import namedtuple
from functools import reduce
from itertools import combinations
from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
# N_CONNECTIONS = 10

IN_FILE = Path("./full_input.txt")
N_CONNECTIONS = 1000

Point = namedtuple("Point", ["x", "y", "z"])


def compute_euclidean_distance_sq(p1: Point, p2: Point) -> int:
    """Computes the euclidean distance squared used for sorting.

    Return an int since all of the point coordinates are integers."""
    return (p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2 + (p2.z - p1.z) ** 2


def populate_primitives() -> tuple[list[tuple[int, Point, Point]], list[set[Point]]]:
    points = []
    distances = []
    circuits = []
    with IN_FILE.open("r") as f:
        for line in f:
            match = re.match(r"(\d+),(\d+),(\d+)", line)
            assert match
            x = int(match.group(1))
            y = int(match.group(2))
            z = int(match.group(3))

            points.append(Point(x, y, z))

    # Initially add all junction boxes as single size circuits
    for point in points:
        circuits.append({point})

    # For all point X point combinations
    for p1, p2 in combinations(points, 2):
        dist = compute_euclidean_distance_sq(p1, p2)

        # Treat `distances` as a min heap
        heapq.heappush(distances, (dist, p1, p2))

    return distances, circuits


def part1():
    distances, circuits = populate_primitives()

    for _ in range(N_CONNECTIONS):
        # Get the next shortest distance
        _, p1, p2 = heapq.heappop(distances)

        # Connect the circuits with p1 and p2
        circuit1 = next(c for c in circuits if p1 in c)
        circuit2 = next(c for c in circuits if p2 in c)

        # The points are already in the same circuit, do nothing!
        if circuit1 is circuit2:
            continue

        # Join these two circuits
        circuits.append(circuit1 | circuit2)
        circuits.remove(circuit1)
        circuits.remove(circuit2)

    # Find the sizes of the top 3 circuits
    top3 = sorted(map(len, circuits), reverse=True)[:3]

    print(f"Part 1 top three product: {reduce(operator.mul, top3, 1)}")


def part2():
    distances, circuits = populate_primitives()

    last_connection = None
    while len(circuits) > 1:
        # Get the next shortest distance
        _, p1, p2 = heapq.heappop(distances)
        last_connection = (p1, p2)

        # Connect the circuits with p1 and p2
        circuit1 = next(c for c in circuits if p1 in c)
        circuit2 = next(c for c in circuits if p2 in c)

        # The points are already in the same circuit, do nothing!
        if circuit1 is circuit2:
            continue

        # Join these two circuits
        circuits.append(circuit1 | circuit2)
        circuits.remove(circuit1)
        circuits.remove(circuit2)

    assert last_connection

    print(f"Part 2 X coord product: {last_connection[0].x * last_connection[1].x}")


if __name__ == "__main__":
    part1()

    part2()
