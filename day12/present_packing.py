from __future__ import annotations

import re
import uuid
from collections import defaultdict
from collections.abc import Iterator
from itertools import product
from pathlib import Path

from ortools.sat.python import cp_model


IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")

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
        self.presents = presents

    def is_satisfiable(self) -> bool:
        # Build the CP-SAT problem
        model = cp_model.CpModel()

        x_intervals = []
        y_intervals = []
        for p_id, p_count in self.present_counts.items():
            present = self.presents[p_id]
            
            for i in range(p_count):
                # Anchor of the present to stay within the bounds of the grid. The range
                # is inclusive on both bounds
                x = model.NewIntVar(0, self.width - 3, f"p_{p_id}_{i}_x")
                y = model.NewIntVar(0, self.height - 3, f"p_{p_id}_{i}_y")

                # Force a rotation pick
                rotation_selector_vars = [
                    model.NewBoolVar(f"r_{p_id}_{i}_{rot}")
                    for rot, _ in present.orientations_iter()
                ]
                model.AddExactlyOne(rotation_selector_vars)

                # Each box in the present shape is its own variable
                _, data = next(present.orientations_iter())
                shape_vars = [
                    (
                        model.NewIntVar(0, self.width - 1, f"p_{p_id}_{i}_{dx}_dx"),
                        model.NewIntVar(0, self.height - 1, f"p_{p_id}_{i}_{dy}_dy")
                    )
                    for dx, dy in product(range(3), range(3))
                    if data[dy][dx]
                ]
                
                for rot, oriented_data in present.orientations_iter():
                    i = 0
                    for dx, dy in product(range(3), range(3)):
                        if oriented_data[dy][dx]:
                            # Get the next unused shape_var
                            dx_var, dy_var = shape_vars[i]
                            i += 1

                            # Require the present shape variable `dx_var/dy_var`
                            # to be properly set relative to the anchor `x/y`
                            # only for the given rotation, disregard otherwise
                            model.Add(dx_var == x + dx).OnlyEnforceIf(
                                rotation_selector_vars[rot]
                            )
                            model.Add(dy_var == y + dy).OnlyEnforceIf(
                                rotation_selector_vars[rot]
                            )

                # Create intervals from the `shape_vars`
                for dx_var, dy_var in shape_vars:
                    x_intervals.append(
                        model.NewIntervalVar(dx_var, 1, dx_var + 1, f"i{dx_var.Name()}")
                    )
                    y_intervals.append(
                        model.NewIntervalVar(dy_var, 1, dy_var + 1, f"i{dy_var.Name()}")
                    )

        model.AddNoOverlap2D(x_intervals, y_intervals)
            
        # Feasibility only (no objective)
        solver = cp_model.CpSolver()
        solver.parameters.stop_after_first_solution = True
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
    for tidx, tree in enumerate(trees):
        print(f"Starting {tidx} / {len(trees) - 1}")
        satisfiable = tree.is_satisfiable()
        n_satisfied += int(satisfiable)
        print(f"Finished {tidx} / {len(trees) - 1} :: {satisfiable}")

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")


if __name__ == "__main__":
    part1()
