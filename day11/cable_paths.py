import re
from collections import Counter, defaultdict, deque
from copy import deepcopy
from itertools import chain
from pathlib import Path

# IN_FILE = Path('./demo_input.txt')
# IN_FILE = Path('./demo_input2.txt')
IN_FILE = Path("./full_input.txt")


def scale_counter(counter: Counter, k: int) -> Counter:
    return Counter({key: count * k for key, count in counter.items()})


def reverse_fill_graph(
    graph: defaultdict[str, list[str]],
    *,
    source: str,
    dest: str,
) -> int:
    # Make a copy of the `graph` since we are modifying the `children` lists
    scratch_graph = deepcopy(graph)

    # Build a reverse index of the `scratch_graph`
    reverse_index = defaultdict(list)

    # For all keys in the `scratch_graph` and the special "out" key
    for key in chain(scratch_graph, ["out"]):
        for candidate, children in scratch_graph.items():
            if key in children:
                reverse_index[key].append(candidate)

    # Make a dictionary for path resolutions. It begins fully unresolved with all of
    # their children and initially the 0 paths to `dest`
    path_resolutions = {}
    for key, children in chain(scratch_graph.items(), [("out", [])]):
        # The `dest` is fully resolved and has one initial path to itself
        if key == dest:
            path_resolutions[key] = (Counter(), 1)
        else:
            path_resolutions[key] = (Counter(children), 0)

    to_do = deque([dest])

    while to_do:
        # Resolve the `work` key in `not_resolved`, adding any fully resolved keys to
        # the `resolved` dict and to the `to_do` processing deque
        work = to_do.popleft()

        for key, (children, path_counts) in path_resolutions.items():
            # Skip if `children` is fully resolved already
            if not children:
                continue

            if work in children:
                # Resolve `work` from the `children` list
                n_occurences = children.pop(work)
                path_counts += n_occurences * path_resolutions[work][1]

                path_resolutions[key] = (children, path_counts)

            # This `key` became fully resolved if it has no more unresolved children
            if not children:
                to_do.append(key)

    # Now walk from `source` to `dest`, substituting any nodes
    # until there is no more to substitute
    while path_resolutions[source][0]:
        children, path_counts = path_resolutions[source]

        new_children = Counter()
        new_path_counts = path_counts

        for child, n_occurences in children.items():
            child_children, child_path_counts = path_resolutions[child]

            new_children += scale_counter(child_children, n_occurences)
            new_path_counts += n_occurences * child_path_counts

        path_resolutions[source] = (new_children, new_path_counts)

    return path_resolutions[source][1]


def part1():
    # Parse out the graph
    graph = defaultdict(list)
    with IN_FILE.open("r") as f:
        for node in f:
            source, destinations = node.split(":", 1)

            for match in re.finditer(r"([a-z]+)", destinations):
                graph[source].append(match.group(1))

    path_counts = reverse_fill_graph(graph, source="you", dest="out")
    print(f"Part 1 Number of paths: {path_counts}")


def part2():
    # Parse out the graph
    graph = defaultdict(list)
    with IN_FILE.open("r") as f:
        for node in f:
            source, destinations = node.split(":", 1)

            for match in re.finditer(r"([a-z]+)", destinations):
                graph[source].append(match.group(1))

    # Resolve the path counts with `dac`, `fft` and `out` as sources
    svr_dac_path_counts = reverse_fill_graph(graph, source="svr", dest="dac")
    dac_fft_path_counts = reverse_fill_graph(graph, source="dac", dest="fft")
    fft_out_path_counts = reverse_fill_graph(graph, source="fft", dest="out")

    svr_fft_path_counts = reverse_fill_graph(graph, source="svr", dest="fft")
    fft_dac_path_counts = reverse_fill_graph(graph, source="fft", dest="dac")
    dac_out_path_counts = reverse_fill_graph(graph, source="dac", dest="out")

    # Compute the path counts: svr -> dac -> fft -> out equals the paths from
    # (svr -> dac) * (dac -> fft) * (fft -> out)
    path_counts_1 = svr_dac_path_counts * dac_fft_path_counts * fft_out_path_counts

    # Compute the path counts: svr -> fft -> dac -> out equals the paths from
    # (svr -> fft) * (fft -> dac) * (dac -> out)
    path_counts_2 = svr_fft_path_counts * fft_dac_path_counts * dac_out_path_counts

    print(f"Part 2 Number of paths: {path_counts_1 + path_counts_2}")


if __name__ == "__main__":
    part1()

    part2()
