.. raw:: html

    <p align="center">
    <img alt="Taskpacker Logo" title="Taskpacker Logo" src="https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/Taskpacker/master/docs/_static/images/title.png" width="600">
    <br /><br />
    </p>

Taskpacker is a generic schedule optimization and visualization library for Python.
For instance, below is an optimized schedule where 20 processes (each comprised of several tasks and represented by one color) are ran 24/7 in a factory:

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/Taskpacker/master/examples/dna_assembly.png
 :alt: [dna_assembly.png]
 :align: center
 :width: 600px

Such plots enable you to spot the bottlenecks of your factory. In this example,
it appears that ovens are the limiting elements (the only machines packed full
with no downtime) and that buying a third oven will increase your factory's
throughput.

Main features
--------------

Taskpacker was built as a toy project to have an easily-extensible scheduling tool in Python.
Only Python2 is supported right now (sorry for that, there is a complex bug with Numberjack in Python3).
It is pretty simple and limited (the core code is ~200 lines) but comes with enough features to cover many cases:

- Supports resources (typically, people or robots) and resource capacity
  (= how much jobs a resource can do at the same time)
- Supports tasks dependencies (some tasks must be finished before other tasks
  can be started) and maximum waiting time (i.e. some tasks must be started at the
  latest X minutes after their *parents* are completed)
- Supports pre-scheduled tasks (such as breaks for human operators, scheduled robotic maintenance etc.)

Work in progress - contribute !
------------------------------------------

Taskpacker is an open-source software originally written to optimize the robot-operated DNA assembly operations at the `Edinburgh Genome Foundry <http://www.genomefoundry.io>`_. It is `released on Github <https://github.com/Edinburgh-Genome-Foundry/plateo>`_
under the MIT licence (¢ Edinburgh Genome Foundry), with no warranties: this is
an experimental piece of software which we hope will be as useful for you as it was for us.
And everyone is welcome to contribute !

Installation
--------------

Taskpacker can be installed by unzipping the source code in one directory and using this command: ::

    sudo python setup.py install

You can also install it directly from the Python Package Index with this command: ::

    sudo pip taskpacker install

It is probable that you will need some dependencies to build Numberjack. On Ubuntu you can install these with: ::

    sudo apt install libxml2-dev swig

Basic Example
--------------

In this example two labbies have been assigned a list of chores.
Alice will visit the GMO plants, cook the hamsters, and feed the gremlins.
Bob will clean the scalpels, dice the hamsters once they are cooked, then
assist Alice in gremlins feeding (a task that takes two people).
Certain tasks can only be done after other tasks have been completed.
Alice has a stereotypical predisposition to multitasking: she can do 2 jobs at
the same time, while Bob can't.

Here is how you would use Taskpacker to find when they will do each task so as
to finish as early as possible:

.. code:: python

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
    ax.figure.savefig("alice_and_bod.png", bbox_inches="tight")

Modeling tasks and reources with spreadsheets
---------------------------------------------

Assume that you have a process consisting in several tasks, each task depending
on some resources to be available, and possibly on other tasks. Such process can
be summarized in a spreadsheet like this one `this file <>`_, which is loaded in
Taskpacker as follows:

.. code:: python

    from taskpacker import (get_resources_from_spreadsheet,
                            get_process_from_spreadsheet)

    resources = get_resources_from_spreadsheet(
        spreadsheet_path="path/to/spreadsheet.xls", sheetname="resources")

    process_tasks = get_process_from_spreadsheet(
        spreadsheet_path="path/to/spreadsheet.xls",
        sheetname="process",
        resources_dict=resources
    )


Then you can for instance plot the dependency graph of the tasks:

.. code:: python

    from taskpacker import plot_tasks_dependency_graph
    plot_tasks_dependency_graph(process_tasks)

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/Taskpacker/master/docs/_static/images/process_plan.png
   :alt: [logo]
   :align: center
   :width: 600px

Or simply schedule the tasks:

.. code:: python

    from taskpacker import numberjack_scheduler
    scheduled_tasks = numberjack_scheduler(process_tasks)


Throughput estimations
-----------------------

Given a list of tasks forming a process, you might ask "how many of these processes
can my factory run in a day ?". The following code loads 20 of these processes
and asks Taskpacker to stack them one by one as compactly as possible:

.. code:: python

    from taskpacker import (get_process_from_spreadsheet,
                            get_resources_from_spreadsheet,
                            schedule_processes_series,
                            plot_tasks_dependency_tree,
                            plot_schedule, Task)
    import matplotlib.cm as cm


    colors = [cm.Paired(0.21 * i % 1.0) for i in range(30)]

    resources = get_resources_from_spreadsheet(
        spreadsheet_path="path/to/spreadsheet.xls", sheetname="resources")

    processes = [
        get_process_from_spreadsheet(spreadsheet_path="path/to/spreadsheet.xls",
                                     sheetname="process",
                                     resources_dict=resources,
                                     tasks_color=colors[i],
                                     task_name_prefix="WU%d_" % (i + 1))
        for i in range(20)
    ]

    # OPTIMIZE THE SCHEDULE
    new_processes = schedule_processes_series(
        processes, est_process_duration=5000, time_limit=5)

    # PLOT THE OPTIMIZED SCHEDULE

    all_tasks = [t for process in new_processes for t in process]
    fig, ax = plot_schedule(all_tasks)
    ax.set_xlabel("time (min)")
    ax.figure.savefig("dna_assembly_schedule.png", bbox_inches="tight")

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/Taskpacker/master/examples/dna_assembly.png
 :alt: [dna_assembly.png]
 :align: center
 :width: 600px

Note that it is also possible to add scheduled breaks (here we make them appear as white rectangles) so that your Igor can rest:

.. code:: python

    scheduled_breaks = [
        Task("break_%03d" % i,
             resources=[resources["igor"]],
             scheduled_resource={resources["igor"]: 1},
             duration=12 * 60, # The break lasts 12H
             scheduled_start=24 * 60 * i, # The break happens every 24H
             color='white')
        for i in range(6)
    ]

    new_processes = schedule_processes_series(
        processes, est_process_duration=5000, time_limit=5,
        scheduled_tasks=scheduled_breaks)

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/Taskpacker/master/examples/dna_assembly_with_breaks.png
 :alt: [dna_assembly_with_breaks.png]
 :align: center
 :width: 600px
