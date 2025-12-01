from pathlib import Path
import re

# IN_FILE = Path("./demo_input.txt")
IN_FILE = Path("./full_input.txt")
LOCK_RING = 100

def part1():
    password = 0
    lock_state = 50
    
    pattern = re.compile(r'([LR])(\d+)')
    for line in IN_FILE.open('r'):
        # Strip any trailing newlines
        line = line.rstrip("\n")
        
        m = pattern.fullmatch(line)
        assert m

        # Left rotation subtracts
        if m.group(1) == 'L':
            lock_state -= int(m.group(2))
        else:
            lock_state += int(m.group(2))

        # Be sure to handle the ring by using modulus
        lock_state = lock_state % LOCK_RING

        # Increment `password` every time the `lock_state` is 0
        if lock_state == 0:
            password += 1

    print(f"Part1 Password is: {password}")

def part2():
    password = 0
    lock_state = 50
    
    pattern = re.compile(r'([LR])(\d+)')
    for line in IN_FILE.open('r'):
        # Strip any trailing newlines
        line = line.rstrip("\n")
        
        m = pattern.fullmatch(line)
        assert m
        direction = m.group(1)
        spin_amount = int(m.group(2))

        # Left rotation subtracts
        sign = -1 if direction == 'L' else 1

        for _ in range(spin_amount):
            lock_state += sign
            if lock_state == -1:
                lock_state = 99
            if lock_state == 100:
                lock_state = 0

            if lock_state == 0:
                password += 1
            
    print(f"Part2 Password is: {password}")

    
if __name__ == "__main__":
    part1()
    part2()
