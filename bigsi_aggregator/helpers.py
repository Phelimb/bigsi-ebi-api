from bigsi_aggregator.tasks import search_bigsi_and_update_results


class BigsiAggregator:
    def __init__(self, bigsi_urls):

        self.bigsi_urls = bigsi_urls

    def search_and_aggregate(self, sequence_search):
        for url in self.bigsi_urls:
            result = search_bigsi_and_update_results.delay(url, sequence_search.id)
