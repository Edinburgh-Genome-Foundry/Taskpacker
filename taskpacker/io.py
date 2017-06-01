from taskpacker import Task, Resource
import itertools as itt
import pandas
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.path import Path
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False


def get_process_from_spreadsheet(spreadsheet_path, resources_dict,
                                 sheetname=0, tasks_color="blue",
                                 task_name_prefix=""):

    if spreadsheet_path.endswith("csv"):
        process_df = pandas.read_csv(spreadsheet_path)
    else:
        process_df = pandas.read_excel(spreadsheet_path,
                                        sheetname=sheetname)

    task_name_prefix = "WU1_"
    process_tasks = {}
    tasks_list = []
    for i, row in process_df.iterrows():
        task_resources = [
            resources_dict[r.strip()]
            for r in row.resources.split(",")
        ]
        follows = str(row.follows)
        if follows == "nan":
            follows = ()
        else:
            follows = [process_tasks[t] for t in follows.split(", ")]
        new_task = Task(
            name=task_name_prefix + row.task,
            resources=task_resources,
            duration=row.duration,
            follows=follows,
            color=tasks_color,
            max_wait=(None if (str(row.max_wait) == "nan")
                           else int(row.max_wait))
        )
        process_tasks[row.task] = new_task
        tasks_list.append(new_task)

    return tasks_list

def get_resources_from_spreadsheet(spreadsheet_path, sheetname):
    if spreadsheet_path.endswith("csv"):
        resources_df = pandas.read_csv(spreadsheet_path)
    else:
        resources_df = pandas.read_excel(spreadsheet_path, sheetname)
    return {
        row.resource_name: Resource(
            name=row.resource_name,
            full_name=row.full_name,
            capacity='inf' if str(row.capacity) == "inf" else int(row.capacity)
        )
        for i, row in resources_df.iterrows()
    }

def plot_schedule(tasks):
    """ Plot the work units schedule in a gant-like way.

    This is quite basic and arbitrary and really meant for R&D purposes.
    """

    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Plotting requires Matplotlib.")

    all_resources = sorted(list(set([
        resource
        for task in tasks
        for resource in task.resources
    ])), key=lambda e: e.full_name)[::-1]

    fig, ax = plt.subplots(1, figsize=(15, 6))
    max_end = 0
    for task in tasks:
        start = task.scheduled_start
        end = task.scheduled_end
        resources = task.scheduled_resource
        max_end = max(end, max_end)
        margin = 0.2

        def height(resource):
            if resource.capacity == 'inf':
                slots = 1.0
            else:
                slots = resource.capacity
            return (1.0 - 2 * margin) / slots

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
                    facecolor=task.color,
                    edgecolor='k'
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
    ax.set_xlabel("Time")
    ax.set_xlim(0, 1.1 * max_end)

    return fig, ax



def plot_tree_graph(levels, edges, draw_node, elements_positions=None,
                    ax=None, width_factor=2.5, height_factor=2, scale=1.0,
                    edge_left_space=0.015, edge_right_space=0.015,
                    interlevel_shift=0, **txt_kw):
    """General function for plotting tree graphs.

    Parameters
    ----------

    levels
      A list of lists of nodes grouped by "level", i.e distance to the in the
      graph to the level 0. levels will be displayed on a same column.

    edges
      List of nodes pairs (source node, target node).

    draw_node
      A function f(x , y , node, ax, **kw) which draws something related to the
      node at the position x,y on the given Matplotlib ax.

    ax
      The matplotlib ax to use. If none is provided, a new ax is generated.

    Examples:
    ---------

    >>> def draw_node(x,y, node, ax):
        ax.text(x,y, node)
    >>> plot_tree_graph(levels=[["A","B","C"], ["D,E"], ["F"]],
                        edges=[("A","D"),("B","D"),("C","E")
                               ("D","F"),("E","F")],
                        draw_node = draw_node,)



    """
    levels_dict = {
        element: level
        for level, elements in enumerate(levels)
        for element in elements
    }
    if elements_positions is None:
        elements_positions = {}
        for lvl, elements in enumerate(levels):
            yy = np.linspace(0, 1, len(elements) + 2)[1:-1]
            yy += interlevel_shift * (1-2*(lvl % 2))
            x = 1.0 * (1 + lvl) / (len(levels) + 1)
            for y, element in zip(yy, elements):
                elements_positions[element] = (x, y)

    if ax is None:
        width = width_factor * len(levels) * scale
        height = height_factor * max([len(lvl) for lvl in levels]) * scale
        fig, ax = plt.subplots(1, figsize=(width, height))

    for element, (x, y) in elements_positions.items():
        draw_node(x, y, element, ax, **txt_kw)

    y_spans = [
        elements_positions[elements[1]][1] - elements_positions[elements[0]][1]
        for elements in levels
        if len(elements) > 1
    ]

    delta_y = 0.5*min(y_spans) if y_spans != [] else 0

    for el1, el2 in edges:
        x1, y1 = elements_positions[el1]
        x2, y2 = elements_positions[el2]
        x1 += edge_left_space * np.sqrt(scale)
        x2 += -edge_right_space * np.sqrt(scale)
        if ((levels_dict[el2] - levels_dict[el1]) > 1) and (y1 == y2):
            patch = patches.PathPatch(
                Path([(x1, y1), (0.5 * x2 + 0.5 * x1, y1-delta_y),
                      (0.5 * x2 + 0.5 * x1, y2-delta_y), (x2, y2)],
                     [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]),
                facecolor='none', lw=1 * scale,
                zorder=-1000
            )

        else:
            patch = patches.PathPatch(
                Path([(x1, y1), (0.9 * x2 + 0.1 * x1, y1),
                      (0.1 * x2 + 0.9 * x1, y2), (x2, y2)],
                     [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]),
                facecolor='none', lw=1 * scale,
                zorder=-1000
            )

        ax.add_patch(patch)

    ax.axis("off")
    return ax


def plot_tasks_dependency_graph(tasks, ax=None):
    """Plot the graph of all inter-dependencies in the provided tasks list."""
    if not NX_AVAILABLE:
        raise ImportError("Install Networkx to plot task dependency graphs.")
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Install Matplotlib to plot task dependency graphs.")
    g = nx.DiGraph()
    tasks_dict = {
        task.id: task
        for task in tasks
    }
    for task_id, task in tasks_dict.items():
        for parent_task in task.follows:
            g.add_edge(parent_task.id, task_id)

    nodes_depths = {
        node: 0
        for node in g.nodes()
    }
    for source, lengths in nx.shortest_path_length(g):
        for target, length in lengths.items():
            nodes_depths[target] = max(nodes_depths[target], length)
    levels = [
        sorted([
            node
            for node, depth in nodes_depths.items()
            if depth == this_depth
        ])[::-1]
        for this_depth in range(max(nodes_depths.values()) + 1)
    ]

    def draw_node(x, y, node, ax):
        task = tasks_dict[node]
        text = task.name.replace("_", "\n") + "\nduration: %d" % task.duration
        ax.text(x, y, text, verticalalignment="center",
                horizontalalignment="center",
                bbox={'facecolor': 'white', 'lw': 0})
    return plot_tree_graph(levels, g.edges(), draw_node, width_factor=2, ax=ax)
