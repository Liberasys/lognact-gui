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
import copy
from flask_babel import gettext
from yaml_file_syncer import YamlFileSyncer
from yaml_dump_like_ansible import yaml_dump_like_ansible
from nodes_and_groups import Group, Node, NodeOrGroup

class Inventory():
    """
    Manages Ansible inventory file (with node-group association) and nodes/groups objects
    """
    def __init__(self, ansible_dir_path, inventory_file_subpath):
        self.__ansible_dir_path = ansible_dir_path
        self.__groups_dict = {}
        self.__nodes_dict = {}
        self.__refresh_timeout = 10

        #self.__last_inventory_refresh_timestamp = time.time()
        self.__inventory_file = YamlFileSyncer(self.__ansible_dir_path + "/" + inventory_file_subpath)
        if self.__inventory_file.init_error_return != "":
            raise ValueError(self.__inventory_file.init_error_return)
        (error_text, nothing) = self.__populate_from_files()
        if error_text != "":
            raise ValueError(error_text)


    def __del__(self):
        pass

    # Read the inventory, get groups and hosts and read group_vars and host_vars
    # from their files, and populate group and node dictionnaries with their
    # corresponding objects.
    def __populate_from_files(self):
        #print(self.__inventory_file.dump_as_text())
        (error_text, data) = self.__inventory_file.read()
        if error_text != "": return(error_text, None)
        if data == "" or data == None or "all" not in data:
            data = {"all": {}}
        if "all" in data:
            if "children" in data["all"]:
                for group_name, group_data in data["all"]["children"].items():
                    #print("found group :" + group_name)
                    self.add_group(group_name, sync=False)
                    if "hosts" in data["all"]["children"][group_name]:
                        for host_name, host_data in data["all"]["children"][group_name]["hosts"].items():
                            if host_name not in self.__nodes_dict:
                                (error_text, entity) = self.add_node(host_name, sync=False)
                                if error_text != "": return(error_text, None)
                            (error_text, entity) = self.add_node_name_in_group_name(host_name, group_name, sync=False)
                            if error_text != "": return(error_text, None)
            if "hosts" in data["all"]:
                for host_name, host_data in data["all"]["hosts"].items():
                    #print("found hostname: " + host_name)
                    if host_name not in self.__nodes_dict:
                        (error_text, entity) = self.add_node(host_name, sync=False)
                        if error_text != "": return(error_text, None)
        return("", None)


    def __write_file(self):
        (error_text, new_inventory_content) = self.get_new_inventory_content()
        if error_text != "": return(error_text, None)
        (error_text, data) = self.__inventory_file.write(new_inventory_content)
        if error_text != "": return(error_text, None)
        return("", None)
        pass


    def get_new_inventory_content(self):
        (error_text, old_data) = self.__inventory_file.read()
        if error_text != "": return(error_text, None)
        data = {"all": {}}
        # Add groups from __groups_dict
        if self.__is_a_group_not_empty:
            data["all"]["children"] = {}
            for group_name, group in self.__groups_dict.items():
                if group.nodes_list != []:
                    data["all"]["children"][group_name] = {}
                    data["all"]["children"][group_name]["hosts"] = {}
                    for node in group.nodes_list:
                        data["all"]["children"][group_name]["hosts"][node.name] = {}
        # Add nodes from __nodes_dict
        if self.__nodes_dict != []:
            data["all"]["hosts"] = {}
            for node_name, node in self.__nodes_dict.items():
                data["all"]["hosts"][node_name] = {}
        # Add old inventories vars
        if old_data != None and "all" in old_data and "vars" in old_data["all"]:
            data["all"]["vars"] = old_data["all"]["vars"]
        return("", data)


    def __is_a_group_not_empty(self):
        for group_name, group in self.__groups_dict.items():
            if group.nodes_list != []:
                return(True)
        return(False)



    def dump_groups(self):
        data = {}
        for group_name, group_instance in self.__groups_dict.items():
            data[group_name] = {}
            data[group_name]["vars"] = group_instance.vars_dict
            data[group_name]["members"] = group_instance.get_nodes_names_list()
        return(data)


    def dump_nodes(self):
        data = {}
        for node_name, node_instance in self.__nodes_dict.items():
            data[node_name] = {}
            data[node_name]["vars"] = node_instance.vars_dict
        return(data)


    def dump(self):
        data = {}
        data["groups"] = self.dump_groups()
        data["nodes"] = self.dump_nodes()
        return(data)


    def get_group_names(self):
        return(("", list(self.__groups_dict.keys())))


    def get_node_names(self):
        return(("", list(self.__nodes_dict.keys())))


    def __get_class_and_dict_from_entity_type(self, type):
        assert type == "group" or type == "node"
        if type == "group":
            entity_dict = self.__groups_dict
            refclass = Group
        if type == "node":
            entity_dict = self.__nodes_dict
            refclass = Node
        return(refclass, entity_dict)


#
# Add and del group/node
# Get group/node object by its name
#
    def add_group(self, group_name, sync=True):
        return(self.__add_entity("group", group_name, sync))
    def add_node(self, node_name, sync=True):
        return(self.__add_entity("node", node_name, sync))
    def __add_entity(self, entity_type, entity_name, sync=True):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        if entity_name in entity_dict:
            return((gettext("The %(entity_type)s \"%(entity_name)s\" already exists", entity_type=entity_type, entity_name=entity_name), None))
        else:
            new_entity = refclass(self.__ansible_dir_path, entity_name)
            if new_entity.init_error_return != "":
                return((new_entity.init_error_return, None))
            entity_dict[entity_name] = new_entity
            if sync == True:
                (error_text, nothing) = new_entity.write()
                if error_text != "" : return(error_text, None)
                (error_text, nothing) = self.__write_file()
                if error_text != "" : return(error_text, None)
            return(("", None))


    def get_group_by_name(self, group_name):
        return(self.__get_entity_by_name("group", group_name))
    def get_node_by_name(self, node_name):
        return(self.__get_entity_by_name("node", node_name))
    def __get_entity_by_name(self, entity_type, entity_name):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        if entity_name not in entity_dict:
            return((gettext("The %(entity_type)s \"%(entity_name)s\" does not exists.", entity_type=entity_type, entity_name=entity_name), None))
        else:
            return("", entity_dict[entity_name])


    def del_group_by_name_(self, group_name, sync=True):
        return(self.__del_entity_by_name_("group", group_name, sync))
    def del_node_by_name_(self, node_name, sync=True):
        return(self.__del_entity_by_name_("node", node_name, sync))
    def __del_entity_by_name_(self, entity_type, entity_name, sync=True):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, entity) = self.__get_entity_by_name(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        if entity_type == "node": # if we are removing a node, we first remove if from groups containing it
            for group_name, group_instance in self.__groups_dict.items():
                group_instance.remove_node(entity)
        if sync == True:
            (error_text, nothing) = self.__write_file()
            if error_text != "" :
                return(error_text, None)
        del entity_dict[entity_name]
        del entity
        return(("", None))


#
# Vars_dict : get and set by group/node name
#
    def get_group_by_name_vars_dict(self, group_name):
        return(self.__get_entity_by_name_vars_dict("group", group_name))
    def get_node_by_name_vars_dict(self, node_name):
        return(self.__get_entity_by_name_vars_dict("node", node_name))
    def __get_entity_by_name_vars_dict(self, entity_type, entity_name):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, entity) = self.__get_entity_by_name(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        return("", entity.vars_dict)

    def set_group_by_name_vars_dict(self, group_name, vars_dict, sync=True):
        return(self.__set_entity_by_name_vars_dict("group", group_name, vars_dict, sync))
    def set_node_by_name_vars_dict(self, node_name, vars_dict, sync=True):
        return(self.__set_entity_by_name_vars_dict("node", group_name, vars_dict, sync))
    def __set_entity_by_name_vars_dict(self, entity_type, entity_name, vars_dict, sync=True):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, entity) = self.__get_entity_by_name(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        entity.vars_dict = copy.deepcopy(vars_dict)
        if sync == True:
            (error_text, nothing) = entity.write()
            if error_text != "" : return(error_text, None)
        return("", None)


#
# Vars_dict key/value : get/set/del by group/node name and key (=variable) name
#
    def update_group_by_name_var(self, group_name, var_name, var_value, sync=True):
        return(self.__update_entity_by_name_var("group", group_name, var_name, var_value, sync))
    def update_node_by_name_var(self, node_name, var_name, var_value, sync=True):
        return(self.__update_entity_by_name_var("node", node_name, var_name, var_value, sync))
    def __update_entity_by_name_var(self, entity_type, entity_name, var_name, var_value, sync=True):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, entity) = self.__get_entity_by_name(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        (entity.vars_dict)[var_name] = var_value
        if sync == True:
            (error_text, nothing) = entity.write()
            if error_text != "" : return(error_text, None)
        return("", None)

    def get_group_by_name_value(self, group_name, var_name):
        return(self.__get_entity_by_name_value("group", group_name, var_name))
    def get_node_by_name_value(self, node_name, var_name):
        return(self.__get_entity_by_name_value("node", node_name, var_name))
    def __get_entity_by_name_value(self, entity_type, entity_name, var_name):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, var_dict) = self.__get_entity_by_name_vars_dict(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        if var_name not in var_dict:
            return((gettext("The %(entity_type)s \"%(entity_name)s\" does not contain \"%(var_name)s\" variable. Cannot get its value.",
                    entity_type=entity_type, entity_name=entity_name, var_name=var_name), None))
        else:
            return("", var_dict[var_name])

    def del_group_by_name_var(self, group_name, var_name, sync=True):
        return(self.__del_entity_by_name_var("group", group_name, var_name, sync))
    def del_node_by_name_var(self, node_name, var_name, sync=True):
        return(self.__del_entity_by_name_var("node", node_name, var_name, sync))
    def __del_entity_by_name_var(self, entity_type, entity_name, var_name, sync=True):
        (refclass, entity_dict) = self.__get_class_and_dict_from_entity_type(entity_type)
        (error_text, entity) = self.__get_entity_by_name(entity_type, entity_name)
        if error_text != "" : return(error_text, None)
        if var_name not in entity.vars_dict:
            return((gettext("The %(entity_type)s \"%(entity_name)s\" does not contain \"%(var_name)s\" variable. Cannot remove it.",
                    entity_type=entity_type, entity_name=entity_name, var_name=var_name), None))
        else:
            del (entity.vars_dict)[var_name]
            if sync == True:
                (error_text, nothing) = entity.write()
                if error_text != "" : return(error_text, None)
            return("", None)

#
# Nodes group management
#
    def add_node_name_in_group_name(self, node_name, group_name, sync=True):
        (error_text, node) = self.get_node_by_name(node_name)
        if error_text != "" : return(error_text, None)
        (error_text, group) = self.get_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        if node_name in group.get_nodes_names_list():
            return((gettext("The group \"%(group_name)s\" already contains \"%(node_name)s\". Cannot add it.",
                group_name=group_name, node_name=node_name), None))
        else:
            group.add_node(node)
        if sync == True:
            (error_text, nothing) = self.__write_file()
            if error_text != "" : return(error_text, None)
        return(("", None))

    def remove_node_name_in_group_name(self, node_name, group_name, sync=True):
        (error_text, node) = self.get_node_by_name(node_name)
        if error_text != "" : return(error_text, None)
        (error_text, group) = self.get_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        if node_name not in group.get_nodes_names_list():
            return((gettext("The group \"%(group_name)s\" does not contain node \"%(node_name)s\". Cannot remove it.",
                group_name=group_name, node_name=node_name), None))
        else:
            group.remove_node(node)
            if sync == True:
                (error_text, nothing) = self.__write_file()
                if error_text != "" : return(error_text, None)
            return(("", None))


    def get_nodes_in_group_by_name(self, group_name):
        (error_text, group) = self.get_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        return(("", group.nodes_list))

    def get_nodes_names_in_group_by_name(self, group_name):
        (error_text, group) = self.get_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        return("", group.get_nodes_names_list())

    def get_nodes_not_in_group_by_name(self, group_name):
        (error_text, nodes_in_group_list) = self.get_nodes_in_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        return("", [item for item in self.__nodes_dict.values() if item not in nodes_in_group_list])

    def get_nodes_names_not_in_group_by_name(self, group_name):
        (error_text, nodes_names_in_group_list) = self.get_nodes_names_in_group_by_name(group_name)
        if error_text != "" : return(error_text, None)
        return("", [item for item in self.__nodes_dict.keys() if item not in nodes_names_in_group_list])



if __name__ == "__main__":
    inventory = Inventory("./ansible", "./inventories/liberasys.yml")
    print("Instanciation passed.")

    print(inventory.add_node("node1"))
    print(inventory.add_node("node1"))
    print(inventory.add_node("node2"))
    print(inventory.add_node("node3"))

    print(inventory.add_group("group1"))
    print(inventory.add_group("group2"))

    print("nodes", inventory.get_node_names())
    print(inventory.del_node_by_name_("node1"))
    print("nodes after del node1", inventory.get_node_names())
    print(inventory.del_node_by_name_("node3"))
    print("nodes after del node3", inventory.get_node_names())

    print(inventory.del_group_by_name_("badgroup"))
    print(inventory.del_group_by_name_("group1"))
    print(inventory.del_group_by_name_("group1"))

    print(inventory.update_node_by_name_var('node2', 'var1', 'value1'))

    print(inventory.set_group_by_name_vars_dict("group2", {"var1": "value1", "var2": "value2"}))
    print(inventory.get_group_by_name_vars_dict("group2"))
    print(inventory.update_group_by_name_var("group2", "var1", "value1updated"))
    print(inventory.get_group_by_name_value("group2", "var1"))
    print(inventory.get_group_by_name_vars_dict("group2"))
    print(inventory.del_group_by_name_var("group2", "var1"))
    print(inventory.get_group_by_name_vars_dict("group2"))

    print(inventory.add_node_name_in_group_name("node2", "group2"))
    print(inventory.get_nodes_in_group_by_name("group2"))
    print(inventory.get_nodes_not_in_group_by_name("group2"))
    print(inventory.get_nodes_names_in_group_by_name("group2"))
    print(inventory.get_nodes_names_not_in_group_by_name("group2"))

    print(inventory.remove_node_name_in_group_name("node2", "group2"))
    print(inventory.get_nodes_names_in_group_by_name("group2"))
    print(inventory.get_nodes_names_not_in_group_by_name("group2"))
    print(inventory.add_node_name_in_group_name("node2", "group2"))

    print("")
    print(yaml_dump_like_ansible(inventory.dump()))

    print("")
    (error_text, data) = inventory.get_new_inventory_content()
    if error_text != "":
        print(error_text)
    else:
        print(yaml_dump_like_ansible(data))
