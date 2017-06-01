from taskpacker import (get_process_from_spreadsheet,
                        get_resources_from_spreadsheet,
                        schedule_processes_series,
                        plot_tasks_dependency_graph,
                        plot_schedule, Task)
import os
import matplotlib.cm as cm

ALLOW_BREAKS = True

colors = (cm.Paired(0.21 * i % 1.0) for i in range(30))


# LOAD THE PROCESS AND RESOURCES CONFIGURATIONS

spreadsheet_path = os.path.join("examples_data", "dna_assembly.xls")

resources = get_resources_from_spreadsheet(spreadsheet_path=spreadsheet_path,
                                           sheetname="resources")

processes = [
    get_process_from_spreadsheet(spreadsheet_path=spreadsheet_path,
                                 sheetname="process",
                                 resources_dict=resources,
                                 tasks_color=next(colors),
                                 task_name_prefix="WU%d_" % (i + 1))
    for i in range(20)
]


# CREATE THE BREAKS

if ALLOW_BREAKS:
    scheduled_breaks = [
        Task("break_%03d" % i,
             resources=[resources["igor"]],
             scheduled_resource={resources["igor"]: 1},
             duration=12 * 60, scheduled_start=24 * 60 * i,
             color='white')
        for i in range(6)
    ]
else:
    scheduled_breaks = []


# OPTIMIZE THE SCHEDULE

print("NOW OPTIMIZING THE SCHEDULE, BE PATIENT...")
new_processes = schedule_processes_series(
    processes, est_process_duration=5000, time_limit=5,
    scheduled_tasks=scheduled_breaks
)


# PLOT THE TASKS DEPENDENCY TREE

ax = plot_tasks_dependency_graph(processes[0])
ax.set_title("PLAN OF A PROCESS")
ax.figure.savefig("dna_assembly_process.pdf", bbox_inches="tight")


# PLOT THE OPTIMIZED SCHEDULE

all_tasks = [t for process in new_processes for t in process] + scheduled_breaks
fig, ax = plot_schedule(all_tasks)
ax.figure.set_size_inches((10, 5))
ax.set_xlabel("time (min)")
figure_name = "dna_assembly" + ("_with_breaks" if ALLOW_BREAKS else "")
ax.figure.savefig(figure_name + ".png", bbox_inches="tight")
