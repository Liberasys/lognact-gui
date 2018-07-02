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




import yaml
import time
import logging
import pathlib
from flask_babel import gettext
from yaml_dump_like_ansible import yaml_dump_like_ansible

class YamlFileSyncer():
    """
    Reads and writes a YAML file, with mutex managment
    """

    def __init__(self, file_path):
        self.__file_path = file_path
        self.__mutex_enabled = False
        self.init_error_return = ""
        # Create paths if needed
        file_purepath = pathlib.PurePosixPath(self.__file_path)
        file_dir = file_purepath.parent
        pathlib.Path(file_dir).mkdir(parents=True, exist_ok=True)

        # Always try to create file if not exists
        try:
            file = open(self.__file_path, 'x')
            file.close()
        except FileExistsError:
            pass
        except Exception as e:
            logging.error("Cannot create" + self.__file_path + " -- " + str(e))
            self.init_error_return = ((gettext("Cannot create file: %(file_path)s.", file_path=self.__file_path)))
        self.init_error_return = ""


    def __get_mutex(self):
        mutex_timeout = 5
        start_epoch = time.time()
        got_mutex = False
        while ((time.time() - start_epoch) < mutex_timeout) and \
              (got_mutex == False):
            if self.__mutex_enabled == False:
                self.__mutex_enabled = True
                got_mutex = True
            time.sleep(0.2)
        if got_mutex == False:
            logging.warning("Unable to get mutex on file: " + self.__file_path)
            return((gettext("Unable to get mutex on file: %(file_path)s.", file_path=self.__file_path), None))
        return("", None)


    def __release_mutex(self):
        self.__mutex_enabled = False


    def read(self):
        data = None
        (error_text, nothing) = self.__get_mutex()
        if error_text != "" : return(error_text, None)
        try:
            with open(self.__file_path, 'r') as yaml_file:
                data = yaml.load(yaml_file.read())
        except Exception as e:
            logging.error("Cannot open or read " + self.__file_path + " -- " + str(e))
            return((gettext("Cannot read file : %(file_path)s.", file_path=self.__file_path), None))
        yaml_file.close()
        self.__release_mutex()
        return("", data)


    def write(self, data):
        (error_text, nothing) = self.__get_mutex()
        if error_text != "" : return(error_text, None)
        try:
            with open(self.__file_path, 'w+') as yaml_file:
                yaml_file.write(yaml_dump_like_ansible(data))
        except Exception as e:
            logging.error("Cannot open or write " + self.__file_path + " -- " + str(e))
            return((gettext("Cannot open or write file: %(file_path)s.", file_path=self.__file_path), None))
            return(None)
        yaml_file.close()
        self.__release_mutex()
        return("", data)


    def dump_as_text(self):
        return(yaml_dump_like_ansible(self.read()))


if __name__ == "__main__":
    data = {
           'key1': 'value1',
           'key2': 'value2',
           'key3': {
                   'key3.1': 'value3.1',
                   'key3.2': 'value3.2'
                   },
            'key4': 'value4'
            }


    yaml_file = YamlFileSyncer('./test.yml')
    print(yaml_file.init_error_return)
    print(yaml_file.write(data))
    data['key2'] = 'value2modified'
    print(yaml_file.write(data))
    print(yaml_file.read())
