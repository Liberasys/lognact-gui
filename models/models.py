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



from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

sqladb = SQLAlchemy()

class Task(sqladb.Model):
    __tablename__ = 'task_list'
    id         = sqladb.Column(sqladb.Integer,  primary_key=True)
    user_id    = sqladb.Column(sqladb.Text,     unique = False)
    pid        = sqladb.Column(sqladb.Integer,  unique = False)
    command    = sqladb.Column(sqladb.Text,     unique = False)
    output     = sqladb.Column(sqladb.Text,     unique = False)
    status     = sqladb.Column(sqladb.Text,     unique = False) # running/ok/ko/disappeared
    start_date = sqladb.Column(sqladb.DateTime, unique = False)
    end_date   = sqladb.Column(sqladb.DateTime, unique = False)
    #thread_ident = sqladb.Column(sqladb.DateTime, unique = False)

    def __init__(self, id, user_id, pid, command, status = 'running', start_date = datetime.now()):
        self.id = id
        self.user_id = user_id
        self.pid = pid
        self.command = command
        self.output = ""
        self.status = status
        self.start_date = start_date
        self.end_date = None
        #self.thread_ident = thread_ident


#    def __repr__(self):
#        return {
#                'id':self.id,
#                'user_id':self.user_id,
#                'pid':self.pid,
#                'command':self.command,
#                'output':self.output,
#                'status':self.status,
#                'start_date':self.start_date,
#                'end_date': self.end_date
#                }
