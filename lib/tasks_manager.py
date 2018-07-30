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

import sys
sys.path.append('./models')
sys.path.append('./lib')
from models import Task, sqladb
from task_thread import TaskThread


class Tasks_manager():

    def __init__(self, db_uri):

        self.max_running_tasks_number = 20
        self.max_days_old_db_entries = 180
        self.utilities_timer = 10
        self.__db_uri = db_uri

    def update_disappeared_tasks(self):
        TaskThread.xt_update_disappeared_tasks(self.__db_uri)
        return('', None)

    def create_task(self, username, command):
        try:
            task = TaskThread(db_uri=self.__db_uri, username=username, command=command)
            return('', None)
        except Exception as e:
            return(e.message, None)

    def read_tasks(self):
        tasks_dict = {}
        #for instance in sqladb.session.query(Task).all().order_by(Task.id.amount.desc()).limit(50):
        for instance in sqladb.session.query(Task).all():
            tasks_dict[instance.id] = {
                                      'username': instance.username,
                                      'pid': instance.pid,
                                      'command': instance.command,
                                      'output': instance.output,
                                      'status': instance.status,
                                      'start_date': instance.start_date,
                                      'end_date': instance.end_date
                                      }
        return('', tasks_dict)


    def kill_task(self, task_id):
        try:
            return(TaskThread.xt_kill_pid_command_and_commit(self.__db_uri, task_id))
        except Exception as e:
            return(e.message, None)
        return("", None)


    def get_task_output(self, task_id):
        try:
            taskorm = sqladb.session.query(Task).get(task_id)
        except Exception as e:
            return(e.message, None)
        return ("", taskorm.output)


    def get_running_tasks(self):
        pass

    def vacuum_tasks(self):
        pass

    def set_max_day_old_db_entries(self, value):
        self.max_days_old_db_entries = value

    def set_max_running_task_number(self, value):
        self.max_running_tasks_number = value
