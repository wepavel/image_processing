"""."""

import flask

import routers
from base_sync.base_module import ModuleException


def setup_app():
    current = flask.Flask(__name__)

    return current


app = setup_app()
app.register_blueprint(routers.tasks_routers)


@app.errorhandler(ModuleException)
def handle_app_exception(e: ModuleException):
    """."""
    if e.code == 500:
        import traceback
        traceback.print_exc()
    return flask.jsonify(e.json()), e.code


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8001,
    )
