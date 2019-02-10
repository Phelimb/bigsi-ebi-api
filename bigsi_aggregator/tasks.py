import requests
import json

from flask_celery import single_instance

from bigsi_aggregator.extensions import celery
from bigsi_aggregator.models import SequenceSearch


class BigsiClient:
    def __init__(self, url):
        self.base_url = url

    def search(self, seq, threshold, score):
        url = "{base_url}/search".format(base_url=self.base_url)
        results = requests.post(
            url,
            data={"seq": seq, "threshold": int(threshold) / 100, "score": int(score)},
        ).json()
        return results


@celery.task(name="search_bigsi_and_update_results")
def search_bigsi_and_update_results(url, sequence_search_id):
    print(url, sequence_search_id)
    sequence_search = SequenceSearch.get_by_id(sequence_search_id)
    bigsi_client = BigsiClient(url)
    bigsi_search_results = bigsi_client.search(
        sequence_search.seq, sequence_search.threshold, sequence_search.score
    )

    sequence_search.add_results(bigsi_search_results["results"])
