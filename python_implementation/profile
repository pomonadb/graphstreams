#! /usr/bin/sh

python -m cProfile -o iso.prof ./"$@"

pyprof2calltree -k -i iso.prof -o iso.tree

