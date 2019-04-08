# Repository for the EBI BIGSI query service API 

The architecture of this project involve an array of individual BIGSI servers with once process per index. 


This service will query each of these BIGSIs via HTTP requests, aggregate the results and combine with EBI metadata. 

It would be possible to design this in such a way that the BIGSI indexes were all controlled by this service. However, this would mean all BIGSIs would need to be on the filesystem. With this architecture, there is no requirement for the indexes to be on the same filesystem, provided they're available via a network. 

As a result, initialising this service requires a list of IP address for each of the BIGSI APIs. These are updatable via an ENV variable.

This API only provides read-only access to the `search` endpoint, creation and updating of the indexes are managed manually.

Queries create a backgroud task which query all the BIGSIs in the array. The results are aggregated and cached in redis for 48 hours and are given a unique endpoint to lookup results. This URL can be polled to get the latests results. 

### Create a BIGSI service for each of the INDEXes


```
## Volume mounts
kubectl create -f k8/bigsi-services/bigsi-1/pv-volume.yaml ## This needs to be updated to use a local path! 
kubectl create -f k8/bigsi-services/bigsi-1/pv-claim.yaml
## BIGSI API services
kubectl create -f k8/bigsi-services/bigsi-1/bigsi-deployment.yaml

## You can test these are working by running 
kubectl exec -it bigsi-1-deployment-f6c8c9c5-76nzt 
curl localhost:8001/search?seq=CGGCGAGGAAGCGTTAAATCTCTTTCTGACG 
###(after installing curl if required)

## nginx reverse proxy config + service (this is the where the bigsi-aggregator service will send requests)
kubectl create configmap bigsi-1-nginx-configmap --from-file k8/bigsi-services/bigsi-1/nginx/nginx.conf
kubectl create -f k8/bigsi-services/bigsi-1/nginx/nginx-service.yaml
kubectl create -f k8/bigsi-services/bigsi-1/nginx/nginx-deployment.yaml

## kubectl exec -it bigsi-1-nginx-deployment-7dd488b66c-52kkv
## curl localhost/search?seq=CGGCGAGGAAGCGTTAAATCTCTTTCTGACG
## (after installing curl if required)

```

To add a new BIGSI index to the aggregator API, start with the template service and replace all instances of `{$INDEX_ID}` with the unique id of this index, and update the "bigsi-config.yaml" and "pv-volume.yaml" with the relevant paths and parameters. 

### Create the BIGSI aggregator service

BIGSI aggregator requires a redis instance to cache the results from a query and as a celery broker.

```
kubectl create -f k8/redis/redis-service.yaml
```

First update `k8/bigsi-aggregator-service/env.yaml` to include the list of BIGSI services it will query on every request.

```
$ cat k8/bigsi-aggregator-service/env.yaml
apiVersion: v1
data:
  BIGSI_URLS: "http://bigsi-1-nginx-service http://bigsi-2-nginx-service" ## space seperated list of BIGSI service URLs
  REDIS_IP: "redis"

kind: ConfigMap
metadata:
  name: bigsi-aggregator-env
```
Create the aggregator API service

```
kubectl create -f k8/bigsi-aggregator-service/env.yaml
kubectl create -f k8/bigsi-aggregator-service/bigsi-aggregator-service.yaml
kubectl create -f k8/bigsi-aggregator-service/bigsi-aggregator-api-deployment.yaml
kubectl create -f k8/bigsi-aggregator-service/bigsi-aggregator-worker-deployment.yaml

## Test it's working by running
$ curl -X POST  -H "Content-Type: application/json"  -d '{"seq":"CGGCGAGGAAGCGTTAAATCTCTTTCTGACG"}' localhost:8001/api/v1/searches/
{"id": "7cddc4de43abdfab233a4a17", "seq": "CGGCGAGGAAGCGTTAAATCTCTTTCTGACG", "threshold": 100, "score": false, "completed_bigsi_queries": 0, "total_bigsi_queries": 1, "results": [], "status": "INPROGRESS"}
$ curl localhost:8001/api/v1/searches/7cddc4de43abdfab233a4a17
{"id": "7cddc4de43abdfab233a4a17", "seq": "CGGCGAGGAAGCGTTAAATCTCTTTCTGACG", "threshold": 100, "score": false, "completed_bigsi_queries": 1, "total_bigsi_queries": 1, "results": [{"percent_kmers_found": 100, "num_kmers": "1", "num_kmers_found": "1", "sample_name": "s2", "score": null, "mismatches": null, "nident": null, "pident": null, "length": null, "evalue": null, "pvalue": null, "log_evalue": null, "log_pvalue": null, "kmer-presence": null}, {"percent_kmers_found": 100, "num_kmers": "1", "num_kmers_found": "1", "sample_name": "s1", "score": null, "mismatches": null, "nident": null, "pident": null, "length": null, "evalue": null, "pvalue": null, "log_evalue": null, "log_pvalue": null, "kmer-presence": null}], "status": "COMPLETE"}

```

Finally setup the nginx ingress

```
kubectl create configmap bigsi-aggregator-nginxconfigmap --from-file k8/bigsi-aggregator-service/nginx/nginx.conf
kubectl create -f k8/bigsi-aggregator-service/nginx/nginx-service.yaml
kubectl create -f k8/bigsi-aggregator-service/nginx/nginx-deployment.yaml

$ kubectl exec -it bigsi-aggregator-nginx-deployment-799c6f5596-5mlcw /bin/bash
root@bigsi-aggregator-nginx-deployment-799c6f5596-5mlcw:/# curl localhost/api/v1/searches/7cddc4de43abdfab233a4a17
{"id": "7cddc4de43abdfab233a4a17", "seq": "CGGCGAGGAAGCGTTAAATCTCTTTCTGACG", "threshold": 100, "score": false, "completed_bigsi_queries": 2, "total_bigsi_queries": 1, "results": [{"percent_kmers_found": 100, "num_kmers": "1", "num_kmers_found": "1", "sample_name": "s2", "score": null, "mismatches": null, "nident": null, "pident": null, "length": null, "evalue": null, "pvalue": null, "log_evalue": null, "log_pvalue": null, "kmer-presence": null}, {"percent_kmers_found": 100, "num_kmers": "1", "num_kmers_found": "1", "sample_name": "s1", "score": null, "mismatches": null, "nident": null, "pident": null, "length": null, "evalue": null, "pvalue": null, "log_evalue": null, "log_pvalue": null, "kmer-presence": null}], "status": "COMPLETE"}

```

## Deploy a new image
```
kubectl set image deployment/bigsi-aggregator-api-deployment bigsi-aggregator=phelimb/bigsi-aggregator:936dc9f
kubectl set image deployment/bigsi-aggregator-worker bigsi-aggregator-worker=phelimb/bigsi-aggregator:936dc9f

kubectl rollout status deployments bigsi-aggregator-api-deployment
kubectl rollout status deployments bigsi-aggregator-worker 

```


## TODO
[] Metadata service which is indexed by sample_id and merged with the results of searches.
[] Filter responses with DELETED SAMPLE
[] Return citation
[] Sort by Score, then Percent Kmers Found
[] BUG: Scored queries not returning score
[] HTTPS
[] BIGSI results output should have the same format as bigsi aggregator

