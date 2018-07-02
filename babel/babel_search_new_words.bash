#!/bin/bash

# Search new words :
# run me

echo extraction messages.pot...
pybabel extract -F babel.cfg -o babel/config/messages.pot .
