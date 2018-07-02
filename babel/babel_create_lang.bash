#!/bin/bash

# Choose language translation and run me

# Create language translation repertory with messages.pot words
echo init fr language...
pybabel init -i babel/config/messages.pot -d babel/config/translations -l fr

# Compile the translation file
echo compilation...
pybabel compile -d babel/config/translations

# You can modify translations/language/ messages.pot and update it with :
# run babel_update_lang
