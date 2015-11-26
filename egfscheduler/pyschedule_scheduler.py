"""Implements a scheduler using Pyschedule.

In effects less useful than numberjack_pyschedule, and
just here for comparison purposes.
"""

import itertools as itt
import pyschedule


def pyschedule_scheduler(work_units, plot=True):
    """ Make a makespan-optimized schedule for the provided work_units

    """

    S = pyschedule.Scenario('Schedule')
    all_tasks = [
        task
        for work_unit in work_units
        for task in work_unit.tasks
    ]
    ps_tasks_dict = {
        task: S.Task("%s(%s)" % (task.name, task.id), length=task.duration)
        for task in all_tasks
    }

    all_resources = list(set([
        resource
        for task in all_tasks
        for resource in task.resources
    ]))
    ps_resources_dict = {
        resource: S.Resource(resource.name, size=resource.capacity)
        for resource in all_resources
    }

    for work_unit in work_units:

        tasks = work_unit.tasks
        ps_tasks = [ps_tasks_dict[task] for task in tasks]

        # The tasks in one work unit are executed after one another
        for (task, next_task) in zip(ps_tasks, ps_tasks[1:]):
            S += (task < next_task)

        # additional constraints can be added to work units
        for constraint in work_unit.constraints:
            S += constraint(ps_tasks)

        # If a work unit has parents it starts after their
        # last tasks.
        for parent_work_unit in work_unit.parents:
            S += (
                ps_tasks_dict[parent_work_unit.tasks[-1]] <
                ps_tasks[0]
            )

        # Enforce scheduled start if any specified
        if work_unit.scheduled_start is not None:
            S += (
                ps_tasks[0] >
                work_unit.scheduled_start + work_unit.tasks[0].duration
            )

        # Enforce work units deadlines if any specified
        if work_unit.due_time is not None:
            S += (ps_tasks[-1] < work_unit.due_time)

    # Attribute resources to tasks.
    for task in all_tasks:
        for resource in task.resources:
            ps_tasks_dict[task] += ps_resources_dict[resource]

    S.use_makespan_objective()
    result = pyschedule.solvers.mip.solve_bigm(S)

    if plot:

        try:
            import matplotlib.cm as cm
        except:
            raise ImportError("Plotting requires Matplotlib.")

        colors = itt.cycle([cm.Paired(0.21*i % 1.0) for i in range(30)])
        colors_dict = {
            ps_tasks_dict[task]: color
            for (color, work_unit) in zip(colors, work_units)
            for task in work_unit.tasks
        }
        pyschedule.plotters.matplotlib.plot(S, resource_height=1.0,
                                            show_task_labels=False,
                                            task_colors=colors_dict,
                                            hide_tasks=[S._tasks['MakeSpan']])

    if result:
        return S
    else:
        raise ValueError('no solution found')
