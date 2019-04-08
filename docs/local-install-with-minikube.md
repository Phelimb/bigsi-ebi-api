
Start minikube
```
minikube start
minikube mount /local/path/to/bigis_test_data/bigsi/:/data/bigsi/
```

In this example, the index file is called "test-bigsi-bdb" and will now be available via local filesystem at `/data/bigsi/test-bigsi-bdb` within the minikube VM. 

In order to make this available from within a k8 pod, we first need a volume and volume claim. 

```
## Volume mounts
kubectl create -f k8/bigsi-services/bigsi-1/pv-volume.yaml
kubectl create -f k8/bigsi-services/bigsi-1/pv-claim.yaml
```

Now, we can create the deployments and services

```
kubectl create -f k8/bigsi-services/bigsi-1/bigsi-deployment.yaml
```