from __future__ import annotations

import re
from tqdm import tqdm
import uuid
from collections import defaultdict
from collections.abc import Iterator
from itertools import product
from pathlib import Path

from ortools.sat.python import cp_model

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
        self.size = 0

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
                self.size += 1

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
        self.presents = presents

    def is_satisfiable(self) -> bool:
        total_present_area = sum(p_count * self.presents[p_id].size
                                 for p_id, p_count in self.present_counts.items())
        
        # Build the CP-SAT problem
        model = cp_model.CpModel()

        # Represents the spaces that are occupied by a present anchored at all possible positions
        sat_vars_by_present = defaultdict(
            lambda: defaultdict(
                lambda: model.NewBoolVar(f"p_{uuid.uuid4().hex}")
            )
        )

        sat_vars_grid_occupancy = [
            [
                model.NewBoolVar(f"occ_{x}_{y}") for x in range(self.width)
            ]
            for y in range(self.height)
        ]

        # Variables used to require the exact amount of present counts
        sat_vars_presents = [
            [] for _ in self.present_counts
        ]

        # Variables used to require grid elements to have at most one occupant
        sat_vars_grid = [[[] for _ in range(self.width)] for _ in range(self.height)]
        
        for p_id, p_count in self.present_counts.items():
            # Skip if there is no `p_count`
            if not p_count:
                continue
            
            present = self.presents[p_id]

            # For every pivot position and every rotation. Stop 2 units from the right
            # and bottom edges of the grid to  prevent the shape from extending beyond
            # the grid's bounds
            for row, col in product(range(self.height - 2), range(self.width - 2)):
                for rotation, data in present.orientations_iter():
                    key = (row, col, rotation)
                    var = sat_vars_by_present[p_id][key]

                    # Look where the current configuration is non-empty and add the `var`
                    # to the respective grid square's expression
                    for col_diff, row_diff in product(range(3), range(3)):
                        if data[row_diff][col_diff]:
                            # Some sanity checks
                            assert row + row_diff < self.height
                            assert col + col_diff < self.width
                            sat_vars_grid[row + row_diff][col + col_diff].append(var)

            # When done processing this present and its rotations, add of this present's
            # variables in to one large present expression
            for var in sat_vars_by_present[p_id].values():
                sat_vars_presents[p_id].append(var)

            # The present variables have to sum up to exactly `p_count`, meaning that
            # for this present exactly `p_count` of it must be selected
            model.Add(sum(sat_vars_presents[p_id]) == p_count)

        # Go through the grid and build the occupancy dependency on all of the present variables
        # This enforces no overlaps since occupancy is a boolean `{0, 1}`. And conversely
        # the occupancy is `True` if there is a var set for `row` and `col`
        for row, col in product(range(self.height), range(self.width)):
            model.Add(sum(sat_vars_grid[row][col]) == sat_vars_grid_occupancy[row][col])
            
        # The occupied cells must equal the `total_present_area` to ensure no overlapping
        model.Add(
            sum(sat_vars_grid_occupancy[row][col]
                for row, col in product(range(self.height), range(self.width)))
            == total_present_area
        )

        # Additionally kill any translational symmetry by requiring that the solved
        # shape touch both the top-most row and leftmost column
        model.AddAtLeastOne(sat_vars_grid_occupancy[0])
        model.AddAtLeastOne([sat_vars_grid_occupancy[row][0] for row in range(self.height)])

        # Add weak constraints that narrow down reflective symmetry by requiring the first row
        # to be left-heavy and the first column to be top-heavy.
        model.Add(
            sum(sat_vars_grid_occupancy[0][col] for col in range(self.width // 2))
            >=
            sum(sat_vars_grid_occupancy[0][col]
                for col in range(self.width - 1, self.width // 2, -1))
        )

        model.Add(
            sum(sat_vars_grid_occupancy[row][0] for row in range(self.height // 2))
            >=
            sum(sat_vars_grid_occupancy[row][0]
                for row in range(self.height - 1, self.height // 2, -1))
        )
                
        # Feasibility only (no objective)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        return status in (cp_model.FEASIBLE, cp_model.OPTIMAL)


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
    for tree in tqdm(trees, desc="Working"):
        n_satisfied += int(tree.is_satisfiable())

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")


if __name__ == "__main__":
    part1()
