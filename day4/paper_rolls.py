from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")


def move_paper(grid: list[list[str]], *, remove: bool = False) -> int:
    # Search directions (dx, dy)
    directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    grid_height = len(grid)
    grid_width = len(grid[0])

    # Compute the number of move-able paper rolls
    n_moveable = 0
    for y in range(grid_height):
        for x in range(grid_width):
            # Skip if we currently are not on a paper roll
            if grid[y][x] != "@":
                continue

            n_neighbors = 0
            for dx, dy in directions:
                x_offset = x + dx
                y_offset = y + dy

                # Out of bounds, skip
                if not ((0 <= x_offset < grid_width) and (0 <= y_offset < grid_height)):
                    continue

                if grid[y_offset][x_offset] == "@":
                    n_neighbors += 1

            if n_neighbors < 4:
                n_moveable += 1

                # Mark the current paper as removed
                if remove:
                    grid[y][x] = "."

    return n_moveable


def part1():
    # Create the full grid
    grid = []
    for paper_rolls in IN_FILE.open("r"):
        # Add a new row
        row = list(paper_rolls.rstrip("\n"))
        grid.append(row)

    n_moveable = move_paper(grid)

    print(f"Part 1 number of moveable: {n_moveable}")


def part2():
    # Create the full grid
    grid = []
    for paper_rolls in IN_FILE.open("r"):
        # Add a new row
        row = list(paper_rolls.rstrip("\n"))
        grid.append(row)

    n_moveable = 0
    while n_moved := move_paper(grid, remove=True):
        n_moveable += n_moved

    print(f"Part 2 number of moveable: {n_moveable}")


if __name__ == "__main__":
    part1()
    part2()
