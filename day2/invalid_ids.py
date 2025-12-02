from pathlib import Path
import re
import math

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")

def is_invalid_id_part1(num: int) -> bool:
    n_digits = math.ceil(math.log10(num))
    # ID must be even number of digits
    if n_digits % 2:
        return False

    lower_half_mask = 10 ** (n_digits // 2)
    lower_half = num % lower_half_mask
    upper_half = (num - lower_half) // lower_half_mask

    return lower_half == upper_half

def part1():
    pattern = re.compile(r'(\d+)-(\d+)')
    invalid_sum = 0
    for match in pattern.finditer(IN_FILE.read_text()):
        range_start = int(match.group(1))
        range_end = int(match.group(2))

        for i in range(range_start, range_end + 1):
            if is_invalid_id_part1(i):
                invalid_sum += i

    print(f"Part1 Invalid sum is: {invalid_sum}")

def is_invalid_id_part2(num: int) -> bool:
    num_str = str(num)
    num_len = len(num_str)

    for prefix_sz in range(1, (num_len // 2) + 1):
        # Check if `prefix_sz` divides `num_len`, otherwise skip
        if num_len % prefix_sz:
            continue
        n_prefixes = num_len // prefix_sz
        prefix = num_str[:prefix_sz]

        # Found an invalid match!
        if prefix * n_prefixes == num_str:
            return True

    # No invalid match found
    return False
    
def part2():
    pattern = re.compile(r'(\d+)-(\d+)')
    invalid_sum = 0
    for match in pattern.finditer(IN_FILE.read_text()):
        range_start = int(match.group(1))
        range_end = int(match.group(2))

        for i in range(range_start, range_end + 1):
            if is_invalid_id_part2(i):
                invalid_sum += i

    print(f"Part2 Invalid sum is: {invalid_sum}")
    
if __name__ == "__main__":
    part1()
    part2()

