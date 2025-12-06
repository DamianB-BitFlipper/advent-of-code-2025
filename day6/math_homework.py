import re
from collections import defaultdict
from functools import reduce
from operator import add, mul
from pathlib import Path

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")


def part1():
    problems = defaultdict(list)
    solutions = []

    with IN_FILE.open("r") as f:
        line = next(f)
        for next_line in f:
            for problem_id, number_match in enumerate(re.finditer(r"(\d+)", line)):
                problems[problem_id].append(int(number_match.group(1)))

            # After processing each row, assert that the lengths of all problems are the same
            assert len({len(problem) for problem in problems.values()}) == 1

            # Move the `line` forward
            line = next_line

        # Now `line` has the last line of the file which has the operators
        for problem_id, operator_match in enumerate(re.finditer(r"([*+])", line)):
            operator = operator_match.group(1)

            if operator == "*":
                solutions.append(reduce(mul, problems[problem_id], 1))
            else:  # operator == '+
                solutions.append(reduce(add, problems[problem_id], 0))

    print(f"Part 1 final solution: {sum(solutions)}")


def part2():
    problems = defaultdict(list)
    operators = []
    solutions = []

    with IN_FILE.open("r") as f:
        lines = f.readlines()

        problem_divider_indices = []

        # Operators are at the last line
        operators_str = lines[-1]
        for operator_match in re.finditer(r"([*+])", operators_str):
            if operator_match.group(1) == "*":
                operators.append(mul)
            else:  # == '+'
                operators.append(add)

            problem_divider_indices.append(operator_match.start())

        # The last divider is the end of the `operators_str`
        problem_divider_indices.append(len(operators_str))

        # Iterate the problem lines
        for line in lines[0:-1]:
            for problem_id, (start_index, end_index) in enumerate(
                zip(problem_divider_indices, problem_divider_indices[1:], strict=False)
            ):
                # The value at the `end_index - 1` should always be
                # the dividing space (or newline)
                assert line[end_index - 1] in {" ", "\n"}

                # Do not include the final dividing space in the `digit`s
                for digit_idx, digit in enumerate(line[start_index : end_index - 1]):
                    # The `digit_idx` is out of range, so append, otherwise edit in place
                    if digit_idx >= len(problems[problem_id]):
                        problems[problem_id].append(digit)
                    else:
                        problems[problem_id][digit_idx] += digit

    # Compute the solutions. The `problems` should be strings of the
    # numbers vertically read from top to bottom
    for problem_id, problem in problems.items():
        op = operators[problem_id]
        if op is mul:
            solutions.append(reduce(op, map(int, problem), 1))
        else:  # `op is add`
            solutions.append(reduce(op, map(int, problem), 0))

    print(f"Part 2 final solution: {sum(solutions)}")


if __name__ == "__main__":
    part1()

    part2()
