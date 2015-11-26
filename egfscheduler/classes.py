import itertools as itt
import numpy as np

import Numberjack as nj

tasks_counter = itt.count()
work_units_counter = itt.count()


class WorkUnit:
    """ A work unit is a series of task

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