import itertools as itt
import numpy as np

MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.cm as cm
except:
    MATPLOTLIB_AVAILABLE = False

BOKEH_AVAILABLE = True
try:
    from bokeh.io import output_notebook
    from bokeh.plotting import figure, show, ColumnDataSource
    from bokeh.models import FixedTicker, Range1d, TapTool, OpenURL, Rect, CustomJS, HoverTool
    import pandas as pd
except:
    BOKEH_AVAILABLE = False


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


def bokeh_plot(work_units):
    all_resources = sorted(list(set([
        resource
        for work_unit in work_units
        for task in work_unit.tasks
        for resource in task.resources
    ])), key=lambda e: e.name)[::-1]

    colors = itt.cycle([
        '#%02x%02x%02x' %
        tuple((255 * np.array(cm.Paired(0.21 * i % 1.0)[:3])).astype(int))
        for i in range(30)]
    )

    tasks_df = pd.DataFrame(columns=["name", "center_x", "center_y", "duration",
                                     "height", "workunit", "color"])

    for work_unit in work_units:
        color = colors.next()
        for task in work_unit.tasks:
            start, end, resources = task.scheduled
            center_x = 0.5 * (start + end)
            duration = end - start
            margin = 0.2

            def height(resource):
                if resource.capacity == 'inf':
                    slots = 1.0
                else:
                    slots = resource.capacity
                return (1.0 - 2 * margin) / slots
            for r in task.resources:
                center_y = (
                    .5 + all_resources.index(r) +
                    margin +
                    height(r) * (0.5 + max(0, (resources[r] - 1)))
                )
                tasks_df = tasks_df.append(pd.DataFrame({
                    "task_name": task.name,
                    "start": start,
                    "end": end,
                    "center_x": center_x,
                    "center_y": center_y,
                    "duration": duration,
                    "height": height(r),
                    "workunit": work_unit.name,
                    "color": color
                }, index=[1]))
    source = ColumnDataSource(tasks_df)

    all_resources_names = [
        resource.name
        for resource in all_resources
    ]
    xmax = max(tasks_df.center_x + tasks_df.duration)
    p = figure(plot_width=900, plot_height=400,
               tools="xpan,xwheel_zoom,box_zoom,reset,resize,tap",
               y_range=all_resources_names, x_range=Range1d(0, xmax),
               title="EGF Planning", responsive=True)

    for i in range(len(all_resources))[::2]:
        p.rect(xmax * .5, i, xmax, 1, color="navy", fill_alpha=0.1,
               line_width=0.3, line_color="black")
    p.ygrid.grid_line_color = None
    p.outline_line_color = None
    p.yaxis.axis_line_width = None

    rects = p.rect(x='center_x', y='center_y', width='duration',
                   height='height', fill_color='color',
                   line_width=0.7, line_color="black", name="task",
                   source=source)

    hover_rects = p.rect(x='center_x', y='center_y', width='duration',
                         height='height', fill_color=None,
                         line_width=3, line_color="black")

    code = """
    var hover_rects_data = {
         'center_x': [],
         'center_y': [],
         'duration': [],
         'height': []
    };
    var ind = cb_data.index['1d'].indices;
    var rects_data = rects.get('data');
    var work_units = rects_data["workunit"]
    var work_unit = work_units[ind]
    for (i=0; i < work_units.length; i++) {
        if (work_units[i] == work_unit){
            hover_rects_data['center_x'].push(rects_data.center_x[i]);
            hover_rects_data['center_y'].push(rects_data.center_y[i]);
            hover_rects_data['duration'].push(rects_data.duration[i]);
            hover_rects_data['height'].push(rects_data.height[i]);
        }
    }
    hover_rects.set('data', hover_rects_data);
    """
    callback = CustomJS(args={'rects': rects.data_source,
                              'hover_rects': hover_rects.data_source},
                        code=code)
    hover = HoverTool(names=["task"],
                      callback=callback,
                      tooltips="""
            <u><b>@task_name (@workunit)</b></u><br/>
            t= @start => @end
            """
                      )

    p.add_tools(hover)
    p.logo = None
    url = "http://www.egfscheduler.com/@workunit/"
    #  taptool = p.select(type=TapTool)
    #  taptool.callback = OpenURL(url=url)
    return p
