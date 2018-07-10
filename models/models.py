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

from datetime import datetime

import sys
if 'flask' in sys.modules:
    print("Model imported within Flask")
    from sqlalchemy import Column, Integer, String, Text, DateTime
    from flask_sqlalchemy import SQLAlchemy
    sqladb = SQLAlchemy()
    inherit = sqladb.Model
else:
    print("Model imported without Flask")
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Integer, String, Text, DateTime
    sqladb = declarative_base()
    inherit = sqladb

class Task(inherit):
    __tablename__ = 'task_list'
    id         = Column(Integer,  unique=True, autoincrement=True, primary_key=True)
    username   = Column(Text,     unique=False)
    pid        = Column(Integer,  unique=False)
    command    = Column(Text,     unique=False)
    output     = Column(Text,     unique=False)
    status     = Column(Text,     unique=False) # running/ok/ko/disappeared
    start_date = Column(DateTime, unique=False)
    end_date   = Column(DateTime, unique=False)

    def __init__(self, username, command):
        # self.id is generated
        self.username = username
        self.pid = None
        self.command = command
        self.output = ''
        self.status = 'running'
        self.start_date = datetime.now()
        self.end_date = None
