from __future__ import annotations

import re
from typing import Literal
from collections import defaultdict
from collections.abc import Iterator
from itertools import product
from pathlib import Path

from ortools.sat.python import cp_model

# IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")
IN_FILE = Path("./full_input2.txt")

PresentID = int
PresentData = tuple[tuple[bool, ...], ...]


class Present:
    def __init__(self, present_id: PresentID, present_str: str):
        self.present_id = present_id
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
        # Sanity check
        assert len(present_counts) == len(presents)
        
        self.width = width
        self.height = height

        # Convert the `present_counts` to a dictionary of present_id
        self.present_counts: dict[int, int] = dict(enumerate(present_counts))

        # Expand the `self.present_counts` to all presents in groups
        self.presents = [[presents[p_idx] for _ in range(p_count)]
                         for p_idx, p_count in self.present_counts.items()] 

        # For convenience, also flatten the list of list of presents
        self.flattened_presents = sum(self.presents, [])

    def _to_stable_ordering(self, row: int, col: int, rotation: Literal[0,1,2,3]) -> int:
        """Given the 3 parameters, produces a unique 1:1 mapping for stable ordering."""
        # There can be up to 4 rotations, so multiply by 4 to make space for them
        return 4 * (row * self.width + col) + rotation
        
    def is_satisfiable(self) -> bool:
        total_present_area = sum(present.size for present in self.flattened_presents)
        
        # Build the CP-SAT problem
        model = cp_model.CpModel()

        # Represents if a given cell is occupied or not
        sat_vars_grid_occupancy = [
            [
                model.NewBoolVar(f"occ_{x}_{y}") for x in range(self.width)
            ]
            for y in range(self.height)
        ]

        # Variables that will be constrained to require that every present to be placed
        sat_vars_presents = [[] for _ in self.flattened_presents]

        # Variables and their ord numbers that later will be used to enforce placement
        # ordering to prevent combinatorial explosion of identical solutions
        sat_vars_label_ords: list[list[tuple[int, cp_model.BoolVar]]] = [
            [] for _ in self.flattened_presents
        ]
        
        # Variables that will be constrained to require grid cells to have at most one occupant
        sat_vars_grid = [[[] for _ in range(self.width)] for _ in range(self.height)]

        for p_idx, present in enumerate(self.flattened_presents):
            # For every pivot position and every rotation. Stop 2 units from the right
            # and bottom edges of the grid to  prevent the shape from extending beyond
            # the grid's bounds
            for row, col in product(range(self.height - 2), range(self.width - 2)):
                for rotation, data in present.orientations_iter():
                    ord_id = self._to_stable_ordering(row, col, rotation)
                    var = model.NewBoolVar(f"p_{p_idx}_{row}_{col}_{rotation}_{ord_id}")
                    sat_vars_presents[p_idx].append(var)
                    sat_vars_label_ords[p_idx].append((ord_id, var))
                    
                    # Look where the current configuration is non-empty and add the `var`
                    # to the respective grid square's expression
                    for col_diff, row_diff in product(range(3), range(3)):
                        if data[row_diff][col_diff]:
                            # Some sanity checks
                            assert row + row_diff < self.height
                            assert col + col_diff < self.width
                            sat_vars_grid[row + row_diff][col + col_diff].append(var)

            # The present must be placed exactly once
            model.AddExactlyOne(sat_vars_presents[p_idx])

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
        model.AddAtLeastOne(sat_vars_grid_occupancy[row][0] for row in range(self.height))

        # Kill combinatorial symmetry from placing identical shapes by enforcing
        # a stable ordering for each present within a present type
        for present_class in self.presents:
            present_class_label_vars = []
            for p_idx, _ in enumerate(present_class):
                # Extract all ord values for the given `p_idx`
                ord_ids = [ord_id for ord_id, _ in sat_vars_label_ords[p_idx]]
                min_ord_id = min(ord_ids)
                max_ord_id = max(ord_ids)

                label_var = model.NewIntVar(min_ord_id, max_ord_id, f"l_{p_idx}")
                present_class_label_vars.append(label_var)

                # Enforce that the current `label_var` is equal to the ord it selected. This
                # constraint works since the `var` is a boolean and only one will be `True`
                model.Add(
                    label_var == sum(ord_id * var for ord_id, var in sat_vars_label_ords[p_idx])
                )

            # Enforce strict label ordering for all presents within a `present_class`
            for label_var1, label_var2 in zip(
                    present_class_label_vars, present_class_label_vars[1:], strict=False
            ):
                model.Add(label_var1 < label_var2)
        
        
        # Feasibility only (no objective)
        solver = cp_model.CpSolver()
        solver.parameters.stop_after_first_solution = True
        status = solver.Solve(model)

        # # Print the placements for debugging
        # if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        #     print('=' * 20)
            
        #     for p_idx, vars in enumerate(sat_exprs_presents):
        #         for var in vars:
        #             if solver.BooleanValue(var):
        #                 print(f"present #{var} placed")

        #     print('-' * 20)

        #     for row in range(self.height):
        #         for col in range(self.width):
        #             if solver.BooleanValue(sat_vars_grid_occupancy[row][col]):
        #                 print('#', end='')
        #             else:
        #                 print('.', end='')

        #         print()
        
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
    for tidx, tree in enumerate(trees):
        print(f"Starting {tidx} / {len(trees) - 1}")
        satisfiable = tree.is_satisfiable()
        n_satisfied += int(satisfiable)
        print(f"Finished {tidx} / {len(trees) - 1} :: {satisfiable}")

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")


if __name__ == "__main__":
    part1()
