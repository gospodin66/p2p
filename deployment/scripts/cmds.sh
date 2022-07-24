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


openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
  -keyout 172.20.0.20.key.pem -out 172.20.0.20.crt.pem -subj "/CN=172.20.0.20" 


curl -vvv --insecure https://127.0.0.1:47780/docker-image-registry/p2p-network-src.tar.xz
  

curl -vvv --insecure -L https://registryadmin:registrypassword@127.0.0.1:47780/docker-image-registry


connnode:10.244.0.20:45666
connnode:10.244.0.25:45666
connnode:10.244.0.24:45666
connnode:10.244.0.23:45666
connnode:10.244.0.22:45666
connnode:10.244.0.21:45666

