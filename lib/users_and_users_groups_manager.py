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



from user import User
from users_group import Users_group

from flask_babel import gettext

class Users_and_users_groups_manager():


    def __init__(self):
                self.users_dict = {}
                self.groups_dict = {}

    # user
    def add_user(self, name, password, su):
        try:
            user = User()
            user.set_user(name, password, su)
            self.users_dict[name] = user
            return (gettext('User %(name)s added successfully', name = name), user)
        except:
            return (gettext('Error encountered with adding user : %(name)s', name = name), None)


    def get_users(self):
        pass

    def get_user(self, name):
        try:
            return ("", self.users_dict[name])
        except KeyError:
            return (gettext('User %(name)s not found', name = name), None)

    def delete_user(self, name):
        pass

    # users_group
    def add_users_group(self, name):
        pass

    def get_users_groups(self):
        pass

    def get_users_group(self, name):
        pass

    def delete_users_group(self, name):
        pass

    def add_user_in_users_group(self, user_name, users_groups_name):
        pass
