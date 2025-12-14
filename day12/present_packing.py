from __future__ import annotations
from typing import Iterator, Literal

import re
from pathlib import Path
from collections import deque
from itertools import repeat

import bitarray as ba

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")

class FrozenBitMap2D:
    def __init__(
        self,
        width: int,
        height: int,
        *,
        data: ba.frozenbitarray | None = None
    ):
        self.w = width
        self.h = height

        if data:
            # Sanity check
            assert len(data) == self.w * self.h
            self.data = data
        else:
            self.data = ba.frozenbitarray(self.w * self.h)

        self.used_space = self.data.count()
        self._or_mask = None

    @classmethod
    def fromBitMap2D(cls, o: BitMap2D) -> FrozenBitMap2D:
        return cls(o.w, o.h, data=ba.frozenbitarray(o.data))

    def toBitMap2D(self) -> BitMap2D:
        return BitMap2D(self.w, self.h, data=ba.bitarray(self.data))
        
    def set_or_mask(self, full_width: int):
        # The first `h - 1` rows get the `full_width`. The last row is just our width
        or_mask = ba.bitarray(full_width * (self.h - 1) + self.w)

        for i in range(self.h):
            src_offset = self.w * i
            dest_offset = full_width * i
            or_mask[dest_offset : dest_offset + self.w] |= self.data[src_offset : src_offset + self.w]

        self._or_mask = ba.frozenbitarray(or_mask)

    def nonconflicting_or_at(
        self,
        other: FrozenBitMap2D,
        xy: tuple[int, int],
    ) -> FrozenBitMap2D | None:
        """Applies the `other` in an XOR with the top left corner at (x, y).

        If there is a conflict (self had a 1 and other also has a 1 in the same place),
        then returns `None`. Otherwise returns the resulting OR'd `FrozenBitMap2D`."""
        x, y = xy
        
        # Sanity check that we are in bounds and have an `_or_mask`
        assert not (x < 0 or y < 0 or x > self.w or y > self.h)
        assert other._or_mask

        # If the `other` extends beyond the bounds, call this conflicting
        if x + other.w > self.w or y + other.h > self.h:
            return None
        
        offset = (y * self.w) + x
        before_count = self.data[offset : offset + len(other._or_mask)].count()
        result = self.data[offset : offset + len(other._or_mask)] | other._or_mask
        after_count = result.count()

        # If the `other._or_mask` did not add `other.used_space` bits exactly,
        # then there was a conflict
        if before_count + other.used_space != after_count:
            return None

        mutable_data = ba.bitarray(self.data)
        mutable_data[offset : offset + len(other._or_mask)] = result
        return FrozenBitMap2D(self.w, self.h, data=ba.frozenbitarray(mutable_data))
        
    def pprint(self, on="#", off=".") -> str:
        rows = []
        for y in range(self.h):
            start = y * self.w
            end = start + self.w
            row = self.data[start:end]
            rows.append("".join(on if bit else off for bit in row))
        return "\n".join(rows)

    @property
    def inactive_indices(self) -> Iterator[tuple[int, int]]:
        """Yields all indices that are 0s."""
        indices_1d = self.data.search(ba.bitarray([0]))

        for i_1d in indices_1d:
            yield (i_1d % self.w, i_1d // self.w)
    
    def __eq__(self, other: FrozenBitMap2D, /) -> bool:
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)
    
    def __str__(self) -> str:
        return self.pprint()    

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
            self.data = ba.bitarray(self.w * self.h)

    def copy(self) -> BitMap2D:
        # Force `self.data` to a mutable bitarray on `copy`
        data_cp = ba.bitarray(self.data)
        return BitMap2D(self.w, self.h, data=data_cp)

    def pprint(self, on="#", off=".") -> str:
        rows = []
        for y in range(self.h):
            start = y * self.w
            end = start + self.w
            row = self.data[start:end]
            rows.append("".join(on if bit else off for bit in row))
        return "\n".join(rows)
        
    def __getitem__(self, xy: tuple[int, int]):
        x, y = xy
        return self.data[y * self.w + x]

    def __setitem__(self, xy: tuple[int, int], v: Literal[0, 1]):
        x, y = xy
        self.data[y * self.w + x] = v

    def __str__(self) -> str:
        return self.pprint()
            

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
                data[col, row] = 1

        return cls(present_id, FrozenBitMap2D.fromBitMap2D(data))

    def set_or_mask(self, full_width: int):
        # Set the `or_mask` for all rotations
        for oriented_present in self.orientations_iter:
            oriented_present.area.set_or_mask(full_width)
    
    def _compute_rotations(self) -> list[Present] | None:
        # Only applies to the original un-rotated shape
        if self.rotation:
            return None

        ret = []
        rotated_areas = set()
        
        # First add ourselves
        ret.append(self)
        rotated_areas.add(self.area)
        
        # Rotate and yield 3 times
        rotated_area = self.area.toBitMap2D()
        for rot in range(1, 4):
            new_rotated_area = BitMap2D(3, 3)

            # Procedure to rotated a 3x3 matrix
            for i in range(3):
                for j in range(3):
                    new_rotated_area[i, j] = rotated_area[(2 - j), i]

            # Add the newly appended present
            assert rot
            new_area = FrozenBitMap2D.fromBitMap2D(new_rotated_area)

            # No point in testing oriented presents that are rotationally symmetrical
            if new_area not in rotated_areas:
                ret.append(Present(self.id, new_area, rotation=rot))
                rotated_areas.add(new_area)

            rotated_area = new_rotated_area.copy()
        
        return ret

    @property
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

        # Convert the `present_counts` to a dictionary of present_id
        self.present_counts = dict(enumerate(present_counts))

        # Set the OR mask for the `presents`
        for p in presents:
            p.set_or_mask(self.width)
        
        self.presents = [presents[p_id] for p_id, count in self.present_counts.items()
                         for _ in range(count)]

    @staticmethod
    def apply_present(
        area: FrozenBitMap2D,
        present: Present,
        *,
        seen: set[FrozenBitMap2D],
    ) -> list[FrozenBitMap2D]:
        ret = []
        
        for xy in area.inactive_indices:
            for oriented_present in present.orientations_iter:
                new_area = area.nonconflicting_or_at(oriented_present.area, xy)

                # If there is a valid `new_area` that we have not seen yet
                if new_area is not None and new_area not in seen:
                    ret.append(new_area)
                    seen.add(new_area)
                    
        return ret
        
    def is_satisfiable(self) -> bool:
        # Start the work with all presents and an empty area
        work = deque([(self.presents, FrozenBitMap2D(self.width, self.height))])
        seen_areas = set()
        
        while work:
            print(len(work), len(seen_areas))
            presents, area = work.popleft()

            assert presents

            new_areas = self.apply_present(area, presents[0], seen=seen_areas)

            # If this was the last present and there were valid `new_areas`,
            # then this tree IS satisfiable
            if len(presents) == 1 and new_areas:
                return True

            # Otherwise add the `new_areas` as new jobs at the end of the `work` deque
            work.extendleft(zip(repeat(presents[1:]), new_areas, strict=False))

        # We exhausted the `work` deque without satisfying the tree
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

        trees.append(ChristmasTree(width, height, present_counts, presents))

    n_satisfied = 0
    for tree in trees: 
        n_satisfied += int(tree.is_satisfiable())

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")

if __name__ == "__main__":
    part1()
