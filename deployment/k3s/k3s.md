## k3s

Quick-Start - Install Script

The install.sh script provides a convenient way to download K3s and add a service to systemd or openrc.

To install k3s as a service, run:

curl -sfL https://get.k3s.io | sh -

A kubeconfig file is written to /etc/rancher/k3s/k3s.yaml and the service is automatically started or restarted. The install script will install K3s and additional utilities, such as kubectl, crictl, k3s-killall.sh, and k3s-uninstall.sh, for example:

sudo kubectl get nodes

K3S_TOKEN is created at /var/lib/rancher/k3s/server/node-token on your server. To install on worker nodes, pass K3S_URL along with K3S_TOKEN environment variables, for example:

curl -sfL https://get.k3s.io | K3S_URL=https://myserver:6443 K3S_TOKEN=XXX sh -

Manual Download

    Download k3s from latest release, x86_64, armhf, arm64 and s390x are supported.
    Run the server.

sudo k3s server &
# Kubeconfig is written to /etc/rancher/k3s/k3s.yaml
sudo k3s kubectl get nodes

# On a different node run the below. NODE_TOKEN comes from
# /var/lib/rancher/k3s/server/node-token on your server
sudo k3s agent --server https://myserver:6443 --token ${NODE_TOKEN}


### Cluster access
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get pods --all-namespaces
helm ls --all-namespaces


### Import docker images to k3s
docker save p2p-0-node:1.0 | sudo k3s ctr images import -
docker save p2p-bot-node:1.0 | sudo k3s ctr images import -


### List images
sudo k3s ctr images ls

