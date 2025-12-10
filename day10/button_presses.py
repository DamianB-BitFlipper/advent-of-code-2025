import re
from collections import deque
from pathlib import Path

import line_profiler
from sortedcontainers import SortedKeyList, SortedList

IN_FILE = Path("./demo_input.txt")
# IN_FILE = Path("./full_input.txt")


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
        self.target_joltages = tuple(int(j) for j in joltages_match.group(1).split(","))

    @staticmethod
    def _toggle_indicators(indicators: tuple[int, ...], button: tuple[int, ...]) -> tuple[int, ...]:
        """Toggles the input `indicators` according to the `button`."""
        return tuple(
            indicators[i] ^ 1 if i in button else indicators[i] for i in range(len(indicators))
        )

    @staticmethod
    def _add_joltages(joltages: tuple[int, ...], button: tuple[int, ...]) -> tuple[int, ...]:
        """Add to the `joltages` according to the `button`."""
        return tuple(joltages[i] + 1 if i in button else joltages[i] for i in range(len(joltages)))

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

    @line_profiler.profile
    def configure_joltages(self) -> int:
        seen_button_presses = set()
        seen_joltages = set()

        # The initial state is all joltages are 0 and no button presses
        states = SortedKeyList(
            [((0,) * len(self.target_joltages), SortedList())],
            key=lambda jolt: sum(tj - j for tj, j in zip(self.target_joltages, jolt[0])),
        )

        last_seen_presses = 0
        processed = 0
        while states:
            joltages, button_presses = states.pop(0)

            # Exit early once the first state matches the `self.target_joltages`
            if joltages == self.target_joltages:
                return len(button_presses)

            if last_seen_presses != len(button_presses):
                last_seen_presses = len(button_presses)
                # print(last_seen_presses)

            processed += 1
            if not processed % 10000:
                print(f"Processed {processed=} {len(button_presses)}")
                if processed == 3e5:
                    return 10

            # Press each button and add to the `states`
            for button in self.buttons:
                next_joltages = self._add_joltages(joltages, button)

                next_button_presses = button_presses.copy()
                next_button_presses.add(button)
                tuple_next_button_presses = tuple(next_button_presses)

                # Only continue BFS if:
                # 1. All joltages are still <= the target joltages
                # 2. The `next_button_presses` have not been seen yet
                # 3. The `next_joltages` have not been seen yet
                if (
                    tuple_next_button_presses not in seen_button_presses
                    and next_joltages not in seen_joltages
                    and all(
                        next_joltages[i] <= self.target_joltages[i]
                        for i in range(len(self.target_joltages))
                    )
                ):
                    seen_button_presses.add(tuple_next_button_presses)
                    seen_joltages.add(next_joltages)

                    states.add((next_joltages, next_button_presses))

        # There should always be a way to configure the joltages
        raise AssertionError()


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

    n_presses = []
    for i, m in enumerate(machines):
        print(f"Starting {i}")
        n_presses.append(m.configure_joltages())
        print(f"Finished {i} / {len(machines) - 1}")

    print(f"Part 2 {sum(n_presses)}")
    # print(f"Part 2 minimum joltage presses: {sum(m.configure_joltages() for m in machines)}")


if __name__ == "__main__":
    part1()

    part2()
