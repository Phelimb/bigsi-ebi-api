from flask import Flask
from flask_restful import Api
from celery import Celery

from bigsi_aggregator.views import SequenceSearchListResource
from bigsi_aggregator.views import SequenceSearchResource

app = Flask(__name__)
api = Api(app)

api.add_resource(SequenceSearchListResource, "/searches/")
api.add_resource(SequenceSearchResource, "/searches/<sequence_search_id>")


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


app.config.update(
    CELERY_BROKER_URL="redis://localhost:6379",
    CELERY_RESULT_BACKEND="redis://localhost:6379",
)
celery = make_celery(app)


if __name__ == "__main__":
    app.run(debug=True)
