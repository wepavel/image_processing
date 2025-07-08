"""."""
import os
import sys

if __name__ == '__main__':
    sys.path.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    )
    from injectors import connections

    connections.pg.init_db()
    from injectors import services

    print(f'Worker started on {os.getpid()}')
    services.tasks_mule().run()
