from copy import copy
from tqdm import tqdm
import matplotlib.pyplot as plt
from egfscheduler import (
    Resource,
    Task,
    WorkUnit,
    numberjack_scheduler,
    plot_schedule,
    gap_constraints
)

human_operator = Resource("Human operator", capacity=1)
tecan_evo = Resource("Tecan EVO", capacity=2)
trobot = Resource("TRobot", capacity=5)
fragment_analyser = Resource("Fragment_analyser", capacity=1)
qpix = Resource("QPix", 1)
incubator = Resource("Incubator", 'inf')
shaker = Resource("Shaker", 2)


def yeastfab_workunit(name, due_time=None, priority=1, parents=None):
    return WorkUnit(
        name,
        tasks=[
            # Primers normalization
            Task('Primers norm.', [tecan_evo], 15),

            # PCR
            Task('PCR_prep', [tecan_evo], 15),
            Task('PCR', [trobot], 90),

            # Fragment analysis 1
            Task('FA_1_prep', [tecan_evo, human_operator], 15),
            Task('FA_1', [fragment_analyser], 80),

            # Golden Gate ligation
            Task('Golden_Gate_mix', [tecan_evo], 15),
            Task('Golden_Gate_incub', [trobot], 48),

            # Transformation
            Task('Transfo', [tecan_evo], 30),
            Task('Regeneration', [shaker], 120),

            # Incubation
            Task('Incubation', [incubator], 960),

            # Colony Picking
            Task('Colony picking', [qpix], 45),

            # Colony PCR
            Task('Colony_PCR_prep', [tecan_evo], 15),
            Task('Colony_PCR', [trobot], 3 * 90),

            # Fragment analysis 2
            Task('FA_2_prep', [tecan_evo, human_operator], 15),
            Task('FA_2', [fragment_analyser], 80),

            # Miniprep
            Task('Miniprep', [tecan_evo], 60),


            # Sequencing Reaction
            Task('sequencing_reaction_prep', [tecan_evo], 15),
            Task('sequencing_reaction', [trobot], 180)

        ],

        constraints=[
            gap_constraints('PCR_prep', 'PCR', max_gap=10),
            gap_constraints('Transfo', 'Regeneration', max_gap=10),
            gap_constraints('Colony_PCR_prep', 'Colony_PCR', max_gap=10),
            gap_constraints('FA_2_prep', 'FA_2', max_gap=10)

        ],

        due_time=due_time,
        priority=priority,
        parents=parents
    )

N_workunits = 20


workunits = [
    yeastfab_workunit("WU %d" % i)
    for i in range(N_workunits)
]

considered_workunits = []

print ("Now placing the tasks one by one")

for workunit in tqdm(workunits):
    workunit_copy = copy(workunit)
    considered_workunits.append(workunit_copy)
    for i in range(10):
        try:
            numberjack_scheduler(
                considered_workunits,
                upper_bound=2000*(i+1),
                time_limit=20
            )
            break
        except:
            pass

print ("The scheduling is done !")
fig, ax = plot_schedule(considered_workunits)
plt.show()
