---

kubectl config set-context --current --namespace=p2p

helm create p2p-net-chart

cd scripts

helm install --dry-run --debug --generate-name -f ../p2p-net/values.yaml ../p2p-net

helm upgrade --install p2p-network -f ../p2p-net/values.yaml ../p2p-net

kubectl get deploy --namespace p2p -o wide && \
kubectl get po --namespace p2p -o wide && \
kubectl get svc --namespace p2p -o wide

kind load docker-image p2p-0-node:1.0
kind load docker-image p2p-def-node:1.0
kind load docker-image p2p-bot-node:1.0




Error: INSTALLATION FAILED: rendered manifests contain a resource that already exists. Unable to continue with install: 

Namespace "p2p" in namespace "" exists and cannot be imported into the current release: invalid ownership metadata; 

label validation error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"; 

annotation validation error: missing key "meta.helm.sh/release-name": must be set to "p2p-net";

annotation validation error: missing key "meta.helm.sh/release-namespace": must be set to "p2p"
