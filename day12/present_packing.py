from __future__ import annotations

import re
import uuid
from collections import defaultdict
from collections.abc import Iterator
from itertools import product
from pathlib import Path

import pulp as pl

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")

PresentID = int
PresentData = tuple[tuple[bool, ...], ...]


class Present:
    def __init__(
        self,
        present_id: PresentID,
        present_str: str,
    ):
        self.id = present_id

        # Sanitize the `present_str` a bit
        present_str = present_str.replace("\n", "")
        assert len(present_str) == 9

        # Convert the the `present_str` in to a 2D boolean array
        data_ls = [[False] * 3 for _ in range(3)]
        for i, c in enumerate(present_str):
            if c == "#":
                row = i // 3
                col = i % 3
                data_ls[row][col] = True

        # Make `data_ls` in to a hashable structure
        data = tuple(tuple(v for v in row) for row in data_ls)
        data_rot1 = self._rotate_data(data)
        data_rot2 = self._rotate_data(data_rot1)
        data_rot3 = self._rotate_data(data_rot2)

        # Store all unique rotations. This removes any rotational symmetry in the shape
        self.data_rotations = {data, data_rot1, data_rot2, data_rot3}

    @staticmethod
    def _rotate_data(data: PresentData) -> PresentData:
        """Rotates the `data` clockwise."""
        data_ls = [[False] * 3 for _ in range(3)]

        # Procedure to rotated a 3x3 matrix clockwise
        for i in range(3):
            for j in range(3):
                data_ls[i][j] = data[2 - j][i]

        # Convert to type `PresentData`
        return tuple(tuple(v for v in row) for row in data_ls)

    def orientations_iter(self) -> Iterator[tuple[int, PresentData]]:
        yield from enumerate(self.data_rotations)


class ChristmasTree:
    def __init__(
        self,
        width: int,
        height: int,
        present_counts: list[int],
        presents: list[Present],
    ):
        self.width = width
        self.height = height

        # Convert the `present_counts` to a dictionary of present_id
        self.present_counts = dict(enumerate(present_counts))
        self.presents = [
            presents[p_id] for p_id, count in self.present_counts.items() for _ in range(count)
        ]

    def is_satisfiable(self) -> bool:
        # Build the optimization problem
        prob = pl.LpProblem("demo", pl.LpMaximize)

        lp_vars_by_present = defaultdict(
            lambda: defaultdict(
                lambda: pl.LpVariable(
                    f"p_{uuid.uuid4().hex}",
                    lowBound=0,
                    upBound=1,
                    cat="Integer",
                )
            )
        )
        lp_exprs_presents = [
            pl.LpAffineExpression(name=f"ep_{i}") for i in range(len(self.presents))
        ]
        lp_exprs_grid = [
            [pl.LpAffineExpression(name=f"eg_{row}_{col}") for col in range(self.width)]
            for row in range(self.height)
        ]

        for pidx, present in enumerate(self.presents):
            # For every pivot position and every rotation. Stop 2 units from the right
            # and bottom edges of the grid to  prevent the shape from extending beyond
            # the grid's bounds
            for row, col in product(range(self.height - 2), range(self.width - 2)):
                for rotation, data in present.orientations_iter():
                    key = (row, col, rotation)
                    var = lp_vars_by_present[pidx][key]

                    # Look where the current configuration is non-empty and add the `var`
                    # to the respective grid square's expression
                    for col_diff, row_diff in product(range(3), range(3)):
                        if data[row_diff][col_diff]:
                            # Some sanity checks
                            assert row + row_diff < self.height
                            assert col + col_diff < self.width
                            lp_exprs_grid[row + row_diff][col + col_diff] += var

            # When done processing this present and its rotations, add of this present's
            # variables in to one large present expression
            for var in lp_vars_by_present[pidx].values():
                lp_exprs_presents[pidx] += var

            # The present variables have to sum up to exactly 1, meaning that
            # for this present, only one position and one rotation will be selected
            prob += lp_exprs_presents[pidx] == 1

        # When all presents have been processed, the grid expressions all have to be <= 1.
        # This indicates that each square in the grid may have at most one present (or be empty)
        for row, col in product(range(self.height), range(self.width)):
            prob += lp_exprs_grid[row][col] <= 1

        # Finally the optimization is to maximize the present variables sum
        prob += sum(
            var for present_vars in lp_vars_by_present.values() for var in present_vars.values()
        )

        # Solve the problem
        status_code = prob.solve(pl.PULP_CBC_CMD(msg=False))
        return status_code == pl.LpStatusOptimal


def part1():
    file_contents = IN_FILE.read_text()

    # Matches:
    # number + ":" + "\n"
    # any number of ".", "#", and "\n" excluding "\n\n"
    present_pattern = re.compile(r"(\d+):\n((?:[.#]|\n(?!\n))+)")

    presents = []
    for present_match in present_pattern.finditer(file_contents):
        present_id = int(present_match.group(1))
        present_str = present_match.group(2)

        presents.append(Present(present_id, present_str))

    christmas_tree_match = re.compile(r"(\d+)x(\d+): ((?:\d+\s+)+)")

    trees = []
    for tree_match in christmas_tree_match.finditer(file_contents[present_match.end() :]):
        width = int(tree_match.group(1))
        height = int(tree_match.group(2))
        present_counts = [int(c) for c in tree_match.group(3).split()]

        trees.append(ChristmasTree(width, height, present_counts, presents))

    n_satisfied = 0
    for tidx, tree in enumerate(trees):
        print(f"Starting {tidx}")
        satisfiable = tree.is_satisfiable()
        n_satisfied += int(satisfiable)
        print(f"Finished {tidx} {satisfiable}")

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")


if __name__ == "__main__":
    part1()
