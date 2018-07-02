#!/usr/bin/python3.5

import sys
sys.path.append('./lib')
sys.path.append('./models')

import flask_app
import yaml_file_syncer
import hash_source


conf_file = "./config.yml"
syncer = yaml_file_syncer.YamlFileSyncer(conf_file)
conf = syncer.read()
if conf[1] is None:
    print('Fichier vide ou erreur : ({})'.format(conf[0]))
else :
    try:
        if conf[1]['password'] != '':
            conf[1]['hash'] = hash_source.hash(conf[1]['password'])
            conf[1]['password'] = ''
            syncer.write(conf[1])
            flask_app.Manage(conf[1])
        else:
            flask_app.Manage(conf[1])
    except OSError as err:
        print("Erreur: {0}".format(err))
