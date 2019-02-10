from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from bigsi_aggregator.views import SequenceSearch

app = Flask(__name__)
api = Api(app)

api.add_resource(SequenceSearch, "/searches/<string:search_result_id>")

if __name__ == "__main__":
    app.run(debug=True)
