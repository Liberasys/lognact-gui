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
        self.__db_uri = db_uri
        self.__username = username
        self.__command = command
        if db_uri == None or username == None or command == None:
            raise ValueError('Cannot start a thread, not enough information.')
        self.start()

    ###########################################################################
    # NOTE : Every function beginning with xt_ are called externally.         #
    #        The DB makes the link between task threads and flask threads.    #
    ###########################################################################


    def __xt_get_db_session(db_uri):
        import sys
        sys.path.append('./models')
        from models import Task
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(db_uri, echo=False, connect_args={'timeout': 15})
        engine.echo = False
        Session = sessionmaker(bind=engine)
        dbsession = Session()
        return(dbsession)


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


    def __xt_get_pgid_number_of_tasks(pgid):
        import glob
        p_list = []
        for stat_file_path in glob.glob('/proc/[1-9]*/stat'):
            try:
                stat_file = open(stat_file_path, 'rt')
                stat = stat_file.readline().split()
                stat_file.close()
                if stat[4] == str(pgid):
                    p_list.append(stat[0])
            except Exception as e:
                print(e)
                pass
        return(len(p_list))


    def xt_kill_pid_command_and_commit(db_uri, id):
        import sys
        sys.path.append('./models')
        from models import Task
        from datetime import datetime
        #from flask_babel import gettext

        if id == None:
            id_text = "None"
        else:
            id_text = str(id)

        if thread_task_debug: print("KILL : xt_kill_pid_command_and_commit process id:", id_text)

        # Here we get task data with a sqlalchemy excecute in order to not
        # get a session which causes multithreads issues
        try:
            from models import Task
            from sqlalchemy import create_engine
            engine = create_engine(db_uri)
            result = engine.execute("select * from task_list where id=" + id_text).fetchone()
            task_pid = result['pid']
            task_pgid = os.getpgid(task_pid)
            task_command = result['command']
        except Exception as e:
            print(e.message)
            ## BUG in babel ? cannot use getttext in this context
            ##   File "/usr/lib/python3/dist-packages/flask_babel/__init__.py", line 214, in get_translations
            ##   babel = current_app.extensions['babel']
            ##   KeyError: 'babel'
            ##return((gettext("Unable to kill task id %(id)s, not found.", id=id_text), None))
            return("Unable to get task id data, abording killing task " + id, None)


        if thread_task_debug: print("Number of process in process group:", TaskThread.__xt_get_pgid_number_of_tasks(task_pgid))

        kill_result = TaskThread.__xt_kill_pid_command(task_pid, task_command)
        if  kill_result != ("", None):
            if thread_task_debug: print("Kill bad result:", kill_result)
            return(kill_result)
        else:
            # Wait for the thread termination
            if thread_task_debug: print("Wait for the thread termination")
            while(TaskThread.__xt_get_pgid_number_of_tasks(task_pgid) != 0):
                time.sleep(0.2)

            try:
                engine = create_engine(db_uri)
                result = engine.execute("UPDATE task_list SET status = " + "'killed'" + "where id=" + id_text)
                print(result)
            except Exception as e:
                print(e.message)
                return("Unable to set task status", None)
            return("", None)


    def xt_update_disappeared_tasks(db_uri):
        import sys
        sys.path.append('./models')
        from models import Task

        dbsession = TaskThread.__xt_get_db_session(db_uri)
        for instance in dbsession.query(Task).filter(Task.status == 'running').all():
            if not TaskThread.__xt_check_proc_exists(instance.pid, instance.command) \
              and instance.end_date == None:
                instance.status = "disappeared"
        dbsession.commit()
        dbsession.close()



    def run(self):
        # This is the thread in which we spawn a process and then we
        #   poll the process stdout/stderr.
        # Each time we can close the DB session we do it in order to
        #   free the sqlite DB.

        import time
        import sys
        sys.path.append('./models')
        from models import Task
        dbsession = TaskThread.__xt_get_db_session(self.__db_uri)
        ormtask = Task(self.__username, self.__command)
        dbsession.add(ormtask)
        dbsession.commit()

        # Run the process and get its PID
        process = Popen(ormtask.command, stdin=None, stdout=PIPE, stderr=STDOUT, shell=True, close_fds=True, preexec_fn=os.setsid)
        ormtask.start_date = datetime.now()
        ormtask.status = "running"
        ormtask.pid = process.pid
        if thread_task_debug: print("Started process:", ormtask.command, "-- pid", ormtask.pid)
        ormtask_id = ormtask.id
        dbsession.commit()
        dbsession.close()

        # poll its stdout/sterr
        last_commit_epoch = time.time()
        tmpoutbuf = ""
        while True:

            # Each second, we oppen a DB session and commit the
            # process output buffer.
            if ((time.time() - last_commit_epoch) > 1) :
                dbsession = TaskThread.__xt_get_db_session(self.__db_uri)
                ormtask = dbsession.query(Task).get(ormtask_id)
                ormtask.output = ormtask.output + tmpoutbuf
                dbsession.commit()
                dbsession.close()
                tmpoutbuf = ""
                last_commit_epoch = time.time()

            # In any case we poll a line from process stdout/stderr
            line = process.stdout.readline()
            line = line.rstrip()

            # If the readline returns None, then the process is ended
            #   and we get out of the polling loop
            if not line:
                break

            # If we have got something, we add it to the buffer of data to
            #   be commitied in db.
            if line != "":
                if thread_task_debug: print("    Stdout line:", line)
                tmpoutbuf = tmpoutbuf + line.decode("utf-8") + "\n"

        # We commit last output from Task
        dbsession = TaskThread.__xt_get_db_session(self.__db_uri)
        ormtask = dbsession.query(Task).get(ormtask_id)
        ormtask.output = ormtask.output + tmpoutbuf
        dbsession.commit()
        dbsession.close()
        tmpoutbuf = ""

        # Be shure that process exited
        process.wait()

        # Now process is ended, we set the status
        if thread_task_debug: print("Process return code:", process.returncode)
        dbsession = TaskThread.__xt_get_db_session(self.__db_uri)
        ormtask = dbsession.query(Task).get(ormtask_id)
        ormtask.output = ormtask.output + "-- Return code: " + str(process.returncode)
        ormtask.end_date = datetime.now()

        if process.returncode != -15:
            if process.returncode != 0:
                ormtask.status = "ko"
                if thread_task_debug: print("Process", ormtask.pid, "ended KO")
            else:
                ormtask.status = "ok"
                if thread_task_debug: print("Process", ormtask.pid, "ended OK")

        dbsession.commit()
        dbsession.close()
        del(ormtask)
        del(dbsession)






if __name__ == "__main__":

    from flask import Flask, request, jsonify
    from flask_babel import gettext
    import sys
    sys.path.append('./models')
    from models import Task, sqladb

    db_uri_filename = 'test_db.sqlite?timeout=15'
    db_uri_header = 'sqlite:///'
    db_uri_flask_path = './'
    db_uri_lib_path = '../'

    db_flask_uri = db_uri_header + db_uri_lib_path + db_uri_filename
    db_lib_uri = db_uri_header + db_uri_flask_path + db_uri_filename


    app = Flask(__name__)
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite/test_db.sqlite?check_same_thread=False'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_flask_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
