from __future__ import annotations
from typing import Iterator, Any

import re
from pathlib import Path
from copy import deepcopy

from sortedcontainers import SortedSet

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")


class ColumnHeader:
    def __init__(self, *, column_id: int | None = None):
        self.id = column_id
        
        self.n_elems = 0
        
        self.head_elem = None
        self.tail_elem = None
        

    def add_elem2d(self, elem: Elem2D):
        self.n_elems += 1
        
        # If this is the first `elem`, mark it also as both the `head_elem` and `tail_elem`
        if self.head_elem is None:
            self.head_elem = elem

            assert self.tail_elem is None
            self.tail_elem = elem
        else:
            assert self.tail_elem is not None
            
            # Link the `elem` to the `tail_elem` vertically
            self.tail_elem.down = elem
            elem.up = self.tail_elem

            # Move the `self.tail_elem` down and make sure it links circularly
            self.tail_elem = elem
            self.tail_elem.down = self.head_elem
            self.head_elem.up = self.tail_elem

        # Set ourselves as the column of the `elem`
        elem.set_column(self)

class RowHeader():
    def __init__(self):
        self.head_elem = None
        self.tail_elem = None

    def add_elem2d(self, elem: Elem2D):
        # If this is the first `elem`, mark it also as both the `head_elem` and `tail_elem`
        if self.head_elem is None:
            self.head_elem = elem

            assert self.tail_elem is None
            self.tail_elem = elem
        else:
            assert self.tail_elem is not None
            
            # Link the `elem` to the `tail_elem` horizontally
            self.tail_elem.right = elem
            elem.left = self.tail_elem            

        # Set ourselves as the row of the `elem`
        elem.set_row(self)
        
        
class Elem2D:
    def __init__(self, *, payload: Any | None = None):
        self.payload = payload
        
        # Initialize to a fully self-referential element
        self.up = self
        self.down = self
        self.left = self
        self.right = self

        # The column and row will be set when we are added to the respective structures later
        self.column = None
        self.row = None

    def set_column(self, column: ColumnHeader):
        self.column = column

    def set_row(self, row: RowHeader):
        self.row = row

    def horizontal_iter(self) -> Iterator[Elem2D]:
        start = self
        cur = start
        yield cur

        cur = cur.right
        while cur is not start:
            yield cur
            cur = cur.right

    def vertical_iter(self) -> Iterator[Elem2D]:
        start = self
        cur = start
        yield cur

        cur = cur.down
        while cur is not start:
            yield cur
            cur = cur.down

    def unlink(self):
        assert self.column
        
        # Check to see if we should move the head element of `self.column`
        if self.column.head_elem is self:
            # If we are the last element of this circular list
            if self.down is self:
                self.column.head_elem = None
            else:
                self.column.head_elem = self.down

        # Decrement the column element counter
        self.column.n_elems -= 1

        # Remove ourselves from the 2D list structure
        self.up.down = self.down
        self.down.up = self.up

        self.left.right = self.right
        self.right.left = self.left

    def relink(self):
        assert self.column
        
        if self.column.head_elem is None:
            self.column.head_elem = self

        # Increment the column element counter
        self.column.n_elems += 1

        # Re-add ourselves to the 2D list structure
        self.up.down = self
        self.down.up = self

        self.left.right = self
        self.right.left = self

class Present:
    def __init__(self, present_id: int, data: list[list[int]], *, rotation: int = 0):
        self.id = present_id
        self.data = data
        self.rotation = rotation

    @classmethod
    def from_str(cls, present_id: int, present_str: str):
        # Presents are always 3x3. Remove all "\n" from the `present_str`
        # and assert the proper length
        present_str = present_str.replace("\n", "")
        assert len(present_str) == 9

        data = [[0] * 3 for _ in range(3)]
        for i, c in enumerate(present_str):
            row = i // 3
            col = i % 3

            if c == '#':
                data[row][col] = 1

        return cls(present_id, data)
                
    def orientations_iter(self) -> Iterator[Present]:
        # First yield ourself before rotating
        yield self
        
        # Rotate and yield 3 times
        rotated_data = deepcopy(self.data)
        for rot in range(1, 4):
            new_rotated_data = [[0] * 3 for _ in range(3)]

            # Procedure to rotated a 3x3 matrix
            for i in range(3):
                for j in range(3):
                    new_rotated_data[i][j] = rotated_data[2 - j][i]

            yield Present(self.id, new_rotated_data, rotation=rot)

            rotated_data = deepcopy(new_rotated_data)

class ChristmasTree:
    def __init__(self, width: int, height: int, present_counts: list[int]):
        self.width = width
        self.height = height

        # Convert the `present_counts` to a dictionary of present_id
        self.present_counts = dict(enumerate(present_counts))

class PackingSolutionSpace:
    def __init__(self, tree: ChristmasTree, presents: list[Present]):
        self.tree = tree

        # Multiply the `presents` by the respective `self.tree.present_counts`
        self.presents = [presents[p_id] for p_id, count in self.tree.present_counts.items()
                         for _ in range(count)]

        self.solution_steps = []
        self.backtracking_stack = []        

        # Every space under the `self.tree` is a soft dependency among presents
        dependencies = [ColumnHeader(column_id=i)
                        for i in range(self.tree.width * self.tree.height)]
        
        # Every present is a column header and a hard constraint that must be satisfied
        constraints = [ColumnHeader(column_id=(self.tree.width * self.tree.height + i))
                       for i in range(len(self.presents))]

        # Form all columns in an enforced sorted order
        self.columns = SortedSet(dependencies + constraints, key=lambda c: c.id)

        # There a 4 * len(self.presents) rows (one for each orientation)
        self.rows = [RowHeader() for _ in range(4 * len(self.presents))]

        # For each present orientation, set its rows
        for pi, present in enumerate(self.presents):
            for opi, oriented_present in enumerate(present.orientations_iter()):
                # Get the `row` for this `oriented_present`
                row = self.rows[4 * pi + opi]
                
                # The top left corner of the present space is meant to determine its location
                # Since the presents are always 3x3, there is a 2 unit space margin along the
                # right and bottom edge of the tree space that the shape can never occupy
                for i in range(self.tree.width - 2):
                    for j in range(self.tree.height - 2):
                        # Iterate the 3x3 of each present
                        for col_diff in range(3):
                            for row_diff in range(3):
                                # If the location `(row_diff, col_diff)` is not empty space
                                if oriented_present.data[row_diff][col_diff]:
                                    cur_col = dependencies[
                                        (i + row_diff) * self.tree.height +
                                        (j + col_diff)
                                    ]
                                    elem = Elem2D(
                                        payload={
                                            "present_id": present.id,
                                            "rotation": oriented_present.rotation
                                        }
                                    )
                                    cur_col.add_elem2d(elem)
                                    row.add_elem2d(elem)

                # Importantly mark ourselves in the constraint corresponding to our present ID
                constr_col = constraints[pi]
                elem = Elem2D(
                    payload={
                        "present_id": present.id,
                        "rotation": oriented_present.rotation
                    }
                )
                constr_col.add_elem2d(elem)
                row.add_elem2d(elem)

        # Every constraint column corresponds to a box.
        # Assert that all 4 rotations are encapsulated
        assert all(c.n_elems == 4 for c in constraints)
                
    def add_solution_step(self, elem: Elem2D):
        self.solution_steps.append(elem)

        satisfied_columns = []
        for elem in elem.horizontal_iter():
            assert elem.column
            satisfied_columns.append(elem.column)

        # Sanity check the invariant that all elements in a row have different columns
        assert len(satisfied_columns) == len(set(satisfied_columns))
        
        # Then remove all elements in all of these columns, marking
        # them in the `self.backtracking_stack` in order of removal
        elements_to_remove = set()
        for column in satisfied_columns:
            assert column.head_elem is not None

            # For all rows in this column
            for col_elem in column.head_elem.vertical_iter():
                # Mark all elements in this row for removal
                for row_elem in col_elem.horizontal_iter():
                    elements_to_remove.add(row_elem)

            # Remove this satisfied `column` from the `self.columns`
            self.columns.remove(column)

        # Convert `elements_to_remove` to a list for stable ordering
        elements_to_remove_ls = list(elements_to_remove)

        # Remove all of the elements
        for elem in elements_to_remove_ls:
            elem.unlink()

        # Record all of the elements to remove as one unit in the `self.backtracking_stack`
        # But reversed to reflect the most recently removed is first
        self.backtracking_stack.append(elements_to_remove_ls[::-1])

    def pop_solution_step(self):
        self.solution_steps.pop()

        # Relink the elements in order of most recent unlinking
        elements_to_add = self.backtracking_stack.pop()
        for elem in elements_to_add:
            elem.relink()
            self.columns.add(elem.column)

    @property
    def constraints(self) -> list[ColumnHeader]:
        # Find where the constraints start in the `self.columns` by bisecting left
        # The first constraint column has index `self.tree.width * self.tree.height`
        idx = self.columns.bisect_key_left(self.tree.width * self.tree.height)
        return self.columns[idx:]
            
    @property
    def is_valid(self) -> bool:
        return all(c.n_elems > 0 for c in self.constraints)

    @property
    def is_solved(self) -> bool:
        # No more constraints left to solve
        return not self.constraints
            
    def solve(self) -> bool:
        # Seed the stack with the first column to try
        candidate_column_stack = [min(self.constraints, key=lambda c: c.n_elems)]
        tried_elems = set()
        while candidate_column_stack:
            candidate_column = candidate_column_stack[-1]

            # An invalid `candidate_column` would never be put on the stack
            # since it is wrapped by an `is_valid` check
            assert candidate_column.head_elem

            local_tried_elems = set()
            for candidate_elem in candidate_column.head_elem.vertical_iter():
                local_tried_elems.add(candidate_elem)

                # Skip this `candidate_elem` if we tried it already in a previous search attempt
                if candidate_elem in tried_elems:
                    continue

                tried_elems.add(candidate_elem)

                self.add_solution_step(candidate_elem)

                # A solution was found, return it!
                if self.is_solved:
                    breakpoint()
                    return True

                # Try the next column if this is a valid step
                if self.is_valid:
                    candidate_column_stack.append(
                        min(self.columns, key=lambda c: c.n_elems)
                    )
                    break

                # If this brings the solution space to an invalid state, undo this step
                self.pop_solution_step()
            else:
                # All elements of the `candidate_column` were invalid
                # since the `break` was never hit, backtrack one level up
                tried_elems -= local_tried_elems
                candidate_column_stack.pop()
                self.pop_solution_step()

        # No solution found after exhausting the `candidate_column_stack`
        return False
            
def part1():
    file_contents = IN_FILE.read_text()

    # Matches:
    # number + ":" + "\n"
    # any number of ".", "#", and "\n" excluding "\n\n"
    present_pattern = re.compile(r'(\d+):\n((?:[.#]|\n(?!\n))+)')

    presents = []
    for present_match in present_pattern.finditer(file_contents):
        present_id = int(present_match.group(1))
        present_str = present_match.group(2)

        presents.append(Present.from_str(present_id, present_str))
        
    christmas_tree_match = re.compile(r'(\d+)x(\d+): ((?:\d+\s+)+)')

    trees = []
    for tree_match in christmas_tree_match.finditer(file_contents[present_match.end():]):
        width = int(tree_match.group(1))
        height = int(tree_match.group(2))
        present_counts = [int(c) for c in tree_match.group(3).split()]

        trees.append(ChristmasTree(width, height, present_counts))

    n_satisfied = 0
    for tree in trees:
        packing_solution_space = PackingSolutionSpace(tree, presents)
        n_satisfied += int(packing_solution_space.solve())

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")

if __name__ == "__main__":
    part1()
