import bisect
import random
import re
from collections import namedtuple
from collections.abc import Iterator
from functools import lru_cache
from itertools import combinations
from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")

random.seed(42)

Point = namedtuple("Point", ["x", "y"])
type Edge = tuple[Point, Point]


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
        self,
        point: Point,
    ) -> tuple[Edge | None, Edge | None, Edge | None, Edge | None]:
        x_indexl = bisect.bisect_left(self.vedges, point.x, key=lambda edge: edge[0].x)
        x_indexr = bisect.bisect_right(self.vedges, point.x, key=lambda edge: edge[0].x)

        y_indexr = bisect.bisect_right(self.hedges, point.y, key=lambda edge: edge[0].y)
        y_indexl = bisect.bisect_left(self.hedges, point.y, key=lambda edge: edge[0].y)

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

    def _point_projected_on_hedge(self, point: Point, hedge: Edge, *, offset: int) -> Point:
        return Point(point.x, hedge[0].y + offset)

    def _point_projected_on_vedge(self, point: Point, vedge: Edge, *, offset: int) -> Point:
        return Point(vedge[0].x + offset, point.y)

    def __contains__(self, point: Point) -> bool:
        # First check if point is on the polygon's border
        x_indexl = bisect.bisect_left(self.vedges, point.x, key=lambda edge: edge[0].x)
        x_indexr = bisect.bisect_right(self.vedges, point.x, key=lambda edge: edge[0].x)

        y_indexr = bisect.bisect_right(self.hedges, point.y, key=lambda edge: edge[0].y)
        y_indexl = bisect.bisect_left(self.hedges, point.y, key=lambda edge: edge[0].y)
        if any(
            edge for edge in self.hedges[y_indexl:y_indexr] if edge[0].x <= point.x <= edge[1].x
        ):
            return True
        if any(
            edge for edge in self.vedges[x_indexl:x_indexr] if edge[0].y <= point.y <= edge[1].y
        ):
            return True

        seen = set()
        to_process = [point]

        while to_process:
            p = to_process.pop()
            edges = self._projection_intersects(p)
            if not all(edges):
                return False

            north_edge, south_edge, east_edge, west_edge = edges
            assert north_edge
            assert south_edge
            assert east_edge
            assert west_edge

            npoint = self._point_projected_on_hedge(p, north_edge, offset=1)
            spoint = self._point_projected_on_hedge(p, south_edge, offset=-1)
            epoint = self._point_projected_on_vedge(p, east_edge, offset=-1)
            wpoint = self._point_projected_on_vedge(p, west_edge, offset=1)

            if npoint not in seen:
                to_process.append(npoint)
            if spoint not in seen:
                to_process.append(spoint)
            if epoint not in seen:
                to_process.append(epoint)
            if wpoint not in seen:
                to_process.append(wpoint)

            seen |= {npoint, spoint, epoint, wpoint}

        # All of the bouncing terminated without exiting the polygon, we must be inside it
        return True


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

    for p1, p2 in zip(tiles, tiles[1:] + [tiles[0]], strict=True):
        apolygon.add_line(p1, p2)

    # Ensure that the `apolygon` was built correctly
    apolygon.postprocess()

    # Order the rectangles from larges to smallest
    rectangles = sorted(combinations(tiles, 2), key=compute_area, reverse=True)

    for i, rect in enumerate(rectangles):
        print(f"Processed {i} / {len(rectangles)}")

        for j, point in enumerate(trace_edges(rect)):
            if j and not (j % 100):
                print(
                    f"Border {j} / {2 * abs(rect[0].x - rect[1].x) + 2 * abs(rect[0].y - rect[1].y)}"
                )
            if point not in apolygon:
                break
        else:
            print(f"Part 2 max area: {compute_area(rect)}")
            return

    # There should always be a solution
    raise AssertionError()


if __name__ == "__main__":
    part1()

    part2()
