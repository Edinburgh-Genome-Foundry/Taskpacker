"""
Code that is only really useful for the examples.
"""

import itt
from .classes import Task, WorkUnit, Resource


foundry = Resource("foundry")


def make_jobs_tree(levels=3, level_width=10, order_due_time=100):

    def generator():
        counter = itt.count()
        for i in counter:
            yield WorkUnit(name="asm(%d)" % (i),
                           tasks=[Task("asm", foundry, 4)])
    job_generator = generator()
    order_job = job_generator.next()
    order_job.steps_to_order = 0
    order_job.due_time = order_due_time
    order_job.order_due_time = order_due_time
    jobs_levels = [[order_job]]

    for level in range(levels):
        jobs_levels.append([])
        for child in jobs_levels[level]:
            new_jobs = [job_generator.next() for i in range(level_width)]
            for job in new_jobs:
                job.steps_to_order = level+1
                job.order_due_time = order_due_time

            child.parents = new_jobs
            jobs_levels[level+1].extend(new_jobs)
    return jobs_levels
