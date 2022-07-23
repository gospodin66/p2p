#!/bin/sh

KIND=deployment
NAME=p2p-net
RELEASE=p2p-net
NAMESPACE=p2p

kubectl annotate $KIND $NAME meta.helm.sh/release-name=$RELEASE
kubectl annotate $KIND $NAME meta.helm.sh/release-namespace=$NAMESPACE
kubectl label $KIND $NAME app.kubernetes.io/managed-by=Helm
