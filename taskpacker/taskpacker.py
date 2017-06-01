import uuid
from tqdm import tqdm
import Numberjack as nj
import itertools as itt
from copy import copy


class Task:
    """ Tasks are the steps of a work unit, performed using specific resources.

    Parameters
    ----------

    name
      Name of the task (appears when printed and plotted)

    resources
      list of Resource objects specifying the resources occupied by the task

    duration
      Duration of the task (the choice of the unit is left to the user.

    """

    def __init__(self, name, resources, duration, follows=(), max_wait=None,
                 scheduled_start=None, scheduled_resource=None,
                 priority=1, due_time=None, color='blue'):

        self.resources = resources
        self.duration = duration
        self.name = name
        self.scheduled_start = scheduled_start
        self.scheduled_resource = scheduled_resource
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


class Resource:
    """Resources are machines/humans that can perform tasks

    Parameters
    ----------

    """

    def __init__(self, name, full_name=None, capacity=1):
        self.full_name = name if full_name is None else full_name
        self.name = name
        self.capacity = capacity

    def __repr__(self):
        return self.name

    def hash(self):
        return hash(self.name)


def numberjack_scheduler(tasks, upper_bound=500,
                         lower_bound=None,
                         optimize=True, time_limit=5,
                         solver_method="Mistral",
                         randomization=False,
                         verbose_solver=False):
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
      A list of tasks to be sceduled

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
    nj_tasks = {}
    for task in tasks:

        if task.scheduled_start is None:
            if lower_bound is not None:
                new_nj_task = nj.Task(lower_bound, upper_bound, task.duration)
            else:

                new_nj_task = nj.Task(upper_bound, task.duration)
        else:
            new_nj_task = nj.Task(
                task.scheduled_start,
                task.scheduled_end,
                task.duration
            )
        new_nj_task.name = task.name
        nj_tasks[task] = new_nj_task

    nj_taskresources = {
        task: {
            resource: (
                # If a task is already scheduled to some slot, its slot is
                # one-choice variable. Otherwise it is a 1..nSlots variable
                nj.Variable(1, resource.capacity)
                if task.scheduled_resource is None else
                nj.Variable([task.scheduled_resource[resource]])
            )
            for resource in task.resources
        }
        for task in tasks
    }

    all_resources = list(set([
        resource
        for task in tasks
        for resource in task.resources
    ]))

    model = nj.Model()

    for resource in all_resources:

        if resource.capacity == 'inf':
            continue
        elif resource.capacity == 1:
            # The resource has one slot: Only one job at the same time
            model.add(nj.UnaryResource([
                nj_tasks[task] for task in tasks
                if (resource in task.resources)
            ]))
        else:
            # The resource has several slots
            tasks_pairs_sharing_resource = [
                (task, other_task)
                for (task, other_task) in itt.combinations(tasks, 2)
                if ((resource in task.resources) and
                    (resource in other_task.resources))
            ]
            for (task, other_task) in tasks_pairs_sharing_resource:
                model.add(nj.Or([
                    nj.Or([
                        nj_tasks[task] + task.duration <= nj_tasks[other_task],
                        nj_tasks[other_task] + other_task.duration <=
                        nj_tasks[task]
                    ]),
                    nj.AllDiff([
                        nj_taskresources[task][resource],
                        nj_taskresources[other_task][resource]
                    ])
                ]))

    model.add([
        (nj_tasks[task] + task.duration <= nj_tasks[next_task])
        for next_task in tasks
        for task in next_task.follows
    ])

    model.add([
        (nj_tasks[next_task] <= nj_tasks[task] +
         task.duration + next_task.max_wait)
        for next_task in tasks
        for task in next_task.follows
        if next_task.max_wait is not None
    ])

    if optimize:
        C_max = nj.Variable(C_LOWER_BOUND, 150000000, 'C_max')
        model.add(
            C_max >
            sum([
                nj.Max([ZERO, nj_tasks[task] +
                        task.duration -
                        task.due_time]) *
                (1000 * task.priority)
                for task in tasks
                if task.due_time is not None
            ]) +
            sum([
                nj_tasks[task]
                for task in tasks
            ])
        )

        # Specify that the goal is to minimize C_max (compress the schedule).
        model.add(nj.Minimize(C_max))

    else:
        model.add([
            nj_tasks[task] + task.duration < task.due_time
            for task in tasks
            if task.due_time is not None
        ])

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
        resources = {resource: nj_taskresources[task][resource].get_value()
                     for resource in task.resources}
        task.scheduled_start = start
        task.scheduled_resource = resources

    return tasks


def schedule_processes_series(processes, est_process_duration=5000,
                              time_limit=20, verbose_solver=False,
                              scheduled_tasks=(), n_trials=2):
    lower_bound = None
    process_duration = upper_bound = est_process_duration

    def schedule_tasks(tasks, upper_bound, lower_bound, time_limit,
                       randomization):
        numberjack_scheduler(
            tasks,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            time_limit=time_limit,
            solver_method="Mistral",
            randomization=randomization,
            verbose_solver=verbose_solver
        )

    considered_tasks = [copy(t) for t in scheduled_tasks]
    schedule_tasks(list(copy(processes[0])) + considered_tasks,
                   upper_bound, lower_bound, time_limit,
                   randomization=-1)
    new_processes = []
    for i, process in tqdm(list(enumerate(processes)), desc="#Process"):
        for trial in range(n_trials):
            new_tasks = copy(process)
            new_processes.append(new_tasks)
            considered_tasks += new_tasks
            try:
                schedule_tasks(considered_tasks, upper_bound, lower_bound,
                               time_limit, randomization=0)
                lower_bound = min([t.scheduled_start for t in new_tasks])
                latest = max([t.scheduled_end for t in new_tasks])
                process_duration = min(process_duration, latest - lower_bound)
                upper_bound = 2 * latest
                break
            except ValueError:
                upper_bound *= 2

    return new_processes
