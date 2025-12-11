import re
from collections import deque
from pathlib import Path

import pulp as pl

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")

# Tell the solver to not log
no_log_solver = pl.PULP_CBC_CMD(msg=False)


class Machine:
    def __init__(self, configuration: str) -> None:
        # Extract the goal state
        target_state_match = re.match(r"\[([.#]+)\]", configuration)
        assert target_state_match

        # Convert the target state to a list of 0s and 1s
        self.target_state = tuple(0 if t == "." else 1 for t in target_state_match.group(1))
        rest_config = configuration[target_state_match.end() :]

        # Extract the buttons
        self.buttons = []
        button_pattern = re.compile(r"\((\d[\d,]*)\)")
        for button_match in button_pattern.finditer(rest_config):
            nums = tuple(int(n) for n in button_match.group(1).split(","))
            self.buttons.append(nums)

        rest_config = rest_config[button_match.end() :]

        # Extract the joltages
        joltages_match = re.search(r"\{(\d[\d,]*)\}", rest_config)
        assert joltages_match

        target_joltages = []
        for j in joltages_match.group(1).split(","):
            target_joltages.append(int(j))

        self.target_joltages = tuple(target_joltages)

    @staticmethod
    def _toggle_indicators(indicators: tuple[int, ...], button: tuple[int, ...]) -> tuple[int, ...]:
        """Toggles the input `indicators` according to the `button`."""
        return tuple(
            indicators[i] ^ 1 if i in button else indicators[i] for i in range(len(indicators))
        )

    def turn_on(self) -> int:
        seen = set()

        # The initial state is all off with 0 button presses
        states = deque([((0,) * len(self.target_state), 0)])

        while states:
            indicators, n_presses = states.popleft()

            # Exit early once the first state matches the `self.target_state`
            if indicators == self.target_state:
                return n_presses

            # Press each button and add to the `states`
            for button in self.buttons:
                next_indicators = self._toggle_indicators(indicators, button)

                # Avoid continuing BFS on already seen indicator states since we
                # know that any further digging in this direction will never produce
                # a shorted button press combination
                if next_indicators not in seen:
                    states.append((next_indicators, n_presses + 1))
                    seen.add(next_indicators)

        # There should always be a way to turn on the machine
        raise AssertionError()

    # @line_profiler.profile
    def configure_joltages(self) -> int:
        # Each button is its own LP variable
        buttons_lp = []
        for bi in range(len(self.buttons)):
            buttons_lp.append(pl.LpVariable(f"b{bi}", lowBound=0, cat="Integer"))

        # Build the optimization problem
        prob = pl.LpProblem("demo", pl.LpMinimize)

        # There are `len(self.target_joltages)` number of constraints
        for j, target_joltage in enumerate(self.target_joltages):
            expr = pl.LpAffineExpression()

            # For each button that has `j`, add it to this constraint
            for bi, button in enumerate(self.buttons):
                if j in button:
                    expr += buttons_lp[bi]

            # Finally this expression must equal the `target_joltage`
            prob += expr == target_joltage

        # After adding all of the constraints, add the condition we want to minimize
        # which is the sum of all of the button variables (representing number of presses)
        prob += sum(buttons_lp)

        # Solve the problem
        prob.solve(no_log_solver)

        # The minimum number of presses is in the values of `buttons_lp`. These are integer
        # values as floats due to solver internals. Round as a result to convert to an int.
        return sum(round(b.value()) for b in buttons_lp)


def part1():
    machines = []
    with IN_FILE.open("r") as f:
        for config_line in f:
            machines.append(Machine(config_line))

    print(f"Part 1 minimum turn on presses: {sum(m.turn_on() for m in machines)}")


def part2():
    machines = []
    with IN_FILE.open("r") as f:
        for config_line in f:
            machines.append(Machine(config_line))

    print(f"Part 2 minimum joltage presses: {sum(m.configure_joltages() for m in machines)}")


if __name__ == "__main__":
    part1()

    part2()
