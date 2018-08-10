#!/bin/bash
echo "all args : $*"
# store arguments in a special array 
args=("$@") 
# get number of elements 
ELEMENTS=${#args[@]} 
 
# echo each element in array  
# for loop 
for (( i=0;i<$ELEMENTS;i++)); do 
	    echo "arg $i : ${args[${i}]}"
    done
