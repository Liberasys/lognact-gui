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



class User():

    def __init__(self):
        self.name = ""
        self.password = ""
        self.su = False
        self.auths_dict = {
                            'read': False,
                            'write': False,
                            'execute':False,
                        }



    def set_user(self, name, password, su):
        self.name = name
        self.password = password
        self.su = su

    def get_name(self):
        return self.name

    def get_password(self):
        return self.password

    def get_auths_dict(self):
        return self.auths_dict

    def set_su(self, boolean):
        self.su = boolean

    def get_su(self):
        return self.su
