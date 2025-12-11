import re
from collections import deque
from pathlib import Path
import numpy as np

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

    def _gaussian_eliminate(self, aug_matrix: np.array) -> np.array:
        for bi in range(len(self.buttons)):
            # Get the index of the first row with index `>= bi`
            # with a non-zero value at column `bi`
            pivot_candidates = np.nonzero(aug_matrix[bi:, bi])[0]
            if pivot_candidates.size:
                first_row = pivot_candidates[0] + bi
            else:
                breakpoint()

            # If the `first_row` is not `bi` already, swap it to this position
            if first_row != bi:
                aug_matrix[[bi, first_row]] = aug_matrix[[first_row, bi]]

            # Scale the row at `bi` so that the column value at `bi` is 1            
            if aug_matrix[bi, bi] != 1:
                # Assert that all values divide evenly
                assert np.all(aug_matrix[bi] % aug_matrix[bi, bi] == 0)
                
                aug_matrix[bi] //= aug_matrix[bi, bi]

            # For all rows below `bi` with non-zero values at `bi`,
            # use subtraction to make them 0
            for r in range(bi + 1, aug_matrix.shape[0]):
                factor = aug_matrix[r, bi]
                aug_matrix[r] -= factor * aug_matrix[bi]

        # Assert that the `aug_matrix` is now in "row-echelon" form
        assert np.all(np.diag(aug_matrix[:, :len(self.buttons)]) == 1)

        # A row is impossible if all coeffs are zero AND the RHS is nonzero
        no_solution_mask = (np.all(aug_matrix[:, :-1] == 0, axis=1) & (aug_matrix[:, -1] != 0))
        assert not np.any(no_solution_mask)
        
        # Now use back substitute from bottom up
        solutions = aug_matrix[:, -1]
        for bi in range(len(self.buttons) - 1, -1, -1):
            solutions[bi] -= np.dot(
                aug_matrix[bi, bi + 1 : len(self.buttons)],
                solutions[bi + 1 : len(self.buttons)]
            )

        # Assert that all solutions are >= 0
        assert np.all(solutions >= 0)

        return solutions
    
    # @line_profiler.profile
    def configure_joltages(self) -> int:
        # Each button gets an index
        buttons_with_ids = list(enumerate(self.buttons))
        
        # The target joltages can be solved as a system of linear equations using linear algebra.
        # Each joltage gets its own equation with its target as the answer. The unknowns are
        # the button_ids that affect this joltage.
        # The coefficient matrix is of size `len(self.target_joltages) X len(self.buttons)`
        coeff_matrix = np.zeros((len(self.target_joltages), len(self.buttons)), dtype=int)

        # Fill in the `coeff_matrix`
        for i in range(len(self.target_joltages)):
            for button_id, button in buttons_with_ids:
                if i in button:
                    coeff_matrix[i, button_id] = 1

        # The answers matrix is of size `len(self.target_joltages) X 1`
        # The augmented matrix is of size `len(self.target_joltages) X (len(self.buttons) + 1)`
        answers = np.array(self.target_joltages).reshape(-1, 1)
        aug_matrix = np.hstack((coeff_matrix, answers))

        # Gaussian eliminate the `aug_matrix`
        solutions = self._gaussian_eliminate(aug_matrix)

        # The number of button presses is the sum of the `solutions`
        return np.sum(solutions)


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
