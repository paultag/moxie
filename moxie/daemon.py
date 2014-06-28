
"""
OK. So, there's some method here. Here are the core concepts:

    needs-run  = needs to be run. We're overdue. Needs to run *now*.
                 + reap the process (ensure it has been reaped)
                 + start the build, put into running state
    running    = Something that is currently running.
                 + wait it out. put into reapable state.
    reapable   = Something that needs to be recorded as finished.
                 + record exit status
                 + dump logs


         +--- ensure --+
         v             |
       [REAPED] -> [RUNNING]
         ^             |
         |           (lag)
         |             |
         +-------- [REAPABLE]
"""


def reap(container):
    """
    Clean up the container, write the log out, save the status.
    """
    pass


def wait(container):
    """
    Wait for the right time to run a container, then wait for it
    to finish. This is the sleepy-state.
    """
    pass


def start(container):
    """
    Start up the container for the job. Write the state back to the
    DB.
    """
    pass


def up(job):
    """
    Establish state. Enter state at the right point. Handle failure
    gracefully. Write new state back to DB.
    """
    pass


def main():
    """
    Start an `up` coroutine for each job.
    """
    pass
