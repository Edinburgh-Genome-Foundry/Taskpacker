"""Basic scheduling example.

Two labbies have been assigned a list of chores.
Alice will visit the GMO plants, cook the hamsters, and feed the gremlins.
Bob will clean the scalpels, dice the hamsters once they are cooked, then
assist Alice in gremlins feeding (a task that takes two people).
Alice has a stereotypical predisposition to multitasking: she can do 2 jobs at
the same time, while Bob can't.

When will they do each of their tasks ?
"""

from taskpacker import Task, Resource, numberjack_scheduler, plot_schedule
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
feed_gremlins = Task("Feed the gremlins", resources=[alice, bob], duration=50,
                     color="orange", follows=[dice_hamsters])


all_tasks = [clean_scalpels, visit_plants, cook_hamsters, dice_hamsters,
             feed_gremlins]
scheduled_tasks = numberjack_scheduler(all_tasks)
fig, ax = plot_schedule(scheduled_tasks)
ax.figure.set_size_inches(7, 3)
ax.figure.savefig("alice_and_bob.png", bbox_inches="tight")
