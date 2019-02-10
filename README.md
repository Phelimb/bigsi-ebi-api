# Repository for the EBI BIGSI query service API 

The architecture of this project involve an array of individual BIGSI servers with once process per index. 


This service will query each of these BIGSIs via HTTP requests, aggregate the results and combine with EBI metadata. 

It would be possible to design this in such a way that the BIGSI indexes were all controlled by this service. However, this would mean all BIGSIs would need to be on the filesystem. With this architecture, there is no requirement for the indexes to be on the same filesystem, provided they're available via a network. 

As a result, initialising this service requires a list of IP address for each of the BIGSI APIs. These are updatable via an ENV variable.

This API only provides read-only access to the `search` endpoint, creation and updating of the indexes are managed manually.

Queries create a backgroud task which query all the BIGSIs in the array. The results are aggregated and cached in redis for 48 hours and are given a unique endpoint to lookup results. This URL can be polled to get the latests results. 

### Create a k8 BIGSI

```
kubectl create -f k8/pv-volume.yaml
kubectl create -f k8/pv-claim.yaml
kubectl create -f k8/env.yaml
kubectl create -f k8/bigsi-config.yaml
kubectl create -f k8/
```


## TODO
[X] POST to /search will create a search objects with a unique ID
[X] POST to /search triggers a "sub_index_search"
[X] Celery task "sub_index_search" to handle POST request to a BIGSI and retrys
[X] "sub_index_search" updates Search object by adding results to the cache as they come in (HSET by sample ID) and marks search as complete. Once all searches are complete the status of Search is set to "complete" and the caches are merged and stored in a new cache. 
[X] GET /search/:search_id returns aggregate of search results 
[] Metadata is indexed by sample_id and merged with the results of sub_index_search.
