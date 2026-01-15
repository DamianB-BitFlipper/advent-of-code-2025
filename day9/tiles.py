import math
import random
import re
from collections import namedtuple
from collections.abc import Iterator
from itertools import combinations
from pathlib import Path
from typing import cast

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")

Point = namedtuple("Point", ["x", "y"])
type Edge = tuple[Point, Point]

random.seed(42)


class Polygon:
    def __init__(self):
        self.h_edges = []
        self.v_edges = []

        self.min_x = math.inf
        self.max_x = -1
        self.min_y = math.inf
        self.max_y = -1

    @staticmethod
    def stably_sort_edge(p1: Point, p2: Point) -> Edge:
        # Pick the point with the smaller x. If a tie, pick the smaller y
        return cast(Edge, tuple(sorted([p1, p2])))

    def add_edge(self, edge: Edge):
        # Make sure to stably sort the `edge`
        edge = self.stably_sort_edge(*edge)

        # Add the `edge` to its respective `self.h_edges` or `self.v_edges`
        if edge[0].y == edge[1].y:
            self.h_edges.append(edge)
        else:
            assert edge[0].x == edge[1].x
            self.v_edges.append(edge)

        # Update the mins and maxes accordingly
        self.min_x = min([self.min_x, edge[0].x])
        self.max_x = max([self.max_x, edge[1].x])
        self.min_y = min([self.min_y, edge[0].y])
        self.max_y = max([self.max_y, edge[1].y])

    def is_point_inside(self, test_point: Point) -> bool:
        # Short circuit test if the point is outside of the rectangular bounding box
        if (
            test_point.x < self.min_x
            or test_point.x > self.max_x
            or test_point.y < self.min_y
            or test_point.y > self.max_y
        ):
            return False

        # Next test if the point is on an edge, which counts as being inside
        for h_edge in self.h_edges:
            if h_edge[0].y == test_point.y and h_edge[0].x <= test_point.x <= h_edge[1].x:
                return True

        for v_edge in self.v_edges:
            if v_edge[0].x == test_point.x and v_edge[0].y <= test_point.y <= v_edge[1].y:
                return True

        # Keep a parity counter which will toggle with each intersection of the vertical edge
        inside = False
        for v_edge in self.v_edges:
            # This will only hit the leftward rays. To prevent double counting,
            # consider edges half-open ignoring the top
            if v_edge[0].x < test_point.x and v_edge[0].y <= test_point.y < v_edge[1].y:
                # Toggle the `inside` parity
                inside = not inside

        return inside


# Make this take one argument for easier mapping
def compute_area(points: tuple[Point, Point]) -> int:
    p1, p2 = points
    # Add 1 since side lengths start from 1
    return (abs(p2.x - p1.x) + 1) * (abs(p2.y - p1.y) + 1)


def trace_edges(points: tuple[Point, Point]) -> Iterator[Point]:
    """Yield all of the points on the edges of the rectangle formed by `points`."""
    # Convert `points` in to a top left and bottom right point `p1` and `p2` respectively
    p1 = Point(min(p.x for p in points), min(p.y for p in points))
    p2 = Point(max(p.x for p in points), max(p.y for p in points))

    dx = p2.x - p1.x
    dy = p2.y - p1.y

    # Yield the corners first since they have high likelihood of being outside of the polygon
    yield p1
    yield Point(p1.x, p1.y + dy)
    yield p2
    yield Point(p1.x + dx, p1.y)

    # Iterate the rest of the edges picking random points in [1, dx) X [1, dy) space
    diffs = (
        [(0, diffy) for diffy in range(1, dy)]
        + [(diffx, dy) for diffx in range(1, dx)]
        + [(dx, dy - diffy) for diffy in range(1, dy)]
        + [(dx - diffx, 0) for diffx in range(1, dx)]
    )
    random.shuffle(diffs)

    for diffx, diffy in diffs:
        yield Point(p1.x + diffx, p1.y + diffy)


def part1():
    points = []
    with IN_FILE.open("r") as f:
        for entry in f:
            match = re.match(r"(\d+),(\d+)", entry)
            assert match
            points.append(Point(int(match.group(1)), int(match.group(2))))

    max_area = max(map(compute_area, combinations(points, 2)))
    print(f"Part 1 max area: {max_area}")


def part2():
    points = []
    with IN_FILE.open("r") as f:
        for entry in f:
            match = re.match(r"(\d+),(\d+)", entry)
            assert match
            points.append(Point(int(match.group(1)), int(match.group(2))))

    polygon = Polygon()
    for p1, p2 in zip(points, points[1:] + [points[0]], strict=True):
        polygon.add_edge((p1, p2))

    # Form a rectangle for every two points combinations, ordered from largest to smallest
    rectangles = sorted(combinations(points, 2), key=compute_area, reverse=True)

    for i, rect in enumerate(rectangles):
        print(f"Processed {i} / {len(rectangles)}")
        for point in trace_edges(rect):
            if not polygon.is_point_inside(point):
                break
        else:
            print(f"Part 2 max area: {compute_area(rect)}")
            return

    # There should always be a solution
    raise AssertionError()


if __name__ == "__main__":
    part1()

    part2()
