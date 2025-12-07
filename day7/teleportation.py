from collections import defaultdict
from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")


class Grid:
    def __init__(self):
        self.grid = []

    def add_line(self, line: str):
        row = list(line)

        # Assert that `row` is the same length as all other rows in `self.grid`
        assert all(len(row) == len(r) for r in self.grid)

        self.grid.append(row)

    def run(self) -> tuple[int, int]:
        paths_count = defaultdict(int)
        n_splits = 0
        assert len(self.grid) >= 2
        for active_row in range(len(self.grid) - 1):
            # Special case for the start
            if active_row == 0:
                start_index = self.grid[active_row].index("S")

                # Sanity check
                assert self.grid[active_row + 1][start_index] == "."
                self.grid[active_row + 1][start_index] = "|"

                # Record the initial path at `start_index`
                paths_count[start_index] = 1
            else:
                for index, char in enumerate(self.grid[active_row]):
                    if char == "|":
                        # Look to see if the next spot is empty or a splitter
                        if self.grid[active_row + 1][index] == ".":
                            self.grid[active_row + 1][index] = "|"

                            # No splitting and paths indices are the same,
                            # no need to affect the `paths_count` dict
                        elif self.grid[active_row + 1][index] == "^":
                            # The `index` should never occupy the edges
                            assert 0 < index < len(self.grid[active_row]) - 1

                            assert self.grid[active_row + 1][index - 1] in {".", "|"}
                            assert self.grid[active_row + 1][index + 1] in {".", "|"}
                            self.grid[active_row + 1][index - 1] = "|"
                            self.grid[active_row + 1][index + 1] = "|"

                            # Advance all paths ending at `index`
                            cur_count = paths_count[index]
                            assert cur_count > 0

                            # The path at `index` ends, but splits in two
                            paths_count[index] = 0
                            paths_count[index - 1] += cur_count
                            paths_count[index + 1] += cur_count

                            # Increment the split counter
                            n_splits += 1

        return sum(paths_count.values()), n_splits


def part1():
    grid = Grid()

    with IN_FILE.open("r") as f:
        for line in f:
            line = line.rstrip("\n")
            grid.add_line(line)

    # Run the grid and count the number of splits
    _, n_splits = grid.run()

    print(f"Part 1 number of splits: {n_splits}")


def part2():
    grid = Grid()

    with IN_FILE.open("r") as f:
        for line in f:
            line = line.rstrip("\n")
            grid.add_line(line)

    # Run the grid and count the number of splits
    n_paths, _ = grid.run()

    print(f"Part 2 number of paths: {n_paths}")


if __name__ == "__main__":
    part1()

    part2()
