import flask

from injectors import services

tasks_routers = flask.Blueprint(
    'tasks', __name__, url_prefix='/api/'
)


@tasks_routers.post('/tasks/')
def add_task():
    """."""
    ts = services.tasks_service()
    res = ts.create_task(flask.request.json)
    return flask.jsonify(res.dump())


@tasks_routers.get('/tasks/')
def get_tasks():
    """."""
    ts = services.tasks_service()
    res = ts.get_all()
    return flask.jsonify([obj.dump() for obj in res])


@tasks_routers.get('/tasks/<int:task_id>/')
def get_task(task_id):
    """."""
    ts = services.tasks_service()
    return flask.jsonify(ts.get(task_id).dump())
