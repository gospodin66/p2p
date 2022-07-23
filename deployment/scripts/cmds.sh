---

kubectl config set-context --current --namespace=p2p

helm create p2p-net-chart

cd scripts

helm install --dry-run --debug --generate-name -f ../p2p-net/values.yaml ../p2p-net

helm install p2p-net -f ../p2p-net/values.yaml ../p2p-net

kubectl get deploy -o wide && \
kubectl get po -o wide && \
kubectl get svc -o wide

kind load docker-image p2p-0-node:1.0
kind load docker-image p2p-def-node:1.0
kind load docker-image p2p-bot-node:1.0


