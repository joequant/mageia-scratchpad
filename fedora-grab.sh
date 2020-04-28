#!/bin/bash

#wget https://src.fedoraproject.org/rpms/$1/raw/master/f/$1.spec
mv $1 $1.bak
./fedora2mageia.py < $1.bak > $1

