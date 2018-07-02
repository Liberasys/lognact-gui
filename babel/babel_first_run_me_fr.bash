#!/bin/bash

# For the first run ! + init lang fr traduction:
# run me

# Create the extraction file
echo first init ...
echo extraction to messages.pot...
pybabel extract -F babel.cfg -o babel/config/messages.pot .

# Create fr translation repertory with messages.pot words
echo init fr language...
pybabel init -i babel/config/messages.pot -d babel/config/translations -l fr

# Compile the translation file
echo compilation ...
pybabel compile -d babel/config/translations

# You can modify translations/language/ messages.pot and update it with :
# run babel_update_lang
