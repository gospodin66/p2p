---
******************************************************************************************
*** Base setup:
1. create cluster from p2p/deployment/p2p-net/kind-cluster-config.yaml

2. run p2p/deployment/scripts/setup.sh

2. (to delete) run p2p/deployment/scripts/clear.sh
******************************************************************************************
*** Create kind cluster from config:
kind create cluster \
    --config /home/cheki/projects/p2p/deployment/p2p-net/kind-cluster-config.yaml

*** Set default kubernetes namespace:
kubectl config set-context --current --namespace=p2p

*** Helm CREATE chart:
helm create p2p-net

*** Helm INSTALL:
helm install --dry-run --debug --generate-name -f ../p2p-net/values.yaml ../p2p-net
helm install -f /home/cheki/projects/p2p/deployment/p2p-net/values.yaml \
                p2pnet \
                /home/cheki/projects/p2p/deployment/p2p-net

*** Helm UPGRADE:
helm upgrade --install p2p-network -f ../p2p-net/values.yaml ../p2p-net
******************************************************************************************
watch "kubectl get deploy -n p2p -o wide && \
       kubectl get po -n p2p -o wide && \
       kubectl get svc -n p2p -o wide"

kubectl get node -n p2p -o wide
******************************************************************************************
kind load docker-image p2p-0-node:1.0
kind load docker-image p2p-bot-node:1.0
******************************************************************************************
*** Create self-signed SSL cert:
openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
  -keyout 172.20.0.20.key.pem -out 172.20.0.20.crt.pem -subj "/CN=172.20.0.20" 
******************************************************************************************
*** Up hosts in network:
kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) \
    -- nmap -n 10.244.0-2.0-255/24 -p 44000-49999 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) \
    -- nmap -sn 10.244.0-2.0-255 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) \
    -- nmap --iflist
******************************************************************************************
*** Add nodes ips in network to file:
kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) \
    -- sh -c "touch /p2p/ips.txt && nmap -n -sn 10.244.1-2.0-255 -oG - \
            | awk '/Up\$/{print \$2}' \
            | sort -V \
            | tee /p2p/ips.txt"
******************************************************************************************

*** Exec on pod by name prefix:
kubectl exec -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) \
    -- /bin/sh

kubectl exec -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep test-probe) \
    -- /bin/sh

*** Scan network & save ips to list:
nmap -vvv -n -sn 10.244.1-2.0-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt



*** Attach to pod by name prefix:
kubectl attach -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node)

kubectl attach -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep test-probe)



*** Get service ports:
kubectl describe service --namespace=p2p | grep -i nodeport | grep -o -E '[0-9]+'
******************************************************************************************
curl -vvv --insecure --user registryadmin:registrypassword https://192.168.1.61:47443
curl -vvv --insecure --user registryadmin:registrypassword http://192.168.1.61:47880
******************************************************************************************
*** Auto-download & run bot-node.py script (auto-connect to remote host):
path="node-autorun.py"
host="$(hostname -i):45666"
remotehost="172.19.0.3:31515"
if [ ! -f $path ]; then wget -O $path http://$remotehost; fi
if [ ! -f $path ]; then curl -vvv -o $path http://$remotehost; fi
python $path $host $remotehost
******************************************************************************************
