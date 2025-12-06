from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")


def compute_max_joltage(battery_bank: Iterable[int], n_active: int) -> int:
    b_indices = defaultdict(list)
    for i, b in enumerate(battery_bank):
        b_indices[b].append(i)

    selected_values = []
    selected_indices = []
    look_for = 9
    while len(selected_values) < n_active:
        # The `look_for` should never go below 0 or above 9
        assert 0 <= look_for <= 9

        found = False
        if b_indices[look_for]:
            if not selected_indices:
                selected_values.append(look_for)
                selected_indices.append(b_indices[look_for][0])

                # Reset the `look_for` since it may have been decreased
                look_for = 9
                found = True
            else:
                for i in b_indices[look_for]:
                    # Add the next value greater than the last selected index
                    if i > selected_indices[-1]:
                        selected_values.append(look_for)
                        selected_indices.append(i)
                        # Reset the `look_for` since it may have been decreased
                        look_for = 9
                        found = True
                        break

        if not found:
            # No match was found, so look for a smaller value, otherwise
            # pop up the stack if the search space is exhausted
            if look_for > 0:
                look_for -= 1
            else:
                # We should always have something to pop
                assert selected_values
                assert selected_indices

                # No next index was found, pop the latest selected value and index
                look_for = selected_values.pop() - 1
                selected_indices.pop()

    # Build the return value from the `selected_values`
    ret_joltage = 0
    for base, val in enumerate(reversed(selected_values)):
        ret_joltage += val * 10**base

    return ret_joltage


def part1():
    sum_joltage = 0
    for battery_bank in IN_FILE.open("r"):
        # Strip any trailing newlines
        battery_bank = battery_bank.rstrip("\n")
        sum_joltage += compute_max_joltage(map(int, battery_bank), 2)

    print(f"Part 1 sum max joltage: {sum_joltage}")


def part2():
    sum_joltage = 0
    for battery_bank in IN_FILE.open("r"):
        # Strip any trailing newlines
        battery_bank = battery_bank.rstrip("\n")
        sum_joltage += compute_max_joltage(map(int, battery_bank), 12)

    print(f"Part 2 sum max joltage: {sum_joltage}")


if __name__ == "__main__":
    part1()
    part2()
