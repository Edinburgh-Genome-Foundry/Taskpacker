"""Basic tests.

And I mean reeeaaaally basic, I'm just making sure the main example runs here.
That's because the project is still experimental and "expected behavior" is
a very fluid concept at this time.
"""

from taskpacker import (get_work_unit_from_spreadsheet,
                        get_resources_from_spreadsheet,
                        schedule_processes_series,
                        plot_tasks_dependency_graph,
                        plot_schedule)
import os
import matplotlib.cm as cm

def test_dna_assembly_example(tmpdir):

    spreadsheet_path = os.path.join('examples', 'examples_data',
                                    "dna_assembly.xls")

    colors = (cm.Paired(0.21 * i % 1.0) for i in range(30))

    resources = get_resources_from_spreadsheet(
       spreadsheet_path=spreadsheet_path, sheetname="resources")

    workunits = [
        get_work_unit_from_spreadsheet(spreadsheet_path=spreadsheet_path,
                                       sheetname="process",
                                       resources_dict=resources,
                                       tasks_color=next(colors),
                                       task_name_prefix="WU%d_" % (i + 1))
        for i in range(5)
    ]

    print("NOW OPTIMIZING THE SCHEDULE, BE PATIENT...")
    new_workunits = schedule_processes_series(
        workunits, est_workunit_duration=5000, time_limit=6)

    # PLOT THE TASKS DEPENDENCY TREE
    ax = plot_tasks_dependency_graph(workunits[0])
    ax.set_title("PLAN OF A WORK UNIT")
    ax.figure.savefig("basic_example_work_unit.pdf", bbox_inches="tight")

    # PLOT THE OPTIMIZED SCHEDULE
    fig, ax = plot_schedule([t for workunit in new_workunits for t in workunit])
    ax.figure.set_size_inches((8, 5))
    ax.set_xlabel("time (min)")
    ax.figure.savefig(os.path.join(tmpdir, "basic_example_schedule.png"),
                      bbox_inches="tight")

def test_alice_and_bob(tmpdir):

    spreadsheet_path = os.path.join('examples', 'examples_data',
                                    "96_assembly_workunit.xls")

    colors = (cm.Paired(0.21 * i % 1.0) for i in range(30))

    resources = get_resources_from_spreadsheet(
       spreadsheet_path=spreadsheet_path, sheetname="Resources")

    workunits = [
        get_work_unit_from_spreadsheet(spreadsheet_path=spreadsheet_path,
                                       sheetname="process",
                                       resources_dict=resources,
                                       tasks_color=next(colors),
                                       task_name_prefix="WU%d_" % (i + 1))
        for i in range(20)
    ]

    print("NOW OPTIMIZING THE SCHEDULE, BE PATIENT...")
    new_workunits = schedule_processes_series(
        workunits, est_workunit_duration=5000, time_limit=6)

    # PLOT THE TASKS DEPENDENCY TREE
    ax = plot_tasks_dependency_graph(workunits[0])
    ax.set_title("PLAN OF A WORK UNIT")
    ax.figure.savefig("basic_example_work_unit.pdf", bbox_inches="tight")

    # PLOT THE OPTIMIZED SCHEDULE
    fig, ax = plot_schedule([t for workunit in new_workunits for t in workunit])
    ax.figure.set_size_inches((8, 5))
    ax.set_xlabel("time (min)")
    ax.figure.savefig(os.path.join(tmpdir, "basic_example_schedule.png"),
                      bbox_inches="tight")
