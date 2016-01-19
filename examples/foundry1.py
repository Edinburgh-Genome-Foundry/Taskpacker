""" EGFScheduler example 1

"""

from egfscheduler import (Resource, Task, WorkUnit,
                          numberjack_scheduler, plot_schedule)

human_operator = Resource("Human operator", capacity=1)
tecan_evo = Resource("Tecan EVO", capacity=1)
trobot = Resource("TRobot", capacity=3)  # <= We have 3 TRobots
fragment_analyser = Resource("Fragment_analyser")


def assembly_workunit(name, due_time=None, priority=1, parents=None):
    return WorkUnit(name,
                    tasks=[
                        Task('prepare samples', [human_operator], 10),
                        Task('mix', [tecan_evo], 5),
                        Task('tpcr', [trobot], 15),
                        Task('gel prep', [tecan_evo], 5),
                        Task('gel assay',
                             [fragment_analyser, human_operator], 20),
                        Task('sorting', [tecan_evo], 10)
                    ],
                    constraints=[
                        lambda tasks: (
                            tasks[1] < tasks[0] + tasks[0].duration + 20),
                        lambda tasks: (
                            tasks[2] < tasks[1] + tasks[1].duration + 20)
                    ],
                    due_time=due_time,
                    priority=priority,
                    parents=parents
                    )

wu_1a = assembly_workunit("WU 1a")
wu_1b = assembly_workunit("WU 1b", parents=[wu_1a])

wu_2a = assembly_workunit("WU 2a")
wu_2b = assembly_workunit("WU 2b", parents=[wu_2a])

wu_3 = assembly_workunit("WU 3", parents=[wu_1b, wu_2b], due_time=300)

wu_lunch = WorkUnit("Lunch",
                    [Task("Lunch", resources=[human_operator], duration=100)],
                    scheduled_start=100)

wus = [wu_1a, wu_1b, wu_2a, wu_2b, wu_3, wu_lunch]
numberjack_scheduler(wus, upper_bound=400, time_limit=60)
print ("The scheduling is done !")

try:
    import matplotlib.pyplot as plt
    fig, ax = plot_schedule(wus)
    plt.show()
except:
    print("Error: printing the schedule requires maplotlib installed")

