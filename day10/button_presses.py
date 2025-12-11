import re
from collections import deque
from pathlib import Path

import line_profiler

# IN_FILE = Path("./demo_input.txt")
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
            nums = tuple(int(n) for n in button_match.group(1).split(","))
            self.buttons.append(nums)

        rest_config = rest_config[button_match.end() :]

        # Extract the joltages
        joltages_match = re.search(r"\{(\d[\d,]*)\}", rest_config)
        assert joltages_match

        target_b2_joltages = ""
        b2_joltage_margins = ""
        for j in joltages_match.group(1).split(","):
            target_b2_joltages += format(int(j), '09b') + "0"
            b2_joltage_margins += "0" * 9 + "1"
        self.target_b2_joltages = int(target_b2_joltages, 2)
        self.b2_joltage_margins = int(b2_joltage_margins, 2)

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

    def _to_b2_button(self, button: tuple[int, ...]) -> int:
        ret_b2_button_str = ""
        for i in range(len(self.target_state)):
            if i in button:
                ret_b2_button_str += "0" * 8 + "1" + "0"
            else:
                ret_b2_button_str += "0" * 10

        return int(ret_b2_button_str, 2)

    def _to_b2_button_index(self, button_index: int) -> int:
        ret_b2_button_index_str = ""
        for i in range(len(self.buttons)):
            if i == button_index:
                ret_b2_button_index_str += "0" * 9 + "1"
            else:
                ret_b2_button_index_str += "0" * 10

        return int(ret_b2_button_index_str, 2)

    @staticmethod
    def _count_b2_button_presses(b2_button_presses: int) -> int:
        ret_count = 0
        mask = int("1" * 10, 2)

        while b2_button_presses:
            ret_count += (b2_button_presses & mask)
            b2_button_presses >>= 10

        return ret_count

    def _b2_joltages_to_regular(self, b2_joltages: int) -> tuple[int, ...]:
        ret = []
        mask = int("1" * 9 + "0", 2)        
        for _ in range(len(self.target_state)):
            joltage = (b2_joltages & mask) >> 1
            ret.insert(0, joltage)

            b2_joltages >>= 10

        return tuple(ret)

    def _b2_button_to_regular(self, b2_button: int) -> tuple[int, ...]:
        ret = []
        mask = int("1" * 9 + "0", 2)        
        for i in range(len(self.target_state) - 1, -1, -1):
            if b2_button & mask:
                ret.insert(0, i)

            b2_button >>= 10

        return tuple(ret)
    
    def _b2_button_presses_to_regular(self, b2_button_presses: int) -> tuple[int, ...]:
        ret = []
        mask = int("1" * 10, 2)        
        for _ in range(len(self.buttons)):
            n_presses = (b2_button_presses & mask)
            ret.insert(0, n_presses)

            b2_button_presses >>= 10

        return tuple(ret)
    
    # @line_profiler.profile
    def configure_joltages(self) -> int:
        seen_button_presses = set()
        seen_joltages = set()

        b2_buttons = [(self._to_b2_button_index(b_idx), self._to_b2_button(b))
                      for b_idx, b in enumerate(self.buttons)]

        # # The initial state is all joltages are 0 and no button presses
        # states = SortedKeyList(
        #     [(
        #         (0,) * len(self.target_joltages),
        #         tuple((button_id, 0) for button_id, _ in ordered_buttons)
        #     )],
        #     key=lambda jolt: sum(tj - j for tj, j in zip(self.target_joltages, jolt[0])), 
        # )

        # The initial state is all joltages are 0 (first 0) and no button presses (second 0)
        states = deque([(0, 0)])

        processed = 0
        while states:
            b2_joltages, b2_button_presses = states.popleft()

            # Exit early once the first state matches the `self.target_joltages`
            if b2_joltages == self.target_b2_joltages:
                return self._count_b2_button_presses(b2_button_presses)

            # if last_seen_presses != len(button_presses):
            #     last_seen_presses = len(button_presses)
            #     # print(last_seen_presses)

            processed += 1
            if not processed % 50000:
                print(f"Processed {processed=:,}")
                # if processed == 1e6:
                #     return 10

            # Press each button and add to the `states`
            for b2_button_index, b2_button in b2_buttons:
                next_b2_joltages = b2_joltages + b2_button

                # Increase the button press counter on the `button_id`
                next_b2_button_presses = b2_button_presses + b2_button_index

                # print("joltages", self._b2_joltages_to_regular(b2_joltages))
                # print("button", self._b2_button_to_regular(b2_button))
                # print("next_jolt", self._b2_joltages_to_regular(next_b2_joltages))
                # print('----')
                # print("button", self._b2_button_to_regular(b2_button))
                # print("button_press", self._b2_button_presses_to_regular(b2_button_presses))
                # print(
                #     "next_button_press",
                #     self._b2_button_presses_to_regular(next_b2_button_presses)
                # )
                # breakpoint()

                # Only continue BFS if:
                # 1. All joltages are still <= the target joltages
                # 2. The `next_button_presses` have not been seen yet
                # 3. The `next_joltages` have not been seen yet
                if (
                    not (self.target_b2_joltages - next_b2_joltages) & self.b2_joltage_margins
                    and next_b2_button_presses not in seen_button_presses
                    and next_b2_joltages not in seen_joltages
                ):
                    seen_button_presses.add(next_b2_button_presses)
                    seen_joltages.add(next_b2_joltages)

                    states.append((next_b2_joltages, next_b2_button_presses))

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

    breakpoint()
            
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
