import uuid
from tqdm import tqdm
import Numberjack as nj
import itertools as itt
from copy import copy
from collections import OrderedDict


class Task:
    """Tasks are the steps of a work unit, performed using specific resources.

    Parameters
    ----------

    name
      Name of the task (appears when printed and plotted).

    resources
      list of Resource objects specifying the resources occupied by the task.

    duration
      Duration of the task (the choice of the unit is left to the user.

    scheduled_resource
      Either None or a dict {resource: slot_used}
    """

    def __init__(
        self,
        name,
        resources,
        duration,
        follows=(),
        max_wait=None,
        scheduled_start=None,
        scheduled_resources=None,
        priority=1,
        due_time=None,
        color="blue",
    ):

        self.resources = resources
        self.duration = duration
        self.name = name
        self.scheduled_start = scheduled_start
        self.scheduled_resources = scheduled_resources
        self.follows = follows
        self.max_wait = max_wait
        self.color = color
        self.priority = priority
        self.due_time = due_time

        self.id = self.name + str(uuid.uuid1().int)

    @property
    def scheduled_end(self):
        if self.scheduled_start is None:
            return None
        else:
            return self.scheduled_start + self.duration

    def __repr__(self):
        return "Task(%(name)s, %(duration)s)" % self.__dict__

    def __hash__(self):
        return hash(self.id)

    def to_dict(self):
        def color_to_html(color):
            if isinstance(color, str):
                return color
            else:
                return "#%02x%02x%02x" % tuple([int(255 * e) for e in color[:3]])

        return OrderedDict(
            [
                (k, "" if v is None else v)
                for k, v in [
                    ("task", self.name),
                    ("resources", ", ".join([r.name for r in self.resources])),
                    ("duration", self.duration),
                    ("follows", ", ".join([task.name for task in self.follows])),
                    ("max_wait", self.max_wait),
                    ("scheduled_start", self.scheduled_start),
                    (
                        "scheduled_resources",
                        None
                        if self.scheduled_resources is None
                        else ", ".join(
                            [
                                "%s:%s" % tuple(kv)
                                for kv in self.scheduled_resources.items()
                            ]
                        ),
                    ),
                    ("color", "" if self.color is None else color_to_html(self.color)),
                ]
            ]
        )


class Resource:
    """Resources are machines/humans that can perform tasks.

    Parameters
    ----------

    name
      Name of the resource.

    full_name
      Full name of the resource.

    capacity
      How many jobs a resource can do at the same time.
    """

    def __init__(self, name, full_name=None, capacity=1):
        self.full_name = name if full_name is None else full_name
        self.name = name
        self.capacity = capacity

    def __repr__(self):
        return self.name

    def hash(self):
        return hash(self.name)

    def to_dict(self):
        return OrderedDict(
            [
                (k, "" if v is None else v)
                for k, v in [
                    ("resource_name", self.name),
                    ("full_name", self.full_name),
                    ("capacity", self.capacity),
                ]
            ]
        )


def numberjack_scheduler(
    tasks,
    upper_bound=500,
    lower_bound=None,
    optimize=True,
    time_limit=5,
    solver_method="Mistral",
    randomization=False,
    verbose_solver=False,
):
    """Makes an optimized schedule for the processes.

    Examples
    --------

    >>>
    >>>
    >>>
    >>>

    Parameters
    -----------

    tasks
      A list of tasks to be sceduled.

    upper_bound
      Upper bound for the time. The unit depends on the unit
      chosen for the duration of the work unit's tasks.

    optimize
      If false, any solution satisfying the constraints (including deadlines)
      will be returned. But sometimes it is not possible to respect all
      deadlines. If True, the function will try to return a schedule which
      minimizes the days over the deadlines. The function minimized is the sum
      of (wu.priority*wu.delay) for all work units with a due time.

    time_limit
      Time in seconds after which the optimizer stops. If the optimizer stops
      because of this time limit the solution may not be optimal.

    solver_method
      The solver used by NumberJack (see NumberJack docs).
    """

    ZERO = nj.Variable([0])
    C_LOWER_BOUND = 0

    # Create Numberjack variables to represent the tasks
    # ( starting times and resource instance that they use).
    tasks = [
        task
        for task in tasks
        if (
            (task.scheduled_start is None)
            or (
                (task.scheduled_start is not None)
                and (task.scheduled_start < upper_bound)
            )
            or (
                (task.scheduled_end is not None)
                and (lower_bound is not None)
                and (task.scheduled_end > lower_bound)
            )
        )
    ]
    nj_tasks = {}
    for task in tasks:

        if task.scheduled_start is None:
            if lower_bound is not None:
                new_nj_task = nj.Task(lower_bound, upper_bound, task.duration)
            else:
                new_nj_task = nj.Task(upper_bound, task.duration)
        else:
            new_nj_task = nj.Task(
                task.scheduled_start, task.scheduled_end, task.duration
            )
        new_nj_task.name = task.name
        nj_tasks[task] = new_nj_task

    nj_taskresources = {
        task: {
            resource: (
                # If a task is already scheduled to some slot, its slot is
                # one-choice variable. Otherwise it is a 1..nSlots variable
                nj.Variable(1, resource.capacity)
                if task.scheduled_resources is None
                else nj.Variable([task.scheduled_resources[resource]])
            )
            for resource in task.resources
        }
        for task in tasks
    }

    all_resources = list(
        set([resource for task in tasks for resource in task.resources])
    )

    model = nj.Model()

    for resource in all_resources:

        if resource.capacity == "inf":
            continue
        elif resource.capacity == 1:
            # The resource has one slot: Only one job at the same time
            model.add(
                nj.UnaryResource(
                    [nj_tasks[task] for task in tasks if (resource in task.resources)]
                )
            )
        else:
            # The resource has several slots
            tasks_pairs_sharing_resource = [
                (task, other_task)
                for (task, other_task) in itt.combinations(tasks, 2)
                if ((resource in task.resources) and (resource in other_task.resources))
            ]
            for (task, other_task) in tasks_pairs_sharing_resource:

                different_times = nj.Or(
                    [
                        nj_tasks[task] + task.duration <= nj_tasks[other_task],
                        nj_tasks[other_task] + other_task.duration < nj_tasks[task],
                    ]
                )
                different_resources = nj.AllDiff(
                    [
                        nj_taskresources[task][resource],
                        nj_taskresources[other_task][resource],
                    ]
                )
                different_resources.lb = 0
                different_resources.ub = 1
                model.add(nj.Or([different_times, different_resources]))

    model.add(
        [
            (nj_tasks[task] + task.duration <= nj_tasks[next_task])
            for next_task in tasks
            for task in next_task.follows
        ]
    )

    model.add(
        [
            (nj_tasks[next_task] <= nj_tasks[task] + task.duration + next_task.max_wait)
            for next_task in tasks
            for task in next_task.follows
            if next_task.max_wait is not None
        ]
    )

    if optimize:
        C_max = nj.Variable(C_LOWER_BOUND, 150000000, "C_max")
        model.add(
            C_max
            > sum(
                [
                    nj.Max([ZERO, nj_tasks[task] + task.duration - task.due_time])
                    * (1000 * task.priority)
                    for task in tasks
                    if task.due_time is not None
                ]
            )
            + sum([nj_tasks[task] for task in tasks])
        )

        # Specify that the goal is to minimize C_max (compress the schedule).
        model.add(nj.Minimize(C_max))

    else:
        model.add(
            [
                nj_tasks[task] + task.duration < task.due_time
                for task in tasks
                if task.due_time is not None
            ]
        )

    solver = model.load(solver_method)
    solver.setVerbosity(verbose_solver)
    solver.setTimeLimit(time_limit)
    solver.setRandomized(randomization)
    result = solver.solve()

    if result is False:
        raise ValueError("No solution found by the schedule optimizer !")

    for task in tasks:
        nj_task = nj_tasks[task]
        start = nj_task.get_value()
        resources = {
            resource: nj_taskresources[task][resource].get_value()
            for resource in task.resources
        }
        task.scheduled_start = start
        task.scheduled_resources = resources

    return tasks


def schedule_processes_series(
    processes,
    est_process_duration=5000,
    time_limit=20,
    verbose_solver=False,
    time_limit_step=0,
    scheduled_tasks=(),
    n_trials=2,
    logger=None,
):
    lower_bound = None
    process_duration = upper_bound = est_process_duration

    def schedule_tasks(tasks, upper_bound, lower_bound, time_limit, randomization):
        numberjack_scheduler(
            tasks,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            time_limit=time_limit,
            solver_method="Mistral",
            randomization=randomization,
            verbose_solver=verbose_solver,
        )

    considered_tasks = [copy(t) for t in scheduled_tasks]
    schedule_tasks(
        list(copy(processes[0])) + considered_tasks,
        upper_bound,
        lower_bound,
        time_limit,
        randomization=-1,
    )
    new_processes = []
    iterator = list(enumerate(processes))
    if logger is not None:
        iterator = logger.iter_bar(process=iterator)
    for i, process in iterator:
        new_tasks = copy(process)
        new_processes.append(new_tasks)
        considered_tasks += new_tasks
        for trial in range(n_trials):

            try:
                schedule_tasks(
                    considered_tasks,
                    upper_bound,
                    lower_bound,
                    time_limit + time_limit_step * trial,
                    randomization=0,
                )
                lower_bound = min([t.scheduled_start for t in new_tasks])
                latest = max([t.scheduled_end for t in new_tasks])
                process_duration = min(process_duration, latest - lower_bound)
                upper_bound = latest + est_process_duration
                break
            except ValueError as e:
                pass
        assert all([(t.scheduled_resources is not None) for t in considered_tasks])

    return new_processes
