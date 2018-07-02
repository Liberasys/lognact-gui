#!/bin/bash

# For update translations :
# run me

echo update translations...

pybabel update -i babel/config/messages.pot -d babel/config/translations
