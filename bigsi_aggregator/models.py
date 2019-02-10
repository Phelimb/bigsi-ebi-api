import redis
import json
from bigsi_aggregator import constants

DEFAULT_SEARCH_RESULTS_TTL = 48 * 60 * 60  # 2 days


def generate_search_key(id):
    return "sequence_search:%s" % id


def generate_search_results_key(id):
    return "sequence_search_results:%s" % id


r = redis.StrictRedis(decode_responses=True)


class SequenceSearch:
    def __init__(
        self,
        seq,
        threshold,
        score,
        total_bigsi_queries,
        results=[],
        completed_bigsi_queries=0,
        ttl=DEFAULT_SEARCH_RESULTS_TTL,
    ):
        self.seq = seq
        self.threshold = threshold
        self.score = score
        self.total_bigsi_queries = total_bigsi_queries
        self.id = self.generate_id()
        self.ttl = ttl
        self.completed_bigsi_queries = completed_bigsi_queries
        self.results = results

    @classmethod
    def create(cls, seq, threshold, score, total_bigsi_queries):
        sequence_search = cls(seq, threshold, score, total_bigsi_queries)
        sequence_search.create_cache()
        sequence_search.set_ttl()
        return sequence_search

    @classmethod
    def get_by_id(cls, id):
        search_params = r.hgetall(generate_search_key(id))
        results = r.hgetall(generate_search_results_key(id))
        print(search_params, results)
        sequence_search = cls(**search_params, results=results)
        sequence_search.set_ttl()
        return sequence_search

    def __dict__(self):
        return {
            constants.SEQUENCE_QUERY_KEY: self.seq,
            constants.THRESHOLD_KEY: self.threshold,
            constants.SCORE_KEY: self.score,
            constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: self.completed_bigsi_queries,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: self.total_bigsi_queries,
            constants.RESULTS_KEY: self.results,
        }

    @property
    def search_key(self):
        return generate_search_key(self.id)

    @property
    def in_progress(self):
        return self.completed_bigsi_queries < self.total_bigsi_queries

    @property
    def search_results_key(self):
        return generate_search_results_key(self.id)

    def set_ttl(self, ttl=DEFAULT_SEARCH_RESULTS_TTL):
        r.expire(self.search_results_key, ttl)
        r.expire(self.search_key, ttl)

    def progress(self):
        return self.completed_bigsi_queries / self.total_bigsi_queries

    def create_cache(self):
        search_params_key = generate_search_key(self.id)
        r.hset(search_params_key, constants.SEQUENCE_QUERY_KEY, self.seq)
        r.hset(search_params_key, constants.THRESHOLD_KEY, self.threshold)
        r.hset(search_params_key, constants.SCORE_KEY, int(self.score))
        r.hset(search_params_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 0)
        r.hset(
            search_params_key,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY,
            self.total_bigsi_queries,
        )

    def generate_id(self):
        string = "{seq}{threshold}{score}{total_bigsi_queries}".format(
            seq=self.seq,
            threshold=self.threshold,
            score=int(self.score),
            total_bigsi_queries=self.total_bigsi_queries,
        )
        print(string, hash(string))
        return hash(string)

    def add_results(self, results):
        search_results_key = generate_search_results_key(self.id)
        for res in results:
            print(res)
            r.hset(self.search_results_key, res["sample_name"], json.dumps(res))
        self.incr_completed_queries()
        self.set_ttl()

    def incr_completed_queries(self):
        r.hincrby(self.search_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 1)
