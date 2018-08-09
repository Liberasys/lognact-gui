# lognact GUI : HTML gui for interacting with ansible scripts of lognact.>
#
#    Copyright (C) 2018 HUSSON CONSULTING SAS - Liberasys
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.




from flask import Flask, redirect, url_for, render_template, jsonify, session, request
# g for global var from Flask
from flask import g
from flask_babel import Babel, format_date, gettext
import os
from datetime import datetime

import sys
sys.path.append('./lib')
sys.path.append('./models')
from tasks_manager import Tasks_manager
from inventory_manager import Inventory
from users_and_users_groups_manager import Users_and_users_groups_manager
from permissions_manager import Permissions_manager
from validator import Validator
from models import sqladb, Task


class Manage():

    def __init__(self, conf):

        # import configuration_file from parametes
        self.host = conf['host']
        self.port = conf['port']
        self.debug_mode = conf['debug_mode']
        self.ansible_path = conf['ansible_dir_path']

        self.db_uri = 'sqlite:///' + conf['db_path']
        self.lib_db_uri = 'sqlite:///' + conf['db_path']
        #self.db_uri = 'sqlite:///' + conf['db_path'] + '?check_same_thread=False'
        #self.lib_db_uri = 'sqlite:///' + conf['db_path'] + '?check_same_thread=False'


        # use Flask as app and set app configuration :
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = self.db_uri
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        self.app.config['BABEL_DEFAULT_LOCALE'] = 'en'
        # self.app.config['SECRET_KEY'] = os.urandom(16)
        self.app.config['SECRET_KEY'] = 'test_key'

        sqladb.app = self.app
        sqladb.init_app(self.app)

        # ! only for tests:
        # sqladb.drop_all()
        # sqladb.create_all()

        # sqladb.session.commit()

        # use Babel
        # see doc : https://pythonhosted.org/Flask-Babel/
        self.babel = Babel(self.app)

        # use managers :
        self.inventory_manager = Inventory(conf['ansible_dir_path'], conf['inventory_file_subpath'])
        self.users_and_users_groups_manager = Users_and_users_groups_manager()
        self.manage_validator = Validator()
        self.permissions_manager = Permissions_manager(self.users_and_users_groups_manager, self.inventory_manager)
        self.tasks_manager = Tasks_manager(self.lib_db_uri)

        self.tasks_manager.update_disappeared_tasks()

        ### XXX tests
        #task1 = self.tasks_manager.create_task(username='user3', command="ping -c 45 127.0.0.1")
        #task2 = self.tasks_manager.create_task(username='user3', command="pwd", cdw=self.ansible_path)
        #task2 = self.tasks_manager.create_task(username='user3', command="echo $PATH")
        #task2 = self.tasks_manager.create_task(username='user3', command="/usr/bin/ansible-playbook -vvv ./example2.yml --inventory ./inventories/inventory.yml --limit localhost", cdw=self.ansible_path)
        #task2 = self.tasks_manager.create_task(username='user3', command="./echo_args.bash --inventory ./inventories/inventory.yml --limit localhost", cdw=self.ansible_path)
        #task2 = self.tasks_manager.create_task(username='user3', command="./test.bash", cdw=self.ansible_path)

        # set global vars (lang):
        # use app_context -> see doc : http://flask.pocoo.org/docs/1.0/appcontext/ for details
        with self.app.app_context():
            g.lang = self.app.config['BABEL_DEFAULT_LOCALE']

        self.users_and_users_groups_manager.add_user(
                                                     conf['default_user'],
                                                     conf['hash'],
                                                     True
                                                     )

        # use views :
        self.__define_views()

        # finally start the server
        self.__run_server()

        # override babel locale :
        # g.lang define with globals
        @self.babel.localeselector
        def get_locale():
            return g.lang

    def __run_server(self):
        self.app.run(host=self.host, port=self.port, debug=self.debug_mode)


    def __define_views(self):

        #home
        @self.app.route('/')
        def index():
            return render_template('index.html', results = ('', None))

        #connection
        @self.app.route('/connection/', methods=['POST'])
        def connection():
            assert request.method == 'POST'
            user = (request.form['username'], request.form['password'])
            results = self.manage_validator.is_valid_user(
                                            user,
                                            self.permissions_manager.connect,
                                            user,
                                            None,
                                            None)
            session['error_message'] = results[0]
            return render_template('index.html', results = results)


        #disconnect
        @self.app.route('/disconnect/', methods=['GET'])
        def disconnect():
            assert request.method == 'GET'
            try:
                session.pop('username')
                return render_template('index.html', results = ('', None))
            except:
                return render_template('index.html', results = ('', None))


        #session message error
        @self.app.route('/set_error_message/<string:message>', methods=['GET'])
        def error_message(message):
            session['error_message'] = message
            return ''


        #tests
        @self.app.route('/tests/', methods=['POST'])
        def tests():
            return render_template('test.html')


        #nodes
        @self.app.route('/nodes/')
        def get_nodes():
            message = ""
            nodes_list = None
            vars_in_node = None
            nodes_list_response = ['']
            vars_in_node_response = ['']

            try:
                nodes_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_node_names,
                        session['username'],
                        self.inventory_manager.get_node_names,
                        [None]
                        )
                nodes_list = sorted(nodes_list_response[1])
            except:
                session['error_message'] = nodes_list_response[0]


            try:
                nodename = session['selected_node']
            except:
                try:
                    if nodes_list[0] is not None:
                        session['selected_node'] = nodes_list[0]
                except:
                    pass


            try:
                vars_in_node_response = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.get_node_by_name_vars_dict,
                                session['username'],
                                self.inventory_manager.get_node_by_name_vars_dict,
                                [session['selected_node']]
                                )
                vars_in_node = vars_in_node_response[1]
            except:
                pass



            session['error_message'] = vars_in_node_response[0]
            if nodes_list_response[0] != '':
                session['error_message'] = nodes_list_response[0]

            return render_template('nodes.html',
                                    results=(message,
                                            nodes_list,
                                            vars_in_node,
                                            )
                                    )



        @self.app.route('/nodes/set_active_node/<string:nodename>', methods=['GET'])
        def set_active_node(nodename):
            session['selected_node'] = nodename
            return nodename


        @self.app.route('/nodes/add_node/', methods=['POST'])
        def add_node():
            message = ""
            nodes_list = None
            vars_in_node = None

            assert request.method == 'POST'
            results = self.manage_validator.is_valid_node(
                        request.form['nodename'],
                        self.permissions_manager.add_node,
                        session['username'],
                        self.inventory_manager.add_node,
                        [request.form['nodename']]
                        )

            try:
                nodes_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_node_names,
                        session['username'],
                        self.inventory_manager.get_node_names,
                        [None]
                        )
                nodes_list = sorted(nodes_list_response[1])
            except:
                pass

            session['error_message'] = nodes_list_response[0]
            if results[0] != '':
                session['error_message'] = results[0]



            return render_template('nodes.html',
                                    results=(message,
                                            nodes_list,
                                            vars_in_node,
                                            )
                                    )

        @self.app.route('/nodes/delete_node/')
        def delete_node():

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.del_node_by_name_,
                                session['username'],
                                self.inventory_manager.del_node_by_name_,
                                [session['selected_node']]
                                )

            try:
                nodes_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_node_names,
                        session['username'],
                        self.inventory_manager.get_node_names,
                        [None]
                        )
                nodes_list = sorted(nodes_list_response[1])
            except:
                pass


            try:
                if nodes_list[0] is not None:
                    session['selected_node'] = nodes_list[0]
            except:
                session.pop('selected_node')



            return results[0]


        @self.app.route('/nodes/get_vars/')
        def get_node_vars():
            tuple_result = None
            return render_template('nodes.html', results=('', None))

        @self.app.route('/nodes/set_var/', methods=['POST'])
        def set_node_var():
            message = ''
            nodes_list = None
            vars_list = None
            nodes_list_response = ['']
            vars_in_node_response = ['']

            assert request.method == 'POST'

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.update_node_by_name_var,
                                session['username'],
                                self.inventory_manager.update_node_by_name_var,
                                [
                                    session['selected_node'],
                                    request.form['varName'],
                                    request.form['varValue']
                                ])

            try:
                nodes_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_node_names,
                        session['username'],
                        self.inventory_manager.get_node_names,
                        [None]
                        )
                nodes_list = sorted(nodes_list_response[1])
            except:
                pass

            try:
                nodename = session['selected_node']
            except:
                try:
                    if nodes_list[0] is not None:
                        session['selected_node'] = nodes_list[0]
                except:
                    pass

            try :
                vars_in_node_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_node_by_name_vars_dict,
                            session['username'],
                            self.inventory_manager.get_node_by_name_vars_dict,
                            [session['selected_node']]
                            )
                vars_in_node = vars_in_node_response[1]
            except:
                pass


            session['error_message'] = vars_in_node_response[0]
            if nodes_list_response[0] != '':
                session['error_message'] = nodes_list_response[0]
            if results[0] != '':
                session['error_message'] = results[0]


            return render_template('nodes.html',
                                    results=(message,
                                            nodes_list,
                                            vars_in_node,
                                            )
                                    )

        @self.app.route('/nodes/delete_var/<string:var_name>', methods=['GET'])
        def delete_node_var(var_name):

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.del_node_by_name_var,
                                session['username'],
                                self.inventory_manager.del_node_by_name_var,
                                [session['selected_node'], var_name]
                                )
            return results[0]



        @self.app.route('/nodes/run_staging/')
        def run_staging():
            tuple_result = None
            return render_template('nodes.html', results=('', None))


        #nodes_groups
        @self.app.route('/nodes_groups/')
        def get_groups():

            message = ''
            groups_list = None
            nodes_not_in_group = None
            nodes_in_group = None
            vars_in_group = None
            groups_list_response = ['']
            nodes_not_in_group_response = ['']
            nodes_in_group_response = ['']
            vars_in_group_response = ['']

            try:
                groups_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_group_names,
                        session['username'],
                        self.inventory_manager.get_group_names,
                        [None]
                        )
                groups_list = sorted(groups_list_response[1])
            except:
                pass


            try:
                groupname = session['selected_group']
            except:
                try:
                    if groups_list[0] is not None:
                        session['selected_group'] = groups_list[0]
                except:
                    pass


            try:
                nodes_not_in_group_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_nodes_names_not_in_group_by_name,
                        session['username'],
                        self.inventory_manager.get_nodes_names_not_in_group_by_name,
                        [session['selected_group']]
                        )
                nodes_not_in_group = sorted(nodes_not_in_group_response[1])
            except:
                pass



            try :
                nodes_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_nodes_names_in_group_by_name,
                            session['username'],
                            self.inventory_manager.get_nodes_names_in_group_by_name,
                            [session['selected_group']]
                            )
                nodes_in_group = sorted(nodes_in_group_response[1])
            except:
                pass

            try :
                vars_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_group_by_name_vars_dict,
                            session['username'],
                            self.inventory_manager.get_group_by_name_vars_dict,
                            [session['selected_group']]
                            )
                vars_in_group = vars_in_group_response[1]
            except:
                pass

            session['error_message'] = vars_in_group_response[0]
            if nodes_in_group_response[0] != '':
                session['error_message'] = nodes_in_group_response[0]
            if nodes_not_in_group_response[0] != '':
                session['error_message'] = nodes_not_in_group_response[0]
            if groups_list_response[0] != '':
                session['error_message'] = groups_list_response[0]

            return render_template('nodes_groups.html',
                                    results=(message,
                                            groups_list,
                                            nodes_not_in_group,
                                            nodes_in_group,
                                            vars_in_group
                                            )
                                    )


        @self.app.route('/nodes_groups/set_active_group/<string:groupname>', methods=['GET'])
        def set_active_group(groupname):
            session['selected_group'] = groupname
            return groupname


        @self.app.route('/nodes_groups/add_group/', methods=['POST'])
        def add_group():

            message = ''
            groups_list = None
            nodes_not_in_group = None
            nodes_in_group = None
            vars_in_group = None
            groups_list_response = ['']
            nodes_not_in_group_response = ['']
            nodes_in_group_response = ['']
            vars_in_group_response = ['']


            assert request.method == 'POST'
            results = self.manage_validator.is_valid_name(
                        request.form['groupname'],
                        self.permissions_manager.add_group,
                        session['username'],
                        self.inventory_manager.add_group,
                        [request.form['groupname']]
                        )

            try:
                groups_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_group_names,
                        session['username'],
                        self.inventory_manager.get_group_names,
                        [None]
                        )
                groups_list = sorted(groups_list_response[1])
            except:
                pass

            try:
                nodes_not_in_group_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_nodes_names_not_in_group_by_name,
                        session['username'],
                        self.inventory_manager.get_nodes_names_not_in_group_by_name,
                        [session['selected_group']]
                        )
                nodes_not_in_group = sorted(nodes_not_in_group_response[1])
            except:
                pass

            try:
                groupname = session['selected_group']
            except:
                try:
                    if groups_list[0] is not None:
                        session['selected_group'] = groups_list[0]
                except:
                    pass

            try :
                nodes_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_nodes_names_in_group_by_name,
                            session['username'],
                            self.inventory_manager.get_nodes_names_in_group_by_name,
                            [session['selected_group']]
                            )
                nodes_in_group = sorted(nodes_in_group_response[1])
            except:
                pass

            try :
                vars_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_group_by_name_vars_dict,
                            session['username'],
                            self.inventory_manager.get_group_by_name_vars_dict,
                            [session['selected_group']]
                            )
                vars_in_group = sorted(vars_in_group_response[1])
            except:
                pass

            session['error_message'] = vars_in_group_response[0]
            if nodes_in_group_response[0] != '':
                session['error_message'] = nodes_in_group_response[0]
            if nodes_not_in_group_response[0] != '':
                session['error_message'] = nodes_not_in_group_response[0]
            if groups_list_response[0] != '':
                session['error_message'] = groups_list_response[0]
            if results[0] != '':
                session['error_message'] = results[0]

            return render_template('nodes_groups.html',
                                    results=(message,
                                            groups_list,
                                            nodes_not_in_group,
                                            nodes_in_group,
                                            vars_in_group
                                            )
                                    )



        @self.app.route('/nodes_groups/delete_group/')
        def delete_group():

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.del_group_by_name_,
                                session['username'],
                                self.inventory_manager.del_group_by_name_,
                                [session['selected_group']]
                                )

            try:
                groups_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_group_names,
                        session['username'],
                        self.inventory_manager.get_group_names,
                        [None]
                        )
                groups_list = sorted(groups_list_response[1])
            except:
                pass


            try:
                if groups_list[0] is not None:
                    session['selected_group'] = groups_list[0]
            except:
                session.pop('selected_group')

            return results[0]


        @self.app.route('/nodes_groups/add_node/<string:nodename>/', methods=['GET'])
        def add_node_in_group(nodename):

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.add_node_name_in_group_name,
                                session['username'],
                                self.inventory_manager.add_node_name_in_group_name,
                                [nodename, session['selected_group']]
                                )
            return results[0]


        @self.app.route('/nodes_groups/delete_node/<string:nodename>', methods=['GET'])
        def delete_node_from_group(nodename):

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.remove_node_name_in_group_name,
                                session['username'],
                                self.inventory_manager.remove_node_name_in_group_name,
                                [nodename, session['selected_group']]
                                )
            return results[0]


        @self.app.route('/nodes_groups/set_var/', methods=['POST'])
        def set_group_var():

            message = ''
            groups_list = None
            nodes_not_in_group = None
            nodes_in_group = None
            vars_in_group = None
            groups_list_response = ['']
            nodes_not_in_group_response = ['']
            nodes_in_group_response = ['']
            vars_in_group_response = ['']


            assert request.method == 'POST'

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.update_group_by_name_var,
                                session['username'],
                                self.inventory_manager.update_group_by_name_var,
                                [
                                    session['selected_group'],
                                    request.form['varName'],
                                    request.form['varValue']
                                ])

            try:
                groups_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_group_names,
                        session['username'],
                        self.inventory_manager.get_group_names,
                        [None]
                        )
                groups_list = sorted(groups_list_response[1])
            except:
                pass

            try:
                nodes_not_in_group_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_nodes_names_not_in_group_by_name,
                        session['username'],
                        self.inventory_manager.get_nodes_names_not_in_group_by_name,
                        [session['selected_group']]
                        )
                nodes_not_in_group = sorted(nodes_not_in_group_response[1])
            except:
                pass

            try:
                groupname = session['selected_group']
            except:
                try:
                    if groups_list[0] is not None:
                        session['selected_group'] = groups_list[0]
                except:
                    pass

            try :
                nodes_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_nodes_names_in_group_by_name,
                            session['username'],
                            self.inventory_manager.get_nodes_names_in_group_by_name,
                            [session['selected_group']]
                            )
                nodes_in_group = sorted(nodes_in_group_response[1])
            except:
                pass

            try :
                vars_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_group_by_name_vars_dict,
                            session['username'],
                            self.inventory_manager.get_group_by_name_vars_dict,
                            [session['selected_group']]
                            )
                vars_in_group = vars_in_group_response[1]
            except:
                pass

            session['error_message'] = vars_in_group_response[0]
            if nodes_in_group_response[0] != '':
                session['error_message'] = nodes_in_group_response[0]
            if nodes_not_in_group_response[0] != '':
                session['error_message'] = nodes_not_in_group_response[0]
            if groups_list_response[0] != '':
                session['error_message'] = groups_list_response[0]
            if results[0] != '':
                session['error_message'] = results[0]

            return render_template('nodes_groups.html',
                                    results=(message,
                                            groups_list,
                                            nodes_not_in_group,
                                            nodes_in_group,
                                            vars_in_group
                                            )
                                    )


        @self.app.route('/nodes_groups/delete_var/<string:var_name>', methods=['GET'])
        def delete_group_var(var_name):

            results = self.manage_validator.check_permission_and_run(
                                self.permissions_manager.del_group_by_name_var,
                                session['username'],
                                self.inventory_manager.del_group_by_name_var,
                                [session['selected_group'], var_name]
                                )
            return results[0]


        #users_manager
        @self.app.route('/users_manager/users/')
        def get_users():
            tuple_result = None
            return render_template('users.html', results=('', None))


        @self.app.route('/users_manager/users/add_user/')
        def add_user():
            tuple_result = None
            return render_template('users.html', results=('', None))


        @self.app.route('/users_manager/users/set_user/')
        def set_user():
            tuple_result = None
            return render_template('users.html', results=('', None))


        @self.app.route('/users_manager/users/delete_user/')
        def delete_user():
            tuple_result = None
            return render_template('users.html', results=('', None))


        @self.app.route('/users_manager/users_groups/')
        def get_users_groups():
            tuple_result = None
            return render_template('users_groups.html', results=('', None))


        @self.app.route('/users_manager/users_groups/set_user/')
        def set_user_in_users_group():
            tuple_result = None
            return render_template('users_groups.html', results=('', None))


        @self.app.route('/users_manager/users_groups/delete_user')
        def delete_user_from_users_group():
            tuple_result = None
            return render_template('users_groups.html', results=('', None))


        @self.app.route('/nodes/set_active_playbook/<string:playbook_name>', methods=['GET'])
        def set_active_playbook(playbook_name):
            session['selected_playbook'] = playbook_name
            return playbook_name

        @self.app.route('/nodes/run_active_playbook_on_node/', methods=['GET'])
        def run_active_playbook_on_node():
            if (
                   'selected_playbook' not in session or
                   session['selected_playbook'] == None or
                   'selected_node' not in session or
                   session['selected_node'] == None
                ):
                session['error_message'] += "No playbook selected or no node selected."
            command_to_run = "ansible-playbook " + session['selected_playbook'] + " --inventory ./inventories/inventory.yml --limit " + session['selected_node']
            print(command_to_run)
            task = self.tasks_manager.create_task(username=session['username'], command=command_to_run, cdw=self.ansible_path)
            return session['selected_playbook']


        @self.app.route('/nodes/run_active_playbook_on_group/', methods=['GET'])
        def run_active_playbook_on_group():
            if (
                   'selected_playbook' not in session or
                   session['selected_playbook'] == None or
                   'selected_group' not in session or
                   session['selected_group'] == None
                ):
                session['error_message'] += "No playbook selected or no group selected."
            command_to_run = "ansible-playbook " + session['selected_playbook'] + " --inventory ./inventories/inventory.yml --limit " + session['selected_group']
            print(command_to_run)
            task = self.tasks_manager.create_task(username=session['username'], command=command_to_run, cdw=self.ansible_path)
            return session['selected_playbook']



        #playbook
        @self.app.route('/playbook/')
        def playbook():
            import glob

            message = ''
            groups_list = None
            nodes_in_group = None
            playbooks_list = None
            groups_list_response = ['']
            nodes_in_group_response =['']
            playbooks_list_response = ['']

            try:
                groups_list_response = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_group_names,
                        session['username'],
                        self.inventory_manager.get_group_names,
                        [None]
                        )
                groups_list = sorted(groups_list_response[1])
            except:
                pass

            try :
                nodes_in_group_response = self.manage_validator.check_permission_and_run(
                            self.permissions_manager.get_nodes_names_in_group_by_name,
                            session['username'],
                            self.inventory_manager.get_nodes_names_in_group_by_name,
                            [session['selected_group']]
                            )
                nodes_in_group = sorted(nodes_in_group_response[1])
            except:
                pass

            playbooks_list = []
            for path in glob.glob(self.ansible_path + "*.yml"):
                playbooks_list.append(os.path.basename(path))
            playbooks_list = sorted(playbooks_list)

            return render_template('playbook.html',
                                                    results=(message,
                                                    groups_list,
                                                    nodes_in_group,
                                                    playbooks_list
                                                    )
                                    )


        #permissions
        @self.app.route('/permissions/')
        def get_permissions():
            tuple_result = None
            return render_template('permissions.html', results=('', None))


        @self.app.route('/permissions/get_permission/')
        def get_permission():
            tuple_result = None
            return render_template('permissions.html', results=('', None))


        @self.app.route('/permissions/set_permission/')
        def set_permission():
            tuple_result = None
            return render_template('permissions.html', results=('', None))


        #task_list
        @self.app.route('/task_list/')
        def get_tasks():
            session['error_message'] = ''
            try:
                (errormsg, tasks_dict) = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_tasks,
                        session['username'],
                        self.tasks_manager.read_tasks,
                        [None]
                        )
                if errormsg != '': session['error_message'] += errormsg
            except:
                pass
            return render_template('task_list.html', results=(tasks_dict))

        @self.app.route('/task_list/add_task/')
        def add_task():
            tuple_result = None
            return render_template('task_list.html', results=('', None))


        @self.app.route('/task_list/get_task_output/<int:task_id>', methods=['GET'])
        def get_task_output(task_id):
            try:
                (errormsg, task_output) = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_task,
                        session['username'],
                        self.tasks_manager.get_task_output,
                        [int(task_id)]
                        )
                if errormsg != '': session['error_message'] += errormsg
            except:
                pass
            return(task_output)


        @self.app.route('/task_list/get_task_as_json/<int:task_id>', methods=['GET'])
        def get_task_as_json(task_id):
            try:
                (errormsg, task_as_jsonify) = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.get_task_as_jsonify,
                        session['username'],
                        self.tasks_manager.get_task_as_jsonify,
                        [int(task_id)]
                        )
                if errormsg != '': session['error_message'] += errormsg
            except Exception as e:
                print(e.message, None)
                pass
            return(task_as_jsonify)


        @self.app.route('/task_list/kill_task/<int:task_id>', methods=['GET'])
        def kill_task(task_id):
            session['error_message'] = ''
            try:
                (errormsg, tasks_dict) = self.manage_validator.check_permission_and_run(
                        self.permissions_manager.kill_task,
                        session['username'],
                        self.tasks_manager.kill_task,
                        [int(task_id)]
                        )
                if errormsg != '': session['error_message'] += errormsg
            except Exception as e:
                print(e.message, None)
                pass

            return redirect(url_for('get_tasks'))
