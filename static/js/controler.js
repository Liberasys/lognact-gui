








function run_node(){
  // implement this
}

// nodes page methods
var selected_node ="";
// delete the selected group
function delete_node(){
  callAjax("/nodes/delete_node/", '/nodes/');
}

function delete_var_from_node(var_name){
  callAjax("/nodes/delete_var/" + var_name, '/nodes/');
}

// nodes_groups page methods

//usuels vars
var selected_group = "";
var selected_node_from_nodes_list = "";
var selected_node_from_group_list = "";
// if not selected, set this group to the session and load nodes, vars corresponding
var old_selected_group;
function select_group(suffix, name) {
    id = name + suffix;
    selected_group = name;
    if (document.getElementById(old_selected_group)) {
        document.getElementById(old_selected_group).style.cssText = "color: black; background-color: white;";
    }
    old_selected_group = id;
    document.getElementById(id).style.cssText = "color: red; background-color: #F5F5F5;";
    if (suffix == '_from_groups_list'){
      callAjax("/nodes_groups/set_active_group/" + name , '/nodes_groups/');
    }
    else if (suffix == '_from_groups_list_in_playbook') {
      // implement this
    }

}

// on page reload set the current group into the javavascript var from the session
function set_active_data(groupname, nodename){
  if (groupname != ''){
    selected_group = groupname;
  }
  if (nodename != ''){
    selected_node = nodename;
  }
}

// set the selected node from node_not_in_group into the javavascript var
var old_selected_node_from_nodes_list;
function select_node(suffix, name) {
  id = name + suffix;
  selected_node_from_nodes_list = name;
    if (document.getElementById(old_selected_node_from_nodes_list)) {
        document.getElementById(old_selected_node_from_nodes_list).style.cssText = "color: black; background-color: white;";
    }
    old_selected_node_from_nodes_list = id;
    document.getElementById(id).style.cssText = "color: red; background-color: #F5F5F5";
    if (suffix == '_from_nodes_list'){
      callAjax("/nodes/set_active_node/" + name , '/nodes/');
    }
    else if (suffix == '_from_node_in_group_in_playbook') {
      // implement this
    }


}

// set the selected node from node_in_group into the javavascript var
var old_selected_node_from_group;
function select_node_from_group(suffix, name) {
  id = name + suffix;
  selected_node_from_group = name;
    if (document.getElementById(old_selected_node_from_group)) {
        document.getElementById(old_selected_node_from_group).style.cssText = "color: black; background-color: white;";
    }
    old_selected_node_from_group = id;
    document.getElementById(id).style.cssText = "color: red; background-color: #F5F5F5";
}

// delete the selected group
function delete_group(){
  callAjax("/nodes_groups/delete_group/", '/nodes_groups/');
}

// add the selected node into the selected group
function add_node_in_group(){
   if (selected_node_from_nodes_list != null) {
     callAjax("/nodes_groups/add_node/" + selected_node_from_nodes_list, '/nodes_groups/');
   }
}

// remove the selected node from the selected group
function remove_node_from_group(){
   if (selected_node_from_group != null) {
     callAjax("/nodes_groups/delete_node/" + selected_node_from_group, '/nodes_groups/');
   }
}

function delete_var_from_group(var_name){
  callAjax("/nodes_groups/delete_var/" + var_name, '/nodes_groups/');
}


// set the session's message alert
function set_alert(message, location) {
    document.getElementById('alert').innerHTML = '';
    callAjax("/set_error_message/" + message);
}

// Ajax method
function callAjax(request, location) {
   var xhttp;
   if (window.XMLHttpRequest) {
     // code for modern browsers
     xhttp = new XMLHttpRequest();
     } else {
     // code for IE6, IE5
     xhttp = new ActiveXObject("Microsoft.XMLHTTP");
   }
   xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
       var response = this.responseText;
       if (location != ''){
         self.location.href=location;
       }

     }
   };
   xhttp.open("GET", request, true);
   xhttp.send();
 }


 // Events methods
 $(document).on("click", ".open-modifyGroupVarDialog", function () {
      var var_from_group_id = $(this).data('id');
      $(".modal-body #varId").val( var_from_group_id );
 });

 $(document).on("click", ".open-modifyNodeVarDialog", function () {
      var var_from_node_id = $(this).data('id');
      $(".modal-body #varId").val( var_from_node_id );
 });
