from __future__ import annotations
from typing import Iterator, Literal

import re
from pathlib import Path

import bitarray as ba

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")

class FrozenBitMap2D:
    def __init__(
        self,
        width: int,
        height: int,
        *,
        data: ba.frozenbitarry
    ):
        self.w = width
        self.h = height

        # Sanity check
        assert len(data) == self.w * self.h
        self.data = data

        self.used_space = self.data.count()
        self._or_mask = None

    @classmethod
    def fromBitMap2D(cls, o: BitMap2D) -> FrozenBitMap2D:
        return cls(o.w, o.h, data=ba.frozenbitarry(o.data))

    def toBitMap2D(self) -> BitMap2D:
        return BitMap2D(self.w, self.h, data=ba.bitarray(self.data))
        
    def set_or_mask(self, full_width: int):
        or_mask = ba.zeros(full_width * self.h)

        for i in range(self.h):
            src_offset = self.w * i
            dest_offset = full_width * i
            or_mask[dest_offset : dest_offset + self.w] |= self.data[src_offset : src_offset + self.w]

        self._or_mask = ba.frozenbitarry(or_mask)        

class BitMap2D:
    def __init__(
        self,
        width: int,
        height: int,
        *,
        data: ba.bitarray | None = None
    ):
        self.w = width
        self.h = height

        if data:
            # Sanity check
            assert len(data) == self.w * self.h
            self.data = data
        else:
            self.data = ba.zeros(self.w * self.h)

    def nonconflicting_or_at(self, other: FrozenBitMap2D, x: int, y: int) -> bool:
        """Applies the `other` in an XOR with the top left corner at (x, y).

        If there is a conflict (self had a 1 and other also has a 1 in the same place),
        then returns `False` with no side-effects. Otherwise, apply in-place."""
        # Sanity check that we are in bounds and have an `_or_mask`
        assert not (x < 0 or y < 0 or x + other.w > self.w or y + other.h > self.h)
        assert other._or_mask

        offset = (y * self.w) + x
        before_count = self.data[offset : offset + len(other._or_mask)].count()
        result = self.data[offset : offset + len(other._or_mask)] | other._or_mask
        after_count = result.count()

        # If the `other._or_mask` did not add `other.used_space` bits exactly,
        # then there was a conflict
        if before_count + other.used_space != after_count:
            return False

        self.data[offset : offset + len(other._or_mask)] = result
        return True
        
    def copy(self) -> BitMap2D:
        # Force `self.data` to a mutable bitarray on `copy`
        data_cp = ba.bitarray(self.data)
        return BitMap2D(self.w, self.h, data=data_cp)
        
    def __getitem__(self, xy: tuple[int, int]):
        x, y = xy
        return self.data[y * self.w + x]

    def __setitem__(self, xy: tuple[int, int], v: Literal[0, 1]):
        x, y = xy
        self.data[y * self.w + x] = v

class Present:
    def __init__(self, present_id: int, area: FrozenBitMap2D, *, rotation: int = 0):
        self.id = present_id
        self.rotation = rotation
        
        self.area = area

        # Compute the other three rotations of this shape if it is not rotated
        self._rotations = self._compute_rotations()

    @classmethod
    def from_str(cls, present_id: int, present_str: str):
        # Presents are always 3x3. Remove all "\n" from the `present_str`
        # and assert the proper length
        present_str = present_str.replace("\n", "")
        assert len(present_str) == 9

        data = BitMap2D(3, 3)
        for i, c in enumerate(present_str):
            row = i // 3
            col = i % 3

            if c == '#':
                data[row, col] = 1

        return cls(present_id, FrozenBitMap2D.fromBitMap2D(data))
                
    def _compute_rotations(self) -> list[Present] | None:
        # Only applies to the original un-rotated shape
        if not self.rotation:
            return None

        ret = []
        
        # First add ourselves
        ret.append(self)
        
        # Rotate and yield 3 times
        rotated_data = self.area.toBitMap2D()
        for rot in range(1, 4):
            new_rotated_data = BitMap2D(3, 3)

            # Procedure to rotated a 3x3 matrix
            for i in range(3):
                for j in range(3):
                    new_rotated_data[i, j] = rotated_data[(2 - j), i]

            # Add the newly appended present
            assert rot
            ret.append(
                Present(self.id, FrozenBitMap2D.fromBitMap2D(new_rotated_data), rotation=rot)
            )

            rotated_data = new_rotated_data.copy()
        
        return ret

    def orientations_iter(self) -> Iterator[Present]:
        assert self._rotations is not None
        yield from self._rotations

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
        self.area = BitMap2D(self.width, self.height)

        # Convert the `present_counts` to a dictionary of present_id
        self.present_counts = dict(enumerate(present_counts))

        self.presents = [presents[p_id] for p_id, count in self.present_counts.items()
                         for _ in range(count)]

    def apply_present(self, present: Present) -> bool:
        # First check if `present` conflicts with any used space
        pass
        


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
