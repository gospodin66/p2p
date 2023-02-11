---

***************************************************************************
1. create cluster from p2p/deployment/p2p-net/kind-cluster-config.yaml

2. run p2p/deployment/scripts/setup.sh

2. (to delete) run p2p/deployment/scripts/clear.sh
***************************************************************************




kind create cluster --config /home/cheki/projects/p2p/deployment/p2p-net/kind-cluster-config.yaml




kubectl config set-context --current --namespace=p2p

helm create p2p-net-chart

cd scripts

helm install --dry-run --debug --generate-name -f ../p2p-net/values.yaml ../p2p-net

helm upgrade --install p2p-network -f ../p2p-net/values.yaml ../p2p-net

***************************************************************************

kubectl get deploy --namespace p2p -o wide && \
kubectl get po --namespace p2p -o wide && \
kubectl get svc --namespace p2p -o wide

***************************************************************************

kind load docker-image p2p-0-node:1.0
# kind load docker-image p2p-def-node:1.0
kind load docker-image p2p-bot-node:1.0

***************************************************************************

openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
  -keyout 172.20.0.20.key.pem -out 172.20.0.20.crt.pem -subj "/CN=172.20.0.20" 


curl -vvv --insecure https://127.0.0.1:47780/docker-image-registry/p2p-network-src.tar.xz
  

curl -vvv --insecure -L https://registryadmin:registrypassword@127.0.0.1:47780/docker-image-registry

***************************************************************************

## up hosts in network
kubectl exec $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) -- \
  nmap -n 10.244.0.0-30/24 -p 44000-49999 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) -- \
  nmap -sn 10.244.0.30-255 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) -- \
  nmap --iflist


# ADD ips in network to txt file
# -D 10.244.0.100,10.244.0.101,10.244.0.102,10.244.0.103
# proxychains

kubectl exec $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) -- touch /p2p/ips.txt && nmap -n -sn 10.244.0.10-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt

***************************************************************************

kubectl exec -it $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) -- /bin/sh

nmap -vvv -n -sn 10.244.1-2.0-50 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt

kubectl attach -it $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node)

# GET service ports

kubectl describe service --namespace=p2p | grep -i nodeport | grep -o -E '[0-9]+'


curl -vvv --insecure --user registryadmin:registrypassword https://192.168.1.61:47443

curl -vvv --insecure --user registryadmin:registrypassword http://192.168.1.61:47880


kubectl config set-context --current --namespace=p2p


helm install -f /home/cheki/projects/p2p/deployment/p2p-net/values.yaml p2pnet /home/cheki/projects/p2p/deployment/p2p-net

kubectl config set-context --current --namespace=p2pnet

