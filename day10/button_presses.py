import re
from collections import deque
from pathlib import Path

# IN_FILE = Path('./demo_input.txt')
IN_FILE = Path("./full_input.txt")


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
            nums = {int(n) for n in button_match.group(1).split(",")}
            self.buttons.append(nums)

        rest_config = rest_config[button_match.end() :]

        # Extract the joltages
        joltages_match = re.search(r"\{(\d[\d,]*)\}", rest_config)
        assert joltages_match
        self.joltages = [int(j) for j in joltages_match.group(1).split(",")]

    @staticmethod
    def _toggle_indicators(indicators: tuple[int, ...], button: set[int]):
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


def part1():
    machines = []
    with IN_FILE.open("r") as f:
        for config_line in f:
            machines.append(Machine(config_line))

    # Turn on all of the machines
    n_presses = []
    for i, m in enumerate(machines):
        print(f"Starting: {m.target_state}")
        n_presses.append(m.turn_on())
        print(f"Finished {i} / {len(machines) - 1}")

    print(f"Part 1 minimum button presses: {sum(n_presses)}")


if __name__ == "__main__":
    part1()
