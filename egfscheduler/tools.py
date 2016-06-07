def gap_constraints(task1_name, task2_name, min_gap=None, max_gap=None):
    if max_gap is None:
        # only a min gap has been provided
        return lambda tasks: (
            (get_task_by_name(tasks, task1_name) +
             get_task_by_name(tasks, task1_name).duration +
             min_gap) < get_task_by_name(tasks, task2_name)
        )
    elif min_gap is None:
        # only a max gap has been provided
        return lambda tasks: (
            (get_task_by_name(tasks, task1_name) +
             get_task_by_name(tasks, task1_name).duration +
             max_gap) > get_task_by_name(tasks, task2_name)
        )
    else:
        return [
            gap_constraints(task1_name, task2_name, min_gap=min_gap),
            gap_constraints(task1_name, task2_name, max_gap=max_gap)
        ]


def get_task_by_name(tasks_list, name):
    """Return the task from the list that verifies task.name == name.

    If there are 0 or more than 2 tasks with that name, a ValueError is raised.
    """
    tasks = [
        task for task in tasks_list
        if task.name == name
    ]
    if len(tasks) != 1:
        raise ValueError("found %d entries for task name %s" % (
            len(tasks), name
        ))
    return tasks[0]
