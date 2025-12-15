from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterator
from enum import IntEnum, auto
from itertools import repeat
from pathlib import Path
from typing import Literal, cast

import bitarray as ba

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")


class Rotation(IntEnum):
    ZERO = auto()
    NINETY = auto()
    ONEEIGHTY = auto()
    TWOSEVENTY = auto()


class FrozenBitMap2D:
    def __init__(self, width: int, height: int, *, data: ba.frozenbitarray | None = None):
        self.w = width
        self.h = height

        if data:
            # Sanity check
            assert len(data) == self.w * self.h
            self.data = data
        else:
            self.data = ba.frozenbitarray(self.w * self.h)

        self.used_space = self.data.count()

    @classmethod
    def fromBitMap2D(cls, o: BitMap2D) -> FrozenBitMap2D:
        return cls(o.w, o.h, data=ba.frozenbitarray(o.data))

    def toBitMap2D(self) -> BitMap2D:
        return BitMap2D(self.w, self.h, data=ba.bitarray(self.data))

    def is_conflicting(self, x: int, y: int) -> bool:
        # Outside of bounds never conflicts
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return False

        offset = (y * self.w) + x
        return bool(self.data[offset])

    def nonconflicting_or_at(
        self,
        other: FrozenBitMap2D,
        rotation: Rotation,
        xy: tuple[int, int],
        *,
        limit_w: int,
        limit_h: int,
    ) -> FrozenBitMap2D | None:
        """Applies the `other` in an XOR with the pivot at (x, y) and the `rotation`.

        If there is a conflict (self had a 1 and other also has a 1 in the same place),
        then returns `None`. Otherwise returns the resulting OR'd `FrozenBitMap2D`."""
        x, y = xy

        # Sanity check that the `other` is a shape of size 3x3
        assert other.w == 3 and other.h == 3

        # Record the possible min/max coordinates of the resulting working area. Since
        # the `xy` can be out of bounds, factor that in as well.
        min_x = min(x, 0)
        min_y = min(y, 0)
        max_x = max(x, self.w - 1)
        max_y = max(y, self.h - 1)

        # Only check for collisions for points within `self`'s working area. Anywhere
        # the `other` extends beyond the bounds does not conflict always
        match rotation:
            case Rotation.ZERO:  # Pivot is top-left
                conflicting = any(
                    self.is_conflicting(i, j)
                    for i, j, oi, oj in [
                        (x, y, 0, 0),
                        (x + 1, y, 1, 0),
                        (x + 2, y, 2, 0),
                        (x, y + 1, 0, 1),
                        (x + 1, y + 1, 1, 1),
                        (x + 2, y + 1, 2, 1),
                        (x, y + 2, 0, 2),
                        (x + 1, y + 2, 1, 2),
                        (x + 2, y + 2, 2, 2),
                    ]
                    if other.data[oi + oj * 3]
                )
                max_x = max(max_x, x + 2)
                max_y = max(max_y, y + 2)
            case Rotation.NINETY:  # Pivot is top-right
                conflicting = any(
                    self.is_conflicting(i, j)
                    for i, j, oi, oj in [
                        (x, y, 2, 0),
                        (x - 1, y, 1, 0),
                        (x - 2, y, 0, 0),
                        (x, y + 1, 2, 1),
                        (x - 1, y + 1, 1, 1),
                        (x - 2, y + 1, 0, 1),
                        (x, y + 2, 2, 2),
                        (x - 1, y + 2, 1, 2),
                        (x - 2, y + 2, 0, 2),
                    ]
                    if other.data[oi + oj * 3]
                )
                min_x = min(min_x, x - 2)
                max_y = max(max_y, y + 2)
            case Rotation.ONEEIGHTY:  # Pivot is bottom-right
                conflicting = any(
                    self.is_conflicting(i, j)
                    for i, j, oi, oj in [
                        (x, y, 2, 2),
                        (x - 1, y, 1, 2),
                        (x - 2, y, 0, 2),
                        (x, y - 1, 2, 1),
                        (x - 1, y - 1, 1, 1),
                        (x - 2, y - 1, 0, 1),
                        (x, y - 2, 2, 0),
                        (x - 1, y - 2, 1, 0),
                        (x - 2, y - 2, 0, 0),
                    ]
                    if other.data[oi + oj * 3]
                )
                min_x = min(min_x, x - 2)
                min_y = min(min_y, y - 2)
            case Rotation.TWOSEVENTY:  # Pivot is bottom-left
                conflicting = any(
                    self.is_conflicting(i, j)
                    for i, j, oi, oj in [
                        (x, y, 0, 2),
                        (x + 1, y, 1, 2),
                        (x + 2, y, 2, 2),
                        (x, y - 1, 0, 1),
                        (x + 1, y - 1, 1, 1),
                        (x + 2, y - 1, 2, 1),
                        (x, y - 2, 0, 0),
                        (x + 1, y - 2, 1, 0),
                        (x + 2, y - 2, 2, 0),
                    ]
                    if other.data[oi + oj * 3]
                )
                max_x = max(max_x, x + 2)
                min_y = min(min_y, y - 2)
            case _:
                # Should never happen
                raise AssertionError()

        # There is a conflict for this configuration, so return `None`
        if conflicting:
            return None

        new_width = max_x - min_x + 1
        new_height = max_y - min_y + 1

        # If any of the new height and widths exceed the given limits, then this
        # new area cannot fit under the tree, so exit early
        if new_width > limit_w or new_height > limit_h:
            return None

        new_area = ba.bitarray(new_width * new_height)

        # Compute the offsets for `self.data` within `new_area` since `min_x` and `min_y`
        # may be negative and extend beyond the bouds. We still want `self.data` to
        # remain in place starting from "its (0, 0)".
        offset_x = 0 - min_x
        offset_y = 0 - min_y

        def old_to_new_offset(old_x: int, old_y: int) -> int:
            """Compute the offset in to the `new_area` given `old_x` and `old_y` coordinates."""
            return (old_y + offset_y) * new_width + offset_x + old_x

        # Copy our `self.data` in to the `new_area` row by row
        for j in range(self.h):
            new_area[old_to_new_offset(0, j) : old_to_new_offset(self.w, j)] = self.data[
                j * self.w : (j + 1) * self.w
            ]

        # Now add in the `other` shape
        match rotation:
            case Rotation.ZERO:  # Pivot is top-left
                for i, j, oi, oj in [
                    (x, y, 0, 0),
                    (x + 1, y, 1, 0),
                    (x + 2, y, 2, 0),
                    (x, y + 1, 0, 1),
                    (x + 1, y + 1, 1, 1),
                    (x + 2, y + 1, 2, 1),
                    (x, y + 2, 0, 2),
                    (x + 1, y + 2, 1, 2),
                    (x + 2, y + 2, 2, 2),
                ]:
                    new_area[old_to_new_offset(i, j)] |= other.data[oj * 3 + oi]

            case Rotation.NINETY:  # Pivot is top-right
                for i, j, oi, oj in [
                    (x, y, 2, 0),
                    (x - 1, y, 1, 0),
                    (x - 2, y, 0, 0),
                    (x, y + 1, 2, 1),
                    (x - 1, y + 1, 1, 1),
                    (x - 2, y + 1, 0, 1),
                    (x, y + 2, 2, 2),
                    (x - 1, y + 2, 1, 2),
                    (x - 2, y + 2, 0, 2),
                ]:
                    new_area[old_to_new_offset(i, j)] |= other.data[oj * 3 + oi]

            case Rotation.ONEEIGHTY:  # Pivot is bottom-right
                for i, j, oi, oj in [
                    (x, y, 2, 2),
                    (x - 1, y, 1, 2),
                    (x - 2, y, 0, 2),
                    (x, y - 1, 2, 1),
                    (x - 1, y - 1, 1, 1),
                    (x - 2, y - 1, 0, 1),
                    (x, y - 2, 2, 0),
                    (x - 1, y - 2, 1, 0),
                    (x - 2, y - 2, 0, 0),
                ]:
                    new_area[old_to_new_offset(i, j)] |= other.data[oj * 3 + oi]
            case Rotation.TWOSEVENTY:  # Pivot is bottom-left
                for i, j, oi, oj in [
                    (x, y, 0, 2),
                    (x + 1, y, 1, 2),
                    (x + 2, y, 2, 2),
                    (x, y - 1, 0, 1),
                    (x + 1, y - 1, 1, 1),
                    (x + 2, y - 1, 2, 1),
                    (x, y - 2, 0, 0),
                    (x + 1, y - 2, 1, 0),
                    (x + 2, y - 2, 2, 0),
                ]:
                    new_area[old_to_new_offset(i, j)] |= other.data[oj * 3 + oi]
            case _:
                # Should never happen
                raise AssertionError()

        return FrozenBitMap2D(new_width, new_height, data=ba.frozenbitarray(new_area))

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
        """Yields all indices that are 0s as well as a border of 1."""
        indices_1d = self.data.search(ba.bitarray([0]))

        # Top border
        yield from [(x, -1) for x in range(-1, self.w + 1)]

        # Bottom border
        yield from [(x, self.h) for x in range(-1, self.w + 1)]

        # Left edge (without double counting on the top/bottom borders)
        yield from [(-1, y) for y in range(self.h)]

        # Right edge (without double counting on the top/bottom borders)
        yield from [(self.w, y) for y in range(self.h)]

        for i_1d in indices_1d:
            yield (i_1d % self.w, i_1d // self.w)

    def __eq__(self, other: FrozenBitMap2D, /) -> bool:
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        """Hash this `FrozenBitMap2D`.

        The hash function is defined such that `FrozenBitMap2D` that are symmetrical
        horizontally, vertically or 180 degree flip will yield the same hash value.

        This is done by checking for every row `i` (^R means reversed):
        row[i] = row[n_rows - i -1]
        row[i] = row[i]^R
        row[i] = row[n_rows - i -1]^R

        with the optimization that we only need to check up to `i` of half the number of rows
        since the above equalities are horizontally symmetrical
        """
        running_hash = 0

        for hi_left in range((self.h + 1) // 2):
            hi_right = (self.h - 1) - hi_left

            data_left = self.data[hi_left * self.w : (hi_left + 1) * self.w]
            data_right = self.data[hi_right * self.w : (hi_right + 1) * self.w]

            running_hash += hash(data_left)
            running_hash += hash(data_left[::-1])
            running_hash += hash(data_right)
            running_hash += hash(data_right[::-1])

        return running_hash

    def __str__(self) -> str:
        return self.pprint()


class BitMap2D:
    def __init__(self, width: int, height: int, *, data: ba.bitarray | None = None):
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
    def __init__(
        self,
        present_id: int,
        area: FrozenBitMap2D,
        *,
        rotation: Rotation = Rotation.ZERO,
    ):
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

            if c == "#":
                data[col, row] = 1

        return cls(present_id, FrozenBitMap2D.fromBitMap2D(data))

    def _compute_rotations(self) -> list[Present] | None:
        # Only applies to the original un-rotated shape
        if self.rotation != Rotation.ZERO:
            return None

        ret = []
        rotated_datas = set()

        # First add ourselves. Importantly we want to uniquely track `self.area.data`, not
        # the `self.area` since the `hash` function of `FrozenBitMap2D` excludes rotational
        # symmetries. In this case we want rotational symmetries and just want to exclude
        # exact matches
        ret.append(self)
        rotated_datas.add(self.area.data)

        # Rotate and yield 3 times
        rotated_area = self.area.toBitMap2D()
        for rot in list(Rotation)[1:]:
            new_rotated_area = BitMap2D(3, 3)

            # Procedure to rotated a 3x3 matrix
            for i in range(3):
                for j in range(3):
                    new_rotated_area[i, j] = cast(Literal[0, 1], rotated_area[j, (2 - i)])

            # Add the newly appended present
            assert rot != Rotation.ZERO
            new_area = FrozenBitMap2D.fromBitMap2D(new_rotated_area)

            # No point in testing oriented presents that are rotationally symmetrical
            if new_area.data not in rotated_datas:
                ret.append(Present(self.id, new_area, rotation=rot))
                rotated_datas.add(new_area.data)

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
        self.presents = [
            presents[p_id] for p_id, count in self.present_counts.items() for _ in range(count)
        ]

    def apply_present(
        self,
        working_area: FrozenBitMap2D,
        present: Present,
        *,
        seen: set[FrozenBitMap2D],
    ) -> list[FrozenBitMap2D]:
        ret = []

        for xy in working_area.inactive_indices:
            for oriented_present in present.orientations_iter:
                new_area = working_area.nonconflicting_or_at(
                    oriented_present.area,
                    oriented_present.rotation,
                    xy,
                    limit_w=self.width,
                    limit_h=self.height,
                )

                # If there is a valid `new_area` that we have not seen yet
                if new_area is not None and new_area not in seen:
                    ret.append(new_area)
                    seen.add(new_area)

        return ret

    def is_satisfiable(self) -> bool:
        # Start the work with all presents and a nil initial working space
        work = deque([(self.presents, FrozenBitMap2D(0, 0))])
        seen_areas = set()

        while work:
            presents, working_area = work.popleft()

            assert presents

            new_areas = self.apply_present(working_area, presents[0], seen=seen_areas)

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
    present_pattern = re.compile(r"(\d+):\n((?:[.#]|\n(?!\n))+)")

    presents = []
    for present_match in present_pattern.finditer(file_contents):
        present_id = int(present_match.group(1))
        present_str = present_match.group(2)

        presents.append(Present.from_str(present_id, present_str))

    christmas_tree_match = re.compile(r"(\d+)x(\d+): ((?:\d+\s+)+)")

    trees = []
    for tree_match in christmas_tree_match.finditer(file_contents[present_match.end() :]):
        width = int(tree_match.group(1))
        height = int(tree_match.group(2))
        present_counts = [int(c) for c in tree_match.group(3).split()]

        trees.append(ChristmasTree(width, height, present_counts, presents))

    n_satisfied = 0
    for ti, tree in enumerate(trees):
        print(f"Starting tree: {ti}")
        satisfied = tree.is_satisfiable()
        n_satisfied += int(satisfied)
        print(f"Finished tree: {ti}, {satisfied=}")

    print(f"Part 1 Christmas trees satisfied: {n_satisfied}")


if __name__ == "__main__":
    part1()
