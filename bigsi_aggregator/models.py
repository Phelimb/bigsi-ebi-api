import redis
import json
from bigsi_aggregator import constants
from bigsi_aggregator.settings import REDIS_IP

import hashlib

DEFAULT_SEARCH_RESULTS_TTL = 48 * 60 * 60  # 2 days


def generate_search_key(_id):
    return "sequence_search:%s" % _id


def generate_search_results_key(_id):
    return "sequence_search_results:%s" % _id


r = redis.StrictRedis(REDIS_IP, decode_responses=True)

# class SequenceSearchResult:
#      def __init__(self, percent_kmers_found, ):
#           self.percent_kmers_found=percent_kmers_found
#           self.num_kmers=percent_kmers_found
#           self.num_kmers_found=percent_kmers_found
#           self.sample_name=percent_kmers_found


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
        self.score = bool(int(score))
        self.total_bigsi_queries = total_bigsi_queries
        self._id = self.generate_id()
        self.ttl = ttl
        self.completed_bigsi_queries = completed_bigsi_queries
        self.results = results

    @classmethod
    def create(cls, seq, threshold, score, total_bigsi_queries):
        sequence_search = cls(seq, threshold, score, total_bigsi_queries)
        if r.exists(generate_search_key(sequence_search.id)):
            return cls.get_by_id(sequence_search.id)
        else:
            sequence_search.create_cache()
            sequence_search.set_ttl()
        return sequence_search

    @classmethod
    def get_by_id(cls, _id):
        search_params = r.hgetall(generate_search_key(_id))
        results = r.hgetall(generate_search_results_key(_id))
        results = [json.loads(s) for s in results.values()]
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
    def id(self):
        return self._id

    @property
    def in_progress(self):
        return self.completed_bigsi_queries < self.total_bigsi_queries

    @property
    def search_results_key(self):
        return generate_search_results_key(self.id)

    @property
    def status(self):
        if self.completed_bigsi_queries < self.total_bigsi_queries:
            return "INPROGRESS"
        else:
            return "COMPLETE"

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
        _hash = hashlib.sha224(string.encode("utf-8")).hexdigest()[:24]
        return _hash

    def add_results(self, results):
        search_results_key = generate_search_results_key(self.id)
        for res in results:
            r.hset(self.search_results_key, res["sample_name"], json.dumps(res))
        self.incr_completed_queries()
        self.set_ttl()

    def incr_completed_queries(self):
        r.hincrby(self.search_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 1)
