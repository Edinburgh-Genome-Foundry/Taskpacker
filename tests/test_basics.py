"""Basic tests.

And I mean reeeaaaally basic, I'm just making sure the main example runs here.
That's because the project is still experimental and "expected behavior" is
a very fluid concept at this time.
"""

from taskpacker import (tasks_from_spreadsheet,
                        resources_from_spreadsheet,
                        schedule_processes_series,
                        plot_tasks_dependency_graph,
                        plot_schedule, Task, Resource,
                        numberjack_scheduler)
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.cm as cm


def test_dna_assembly_example(tmpdir):

    spreadsheet_path = os.path.join('examples', 'examples_data',
                                    "dna_assembly.xls")

    colors = (cm.Paired(0.21 * i % 1.0) for i in range(30))

    resources = resources_from_spreadsheet(
        spreadsheet_path=spreadsheet_path, sheetname="resources")

    processes = [
        tasks_from_spreadsheet(spreadsheet_path=spreadsheet_path,
                               sheetname="process",
                               resources_dict=resources,
                               tasks_color=next(colors),
                               task_name_prefix="WU%d_" % (i + 1))
        for i in range(5)
    ]

    print("NOW OPTIMIZING THE SCHEDULE, BE PATIENT...")
    new_processes = schedule_processes_series(
        processes, est_process_duration=5000, time_limit=6)

    # PLOT THE TASKS DEPENDENCY TREE
    ax = plot_tasks_dependency_graph(processes[0])
    ax.set_title("PLAN OF A WORK UNIT")
    ax.figure.savefig("basic_example_work_unit.pdf", bbox_inches="tight")

    # PLOT THE OPTIMIZED SCHEDULE
    ax = plot_schedule([t for process in new_processes for t in process])
    ax.figure.set_size_inches((8, 5))
    ax.set_xlabel("time (min)")
    ax.figure.savefig(os.path.join(str(tmpdir),
                                   "basic_example_schedule.png"),
                      bbox_inches="tight")


def test_alice_and_bob():

    alice = Resource("Alice", capacity=2)
    bob = Resource("Bob", capacity=1)

    clean_scalpels = Task("Clean the scalpels", resources=[bob], duration=20,
                          color="white")
    visit_plants = Task("Visit the plants", resources=[alice], duration=60,
                        color="yellow")
    cook_hamsters = Task("Cook the hamsters", resources=[alice], duration=30,
                         color="red")
    dice_hamsters = Task("Dice the hamsters", resources=[bob], duration=40,
                         color="blue", follows=[cook_hamsters, clean_scalpels])
    feed_gremlins = Task("Feed the gremlins", resources=[alice, bob],
                         duration=50,
                         color="orange", follows=[dice_hamsters])

    all_tasks = [clean_scalpels, visit_plants, cook_hamsters, dice_hamsters,
                 feed_gremlins]
    scheduled_tasks = numberjack_scheduler(all_tasks)
