import itertools as itt

tasks_counter = itt.count()
work_units_counter = itt.count()


class WorkUnit:
    """ A work unit is a series of task with precedence constraints.

    A work unit represents a series of operations that must be done
    at a factory as part of a project. It can have a due time (deadline for
    an order), parents (work units whose completion allows this wor unit),
    a priority. Lists of work units can be planned by a scheduler.

    Parameters
    ----------

    name (str)
      Name of the work unit (that will appear e.g. on plotted schedules)

    tasks (list)
      List of Tasks in the order in which they should be performed for the
      work unit.

    constraints (list)
      Additional constraints on the Tasks. Constraints should be given in
      the form lambda (tasks_list): tasks_list[4] < tasks_list[3] + 100
      to express that task 5 should start at most 100 time-units after the
      start of task 4.

    parents (list)
      Work units that must be completed before the first task of this work
      unit starts

    due_time (int)
      Time at which the work unit is due. Depending on the scheduling
      algorithm, this will be interpreted either as a hard constraint,
      or as an objective (minimize priority * due_time)

    priority (int)
      Integer. The higher the priority the more the due_time of this
      work unit will be taken into account in an optimized schedule.

    scheduled_start
      Hard constraint indicating a fixed time for the start of this work
      unit.


    """

    def __init__(self, name, tasks, constraints=None, parents=None,
                 due_time=None, priority=1, scheduled_start=None):
        self.tasks = tasks
        self.name = name
        self.id = work_units_counter.next()
        self.constraints = [] if constraints is None else constraints
        self.parents = [] if parents is None else parents
        self.due_time = due_time
        self.priority = priority
        self.scheduled_start = scheduled_start


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
    def __init__(self, name, resources, duration):

        self.resources = resources
        self.duration = duration
        self.name = name
        self.id = tasks_counter.next()

    def __repr__(self):
        return "Task(%(id)d, %(name)s, %(duration)s)" % self.__dict__

    def __hash__(self):
        return self.id


class Resource:
    """Resources are machines/humans that can perform tasks

    Parameters
    ----------

    """

    def __init__(self, name, capacity=1):
        self.name = name
        self.capacity = capacity

    def __repr__(self):
        return self.name
