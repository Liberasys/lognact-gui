import threading
import time
from datetime import datetime
import syslog
import os
import errno
import signal
from subprocess import Popen, PIPE, STDOUT
#from flask_babel import gettext

thread_task_debug = False

class TaskThread(threading.Thread):

    def __init__(self, db_uri = None, username = None, command = None):
        threading.Thread.__init__(self)
        self.__dburi = db_uri
        self.__dbsession = None
        self.__ormtask = None
        self.__mutex_taken = False
        #self.__waskilled = False
        #self.__thread_running = False
        self.start()

        if db_uri == None or username == None or command == None:
            raise ValueError('Cannot start a thread, not enough information.')

        import sys
        sys.path.append('./models')
        from models import Task
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(self.__dburi, echo=True)
        engine.echo = False
        Session = sessionmaker(bind=engine)
        self.__dbsession = Session()

        #for instance in self.__dbsession.query(Task).all():
        #    print(instance.id, instance.start_date, instance.username, instance.command)

        self.__ormtask = Task(username, command)
        self.__dbsession.add(self.__ormtask)
        self.__dbsession.commit()


    def __xt_get_proc_command_by_pid(pid):
        if pid != None and os.path.isdir("/proc/" + str(pid)):
            proc_command = open(os.path.join('/proc', str(pid), 'cmdline'), 'rb').read()
            proc_command = proc_command.decode("utf-8")
            proc_command = proc_command.replace(chr(0), ' ')
            if thread_task_debug: print("Found command from pid", pid, ":", proc_command)
            return(proc_command)
        else:
            if thread_task_debug: print("PID", pid, "does not exists")
            return(None)

    #
    # NOTE : every function beginning with xt_ are called externally
    #        the DB makes the link between task threads and flask threads
    #

    def __xt_check_proc_exists(pid, command):
        proc_command = TaskThread.__xt_get_proc_command_by_pid(pid)
        if pid == None or proc_command == None:
            return(False)
        elif proc_command.lower().find(command.lower()) < 0:
            return(False)
        return(True)


    def __xt_kill_pid_command(pid, command):
        #from flask_babel import gettext
        if command == None:
            command_text = "None"
        else:
            command_text = command

        if pid == None:
            pid_text = "None"
        else:
            pid_text = str(pid)

        if not TaskThread.__xt_check_proc_exists(pid, command):
            # BUG in babel ? cannot use getttext in this context
            #   File "/usr/lib/python3/dist-packages/flask_babel/__init__.py", line 214, in get_translations
            #   babel = current_app.extensions['babel']
            #   KeyError: 'babel'
            #return((gettext("Unable to kill process id %(pid)s : %(command)s. Process not found in system.", pid=pid_text, command=command_text), None))
            return((("Unable to kill process id " + pid_text + " : " + command_text + ". Process not found in system."), None))

        else:
            if thread_task_debug: print("KILL : Killing process", pid_text)
            # Send the signal to all the process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            if thread_task_debug: print("Killed : Process", pid_text, ":", command_text)
            return("", None)

    def xt_kill_pid_command_and_commit(db_uri, id):
        import sys
        sys.path.append('./models')
        from models import Task
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime
        #from flask_babel import gettext

        engine = create_engine(db_uri, echo=True)
        engine.echo = False
        Session = sessionmaker(bind=engine)

        if id == None:
            id_text = "None"
        else:
            id_text = str(id)

        # A small DB session in order to get Task ORM object
        dbsession = Session()
        taskorm = dbsession.query(Task).filter(Task.id == id).one()
        dbsession.close()
        # BUG in babel ? cannot use getttext in this context
        #   File "/usr/lib/python3/dist-packages/flask_babel/__init__.py", line 214, in get_translations
        #   babel = current_app.extensions['babel']
        #   KeyError: 'babel'
        #return((gettext("Unable to kill task id %(id)s, not found.", id=id_text), None))
        if taskorm == None:
            dbsession.close()
            return(("Unable to kill task id " + id_text + ", not found.", None))

        kill_result = TaskThread.__xt_kill_pid_command(taskorm.pid, taskorm.command)
        if  kill_result != ("", None):
            return(kill_result)
        else:
            while(TaskThread.__xt_check_proc_exists(taskorm.pid, taskorm.command)):
                time.sleep(0.2)
            time.sleep(0.5)

            # We have to open a new DB session here because the ORM object was
            # created in an other thread and have just been released.
            dbsession = Session()
            taskorm = dbsession.query(Task).filter(Task.id == id).one()
            taskorm.status = "killed"
            taskorm.end_date = datetime.now()
            dbsession.commit()
            dbsession.close()
            return("", None)

    def xt_update_disappeared_tasks(db_uri):
        import sys
        sys.path.append('./models')
        from models import Task
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime
        #from flask_babel import gettext

        engine = create_engine(db_uri, echo=True)
        engine.echo = False
        Session = sessionmaker(bind=engine)
        dbsession = Session()

        for instance in dbsession.query(Task).filter(Task.status == 'running').all():
            if not TaskThread.__xt_check_proc_exists(instance.pid, instance.command):
                instance.status = "disappeared"
        dbsession.commit()
        dbsession.close()



    def run(self):
        # Run the process and get its PID
        self.__get_mutex()
        #self.__ormtask.status = 'running'
        #self.__ormtask.start_date = datetime.now()
        #self.__thread_running = True
        process = Popen(self.__ormtask.command, stdin=None, stdout=PIPE, stderr=STDOUT, shell=True, close_fds=True, preexec_fn=os.setsid)
        self.__ormtask.pid = process.pid

        # Loop on stderr+stdout lines of the process
        if thread_task_debug: print("Started process:", self.__ormtask.command, "-- pid", self.__ormtask.pid)
        self.__dbsession.commit()
        self.__release_mutex()

        # poll its stdout/sterr
        while True:
            line = process.stdout.readline()
            line = line.rstrip()
            if line != "":
                if thread_task_debug: print("    Stdout line:", line)
                self.__get_mutex()
                self.__ormtask.output = self.__ormtask.output + line.decode("utf-8") + "\n"
                self.__dbsession.commit()
                self.__release_mutex()
            if not line:
                break
        process.wait()

        # Now process is ended, we set the status
        if thread_task_debug: print("Process return code:", process.returncode)
        self.__get_mutex()
        self.__ormtask.output = self.__ormtask.output + "-- Return code: " + str(process.returncode)
        self.__ormtask.end_date = datetime.now()
        #if self.__waskilled != True:
        if self.__ormtask.status != "killed":
            if process.returncode != 0:
                self.__ormtask.status = "ko"
                if thread_task_debug: print("Process", self.__ormtask.pid, "ended KO")
            else:
                self.__ormtask.status = "ok"
                if thread_task_debug: print("Process", self.__ormtask.pid, "ended OK")
            #self.__thread_running = False
        self.__dbsession.commit()
        self.__dbsession.close()
        self.__release_mutex()


    #def kill(self):
    #    pid = self.get_pid()
    #    command = self.get_command()

    #    if command == None:
    #        command_text = "None"
    #    else:
    #        command_text = command

    #    if pid == None:
    #        pid_text = "None"
    #    else:
    #        pid_text = str(pid)

    #    if self.get_status() != "running":
    #        return(gettext("Unable to kill process id %(pid)s : %(command)s. Process was not running.",
    #                       pid=str(pid_text),
    #                       command=command_text),
    #               None)

    #    self.set_waskilled()
    #    (error_text, data) = TaskThread.__xt_kill_pid_command(pid, command)
    #    if error_text != "":
    #        return(error_text, data)
    #    elif self.__thread_running == True:
    #        self.join()
    #    else:
    #        while(TaskThread.__xt_check_proc_exists(pid, command)):
    #            time.sleep(0.2)
    #        time.sleep(0.5)
    #    self.__thread_running = False
    #    self.set_end_killed()
    #    self.__dbsession.commit()
    #    self.__dbsession.close()
    #    return("", None)


    #def get_pid(self):
    #    self.__get_mutex()
    #    pid = copy(self.__ormtask.pid)
    #    self.__release_mutex()
    #    return(pid)

    #def get_command(self):
    #    self.__get_mutex()
    #    command = copy(self.__ormtask.command)
    #    self.__release_mutex()
    #    return(command)

    #def get_status(self):
    #    self.__get_mutex()
    #    status = copy(self.__ormtask.status)
    #    self.__release_mutex()
    #    return(status)

    def __set_end_ok(self): self.__set_end("ok")
    def __set_end_ko(self): self.__set_end("ko")
    #def set_end_killed(self): self.__set_end("killed")
    def set_end_disappeared(self): self.__set_end("disappeared")
    def __set_end(self, status):
        self.__get_mutex()
        self.__ormtask.status = status
        self.__ormtask.end_date = datetime.now()
        self.__dbsession.commit()
        self.__release_mutex()
        if thread_task_debug: print("Set task status of PID", self.__ormtask.pid, "to:", status)

    def get_data_dict(self):
        out_data = {}
        self.__get_mutex()
        out_data['id'] = self.__ormtask.id
        out_data['username'] = self.__ormtask.username
        out_data['pid'] = self.__ormtask.pid
        out_data['command'] = self.__ormtask.command
        out_data['output'] = self.__ormtask.output
        out_data['status'] = self.__ormtask.status
        out_data['start_date'] = self.__ormtask.start_date
        out_data['end_date'] = self.__ormtask.end_date
        self.__release_mutex()
        return(out_data)

#    def set_waskilled(self):
#        self.__get_mutex()
#        self.__waskilled = True
#        self.__release_mutex()

    def __get_mutex(self):
        """ Tries to get the mutex on the data """
        mutex_timeout = 5
        start_epoch = time.time()
        got_mutex = False
        while ((time.time() - start_epoch) < mutex_timeout) and \
              (got_mutex == False):
            if self.__mutex_taken == True:
                if thread_task_debug: print("Mutex busy...")
            else:
                got_mutex = True
                self.__mutex_taken = False
                if thread_task_debug: print("Got mutex.")
            time.sleep(0.2)
        return got_mutex

    def __release_mutex(self):
        """ Releases the mutex on the data """
        self.__mutex_taken = False
        if thread_task_debug: print("Mutex released.")






if __name__ == "__main__":

    from flask import Flask, request, jsonify
    from flask_babel import gettext
    import sys
    sys.path.append('./models')
    from models import Task, sqladb

    db_uri_filename = 'test_db.sqlite'
    db_uri_header = 'sqlite:///'
    db_uri_flask_path = './'
    db_uri_lib_path = '../'

    db_flask_uri = db_uri_header + db_uri_lib_path + db_uri_header
    db_lib_uri = db_uri_header + db_uri_flask_path + db_uri_header


    app = Flask(__name__)
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite/test_db.sqlite?check_same_thread=False'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_flask_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    #app.config['SQLALCHEMY_ECHO'] = True

    sqladb.app = app
    sqladb.init_app(app)

    #sqladb.drop_all()
    sqladb.create_all()
    sqladb.session.commit()
    time.sleep(1)

    TaskThread.xt_update_disappeared_tasks(db_lib_uri)


    task1 = TaskThread(db_uri=db_lib_uri, username='user1', command="ping -mLQSKDJQMSLKj 1 127.0.0.1")
    task2 = TaskThread(db_uri=db_lib_uri, username='user2', command="ping -c 7 127.0.0.1")
    task3 = TaskThread(db_uri=db_lib_uri, username='user3', command="ping -c 15 127.0.0.1")

    time.sleep(1)
    #print(task1.get_data_dict(), task1.get_data_dict(), task1.get_data_dict())
    #print(task1.get_data_dict())


    @app.route('/ktasks', methods=['GET'])
    def kill_tasks():
        assert request.method == 'GET'
        out = ""
        for instance in sqladb.session.query(Task).filter(Task.status == "running"):
            #(errormsg, object) = kill_pid_command(instance.pid, instance.command)
            (errormsg, object) = TaskThread.xt_kill_pid_command_and_commit(db_lib_uri, instance.id)
            out = out + "killed task " + str(instance.pid) + " : " + instance.command + " -- " + errormsg + "<br>"
        return(out)


    @app.route('/ctask', methods=['GET'])
    def create_task():
        assert request.method == 'GET'
        taskn = TaskThread(db_uri=db_lib_uri, username='user3', command="ping -c 15 127.0.0.1")
        return('OK')

    @app.route('/gtasks', methods=['GET'])
    def get_tasks():
        TaskThread.xt_update_disappeared_tasks(db_lib_uri)
        out = ""
        out = out + "<style>\n"
        out = out + 'p {font-family:Consolas, monospace;}\n'
        out = out + "table, th, td {border: 1px solid black;}\n"
        out = out + "th, td {padding: 15px;}\n"
        out = out + "th {text-align: left;}\n"
        out = out + "table {border-spacing: 5px;}\n"
        out = out + "</style>\n"
        out = out + '<table style="width:100%">\n'
        out = out + "  <tr>\n"
        out = out + "    <th>" + "ID"         + "</th>\n" + \
                    "    <th>" + "USERNAME"   + "</th>\n" + \
                    "    <th>" + "PID"        + "</th>\n" + \
                    "    <th>" + "COMMAND"    + "</th>\n" + \
                    "    <th>" + "OUTPUT"     + "</th>\n" + \
                    "    <th>" + "STATUS"     + "</th>\n" + \
                    "    <th>" + "START DATE" + "</th>\n" + \
                    "    <th>" + "END DATE"   + "</th>\n"
        out = out + "  </tr>"
        for instance in sqladb.session.query(Task).all():
            out = out + "  <tr>\n"
            out = out + "    <th>" + str(instance.id)         + "</th>\n" + \
                        "    <th>" + instance.username        + "</th>\n" + \
                        "    <th>" + str(instance.pid)        + "</th>\n" + \
                        "    <th>" + instance.command         + "</th>\n" + \
                        "    <th>" + instance.output.replace("\n", "<br>")          + "</th>\n" + \
                        "    <th>" + instance.status          + "</th>\n" + \
                        "    <th>" + str(instance.start_date) + "</th>\n" + \
                        "    <th>" + str(instance.end_date)   + "</th>\n"
            out = out + "  </tr>"
        return(out)


    app.run()

    print("===================RUN=================")
