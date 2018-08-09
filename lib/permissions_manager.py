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




from flask import session
import hash_source
from flask_babel import gettext

class Permissions_manager():

    def __init__(self, user_manager, inventory):
        self.user_manager = user_manager
        self.inventory = inventory
        self.permission_dict = {}


    def set_permission(self,fx_permission_mgr_args):
        self.permission_dict[(fx_permission_mgr_args[0],
                             fx_permission_mgr_args[1])] = fx_permission_mgr_args[2]


    def connect(self, fx_permission_mgr_args):
        request = self.user_manager.get_user(fx_permission_mgr_args[0])
        if request[1] is not None:
            if request[1].get_password() == hash_source.hash(fx_permission_mgr_args[1]):
                session['username'] = request[1].get_name()
            else:
                return gettext('wrong password')
        return request[0]

    # nodes
    def get_node_names(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def add_node(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def del_node_by_name_(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_node_by_name_vars_dict(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def update_node_by_name_var(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def del_node_by_name_var(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)


    def run_staging(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)




    # nodes_groups
    def get_nodes_groups(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def set_nodes_group(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_group_names(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def add_group(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def del_group_by_name_(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_nodes_in_group_by_name(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_nodes_names_in_group_by_name(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_nodes_names_not_in_group_by_name(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def delete_nodes_group(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def add_node_name_in_group_name(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def remove_node_name_in_group_name(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_group_by_name_vars_dict(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def set_group_by_name_vars_dict(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def update_group_by_name_var(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def del_group_by_name_var(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    #users_manager
    def get_users(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def add_user(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def set_user(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def delete_user(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def set_auth(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def playbookk(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_tasks(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_task(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def get_task_as_jsonify(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)

    def kill_task(self, fx_permission_mgr_args):
        return self.__is_su(fx_permission_mgr_args)


    def __is_su(self, user):
        request = self.user_manager.get_user(user)
        if request[1] is not None:
            if request[1].get_su():
                return None
            else:
                return gettext('permission denied')
        else :
            return request[0]
