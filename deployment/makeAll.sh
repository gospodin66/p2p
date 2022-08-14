#!/bin/sh

echo "Making 0.."

make env -f Makefile0Node
make init -f Makefile0Node
make install -f Makefile0Node
make test -f Makefile0Node
make build -f Makefile0Node
make create -f Makefile0Node
make start -f Makefile0Node
make run -f Makefile0Node
make clean -f Makefile0Node
make exec -f Makefile0Node

# echo "Making bot.."

# make init -f MakefileBotNode
# make install -f MakefileBotNode
# make clean -f MakefileBotNode
# make env -f MakefileBotNode
# make test -f MakefileBotNode
# make build -f MakefileBotNode
# make create -f MakefileBotNode
# make start -f MakefileBotNode
# make run -f MakefileBotNode
# make exec -f MakefileBotNode

echo "Done!"
exit 0