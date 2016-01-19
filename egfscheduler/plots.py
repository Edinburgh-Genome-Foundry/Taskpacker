import itertools as itt
import numpy as np

MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.cm as cm
except:
    MATPLOTLIB_AVAILABLE = False


def plot_schedule(work_units):
    """ Plot the work units schedule in a gant-like way.

    This is quite basic and arbitrary and really meant for R&D purposes.

    Example
    -------

    >>> # ... Make some work units
    >>> solve_constraints(work_units)
    >>> plot_schedule(work_units)

    """

    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Plotting requires Matplotlib.")

    all_resources = sorted(list(set([
        resource
        for work_unit in work_units
        for task in work_unit.tasks
        for resource in task.resources
    ])), key=lambda e: e.name)[::-1]

    print all_resources

    colors = itt.cycle([cm.Paired(0.21 * i % 1.0) for i in range(30)])
    fig, ax = plt.subplots(1, figsize=(15, 6))
    max_end = 0
    for work_unit in work_units:
        color = colors.next()
        ax.plot([0, 0], [0, 0], color=color, lw=8, label=work_unit.name)
        for task in work_unit.tasks:
            start, end, resources = task.scheduled
            max_end = max(end, max_end)
            margin = 0.2

            def height(resource):
                if resource.capacity == 'inf':
                    slots = 1.0
                else:
                    slots = resource.capacity
                return (1.0-2*margin) / slots

            for r in task.resources:
                y = (
                    all_resources.index(r) +
                    margin +
                    height(r) * max(0, (resources[r] - 1))
                )
                ax.add_patch(
                    patches.Rectangle(
                        (start, y),   # (x,y)
                        end - start,          # width
                        height(r),          # height
                        facecolor=color
                    )
                )

    strips_colors = itt.cycle([(1, 1, 1), (1, 0.92, 0.92)])
    for i, color in zip(range(-1, len(all_resources) + 1), strips_colors):
        ax.fill_between(
            [0, 1.1 * max_end], [i, i], y2=[i + 1, i + 1], color=color)

    N = len(all_resources)
    ax.set_yticks(np.arange(N) + 0.5)
    ax.set_ylim(-max(1, int(0.4 * N)), max(2, int(1.5 * N)))
    ax.set_yticklabels(all_resources)
    ax.legend(ncol=3, fontsize=8)
    ax.set_xlabel("time (a.u.)")
    ax.set_xlim(0, 1.1 * max_end)

    return fig, ax


# The following compute job trees


def _compute_depth(node, graph):
    parents = graph.predecessors(node)
    return (0 if (parents == []) else
            1 + max([_compute_depth(n, graph) for n in parents]))


def _tree_layout(graph):
    depth_dict = {
        node: _compute_depth(node, graph)
        for node in graph.nodes()
    }
    nodes_per_level = [
        [
            node
            for node in graph.nodes()
            if depth_dict[node] == depth
        ]
        for depth in range(max(depth_dict.values()) + 1)
    ]

    positions = {}
    for level, level_nodes in enumerate(nodes_per_level):
        level_width = len(level_nodes)
        for i, node in enumerate(level_nodes):
            x_position = 8 * (i + 1.0) / (level_width + 1)
            y_position = -level
            positions[node] = (x_position, y_position)
    return positions


def plot_dependency_graph(elements, mode="circle", figsize=(8, 5), ax=None):

    import networkx as nx

    if ax is None:
        fig, ax = plt.subplots(1, figsize=figsize)
    edges = [
        (e1.id, e2.id)
        for e2 in elements
        for e1 in e2.parents
    ]
    graph = nx.DiGraph(edges)
    if mode == "circle":
        pos = nx.graphviz_layout(graph, prog='twopi')
    elif mode == "tree":
        pos = _tree_layout(graph)
    nx.draw(graph, pos, with_labels=False, arrows=True, node_size=20,
            alpha=0.5, node_color="blue", ax=ax)
    for w in elements:
        if w.due_time is not None:
            pass

    return ax
