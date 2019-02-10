from flask import Flask
from flask_restful import Api
from bigsi_aggregator.extensions import celery
from bigsi_aggregator.views import SequenceSearchListResource
from bigsi_aggregator.views import SequenceSearchResource
from bigsi_aggregator.settings import REDIS_IP

app = Flask(__name__)
api = Api(app)

api.add_resource(SequenceSearchListResource, "/searches/")
api.add_resource(SequenceSearchResource, "/searches/<sequence_search_id>")


app.config.update(
    CELERY_BROKER_URL="redis://{redis_ip}:6379/1".format(redis_ip=REDIS_IP),
    CELERY_RESULT_BACKEND="redis://{redis_ip}:6379/1".format(redis_ip=REDIS_IP),
    CELERY_TRACK_STARTED=True,
    CELERY_SEND_EVENTS=True,
)
celery.init_app(app)

if __name__ == "__main__":
    app.run(debug=True)
