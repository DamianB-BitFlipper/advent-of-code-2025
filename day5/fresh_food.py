import re
from pathlib import Path

from sortedcontainers import SortedList

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")


def read_input_data() -> tuple[list[tuple[int, int]], list[int]]:
    """Read the input data to get the fresh ID ranges and ingredient IDs."""
    fresh_id_ranges = []
    ingredient_ids = []

    fresh_ids_pattern = re.compile(r"(\d+)-(\d+)")
    with IN_FILE.open("r") as f:
        for fresh_id_range in f:
            fresh_id_range = fresh_id_range.rstrip("\n")

            # Finished processing all fresh ID ranges
            if not fresh_id_range:
                break

            m = fresh_ids_pattern.fullmatch(fresh_id_range)
            assert m
            range_start = int(m.group(1))
            range_end = int(m.group(2))

            fresh_id_ranges.append((range_start, range_end))

        for ingredient_id in f:
            ingredient_id = int(ingredient_id.rstrip("\n"))
            ingredient_ids.append(ingredient_id)

    return fresh_id_ranges, ingredient_ids


def get_simplified_fresh_id_ranges(id_ranges: list[tuple[int, int]]) -> SortedList:
    fresh_id_ranges = SortedList()
    for range_start, range_end in id_ranges:
        start_idx = fresh_id_ranges.bisect_left(range_start)
        end_idx = fresh_id_ranges.bisect_right(range_end)

        # If `start_idx` is odd, then it falls within an existing range.
        # So the real `start_idx` is the one before it
        if start_idx % 2:
            start_idx -= 1
            assert start_idx >= 0

            # Update the `range_start` with the new beginning of the range
            range_start = fresh_id_ranges[start_idx]

        # If `end_idx` is odd, then it also falls within an existing range.
        # So the real `end_idx` is the one after it. The `bisect_right`
        # already returns the index of the next item
        if end_idx % 2:
            # Update the `range_end` with the new end of the range
            range_end = fresh_id_ranges[end_idx]

        # Delete all of the values between the `range_start` and `range_end` inclusively
        to_delete = list(fresh_id_ranges.irange(range_start, range_end))
        for v in to_delete:
            fresh_id_ranges.remove(v)

        # Add in the `range_start` and `range_end`
        fresh_id_ranges.add(range_start)
        fresh_id_ranges.add(range_end)

        # There should always be an even number of elements in the `fresh_id_ranges`
        assert not (len(fresh_id_ranges) % 2)

    return fresh_id_ranges


def part1():
    n_fresh = 0
    id_ranges, ingredient_ids = read_input_data()
    fresh_id_ranges = get_simplified_fresh_id_ranges(id_ranges)

    # Once the `fresh_id_ranges` is built, then count the number of fresh ingredients
    for ingredient_id in ingredient_ids:
        # If the `ingredient_id` is in the `fresh_id_ranges` or the bisect_left
        # is odd, then it falls within a range
        if ingredient_id in fresh_id_ranges or fresh_id_ranges.bisect_left(ingredient_id) % 2:
            n_fresh += 1

    print(f"Part 1 number of fresh: {n_fresh}")


def part2():
    n_total = 0
    id_ranges, _ = read_input_data()
    fresh_id_ranges = get_simplified_fresh_id_ranges(id_ranges)

    for range_start, range_end in zip(fresh_id_ranges[0::2], fresh_id_ranges[1::2], strict=True):
        # Add the total number of possible fresh ingredients in this range + 1 to count endpoint
        n_total += range_end - range_start + 1

    print(f"Part 2 possible fresh {n_total}")


if __name__ == "__main__":
    part1()

    part2()
