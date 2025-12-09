import bisect
import re
from collections import namedtuple
from collections.abc import Iterator
from functools import lru_cache
from itertools import combinations
from pathlib import Path

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")

Point = namedtuple("Point", ["x", "y"])
type Edge = tuple[Point, Point]


# Make this take one argument for easier mapping
def compute_area(points: tuple[Point, Point]) -> int:
    p1, p2 = points
    # Add 1 since side lengths start from 1
    return (abs(p2.x - p1.x) + 1) * (abs(p2.y - p1.y) + 1)


def trace_edges(points: tuple[Point, Point]) -> Iterator[Point]:
    """Yield all of the points on the edges of the rectangle formed by `points`."""
    # Smaller x comes first, then smaller y acts as tie breaker
    p1, p2 = sorted(points)

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
    # random.shuffle(diffs)

    for diffx, diffy in diffs:
        yield Point(p1.x + diffx, p1.y + diffy)


class AmorphousPolygon:
    def __init__(self):
        # Container for horizontal and vertical edges
        self.hedges = []
        self.vedges = []

        # bind a cached function that captures the edges
        @lru_cache(None)
        def projection_intersects(p):
            return self._projection_intersects_uncached(p)

        self._projection_intersects = projection_intersects

    def add_line(self, p1: Point, p2: Point):
        # Smaller x comes first, then smaller y acts as tie breaker
        stable_order = tuple(sorted([p1, p2]))

        # Add horizontal edge
        if p1.y == p2.y:
            self.hedges.append(stable_order)
        else:  # p1.x == p2.x
            self.vedges.append(stable_order)

    def postprocess(self):
        """Assert that the `apolygon` was built correctly"""
        assert all(edge[0].y == edge[1].y for edge in self.hedges)
        assert all(edge[0].x < edge[1].x for edge in self.hedges)
        assert all(edge[0].x == edge[1].x for edge in self.vedges)
        assert all(edge[0].y < edge[1].y for edge in self.vedges)

        # Sort the hedges by increasing y coordinates
        self.hedges.sort(key=lambda edge: edge[0].y)

        # Sort the vedges by increasing x coordinates
        self.vedges.sort(key=lambda edge: edge[0].x)

    def _projection_intersects_uncached(
        self, point: Point
    ) -> tuple[Edge | None, Edge | None, Edge | None, Edge | None]:
        x_indexl = bisect.bisect_left(self.vedges, point.x, key=lambda edge: edge[0].x)
        x_indexr = bisect.bisect_right(self.vedges, point.x, key=lambda edge: edge[0].x)
        y_indexl = bisect.bisect_left(self.hedges, point.y, key=lambda edge: edge[0].y)
        y_indexr = bisect.bisect_right(self.hedges, point.y, key=lambda edge: edge[0].y)

        # A `point` is contained in this shape if it has a edge in all 4 directions
        north_edge = next(
            (
                edge
                for edge in reversed(self.hedges[:y_indexr])
                if edge[0].x <= point.x <= edge[1].x
            ),
            None,
        )
        south_edge = next(
            (edge for edge in self.hedges[y_indexl:] if edge[0].x <= point.x <= edge[1].x), None
        )
        east_edge = next(
            (edge for edge in self.vedges[x_indexl:] if edge[0].y <= point.y <= edge[1].y), None
        )
        west_edge = next(
            (
                edge
                for edge in reversed(self.vedges[:x_indexr])
                if edge[0].y <= point.y <= edge[1].y
            ),
            None,
        )

        return north_edge, south_edge, east_edge, west_edge

    def _does_projection_intersect(self, point: Point) -> bool:
        return all(self._projection_intersects(point))

    def __contains__(self, point: Point) -> bool:
        nearest_edges = self._projection_intersects(point)
        if not all(nearest_edges):
            return False

        north_edge, south_edge, east_edge, west_edge = nearest_edges
        assert north_edge is not None
        assert south_edge is not None
        assert east_edge is not None
        assert west_edge is not None

        north_projection_pass = all(
            [
                self._does_projection_intersect(Point(point.x, point.y - dy))
                for dy in range(1, point.y - north_edge[0].y + 1)
            ]
        )
        south_projection_pass = all(
            [
                self._does_projection_intersect(Point(point.x, point.y + dy))
                for dy in range(1, south_edge[0].y - point.y + 1)
            ]
        )
        east_projection_pass = all(
            [
                self._does_projection_intersect(Point(point.x + dx, point.y))
                for dx in range(1, east_edge[0].x - point.x + 1)
            ]
        )
        west_projection_pass = all(
            [
                self._does_projection_intersect(Point(point.x - dx, point.y))
                for dx in range(1, point.x - west_edge[0].x + 1)
            ]
        )

        return (
            north_projection_pass
            and south_projection_pass
            and east_projection_pass
            and west_projection_pass
        )


def part1():
    tiles = []
    with IN_FILE.open("r") as f:
        for entry in f:
            match = re.match(r"(\d+),(\d+)", entry)
            assert match
            tiles.append(Point(int(match.group(1)), int(match.group(2))))

    max_area = max(map(compute_area, combinations(tiles, 2)))
    print(f"Part 1 max area: {max_area}")


def part2():
    apolygon = AmorphousPolygon()
    tiles = []
    with IN_FILE.open("r") as f:
        for entry in f:
            match = re.match(r"(\d+),(\d+)", entry)
            assert match
            tiles.append(Point(int(match.group(1)), int(match.group(2))))

    for p1, p2 in zip(tiles, tiles[1:] + [tiles[0]]):
        apolygon.add_line(p1, p2)

    # Ensure that the `apolygon` was built correctly
    apolygon.postprocess()

    # Order the rectangles from larges to smallest
    rectangles = sorted(combinations(tiles, 2), key=compute_area, reverse=True)

    for i, rect in enumerate(rectangles):
        print("Processed ", i)

        for j, point in enumerate(trace_edges(rect)):
            if j and not (j % 10):
                print(f"Border {j}")
            if point not in apolygon:
                break
        else:
            print(f"Part 2 max area: {compute_area(rect)}")
            return

    # There should always be a solution
    assert False


if __name__ == "__main__":
    part1()

    part2()
