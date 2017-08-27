function loadResults() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            update_tasks(this.responseText);
        }
    };
    var results_url = api_url + "/result/" + job_id;
    xhttp.open("GET", results_url);
    xhttp.send();
}

function remove(elem) {
    if (elem != null) {
        return elem.parentNode.removeChild(elem);
    }
}

function update_tasks(response) {
    var response = JSON.parse(response);
    var results = response['results'];
    // Update symbols
    for (var i = 0; i < results.length; i++){
        var uniprot_id = results[i].uniprot_id;
        var li = document.querySelector("#li_" + uniprot_id);

        // If contaminant is already complete, no update
        if ("running".match(li.className)) {
            if (results[i].status != "Running"){
                remove(li.querySelector(".fa_progress"));
                li.classList.remove("running");
            }
            // Build content of popover
            var popover_content = "<dl>";
            if (results[i].percent == 0) {
                popover_content += "<dt>No solution</dt>";
            } else {
                // Update indicator
                var indicator = li.querySelector(".fa_result");
                indicator.classList.remove(
                    "fa-times-circle", "failure",
                    "fa-question-circle", "warning",
                    "fa-check-circle", "success");
                // percent_threshold is defined in result.html by django tag
                if (results[i].percent > percent_threshold) {
                    indicator.className += " fa-check-circle success";
                } else { // We already know percent != 0
                    indicator.className += " fa-question-circle warning";
                }

                // Update popover content
                popover_content += "<dt>Percent</dt>";
                popover_content += "<dd>" + results[i].percent + "</dd>";
                popover_content += "<dt>Q factor</dt>";
                popover_content += "<dd>" + results[i].q_factor + "</dd>";
                popover_content += "<dt>Space group</dt>";
                popover_content += "<dd>" + results[i].space_group + "</dd>";

                if (results[i].files_available == "True") {
                    popover_content += "<dt>Files</dt>";
                    task_details = "?id=" + job_id
                        + "&uniprot_id=" + results[i].uniprot_id
                        + "&space_group=" + results[i].space_group
                        + "&pack_nb=" + results[i].pack_number;
                    pdb_url = api_url + "/final_pdb" + task_details;
                    mtz_url = api_url + "/final_mtz" + task_details;
                    popover_content += "<dd><a href=\"" + pdb_url + "\">PDB</a></dd>";
                    popover_content += "<dd><a href=\"" + mtz_url + "\">MTZ</a></dd>";
                    task_name = results[i].uniprot_id + '_'
                        + results[i].pack_number + '_'
                        + results[i].space_group
                    ugl_url = uglymol_url + task_name;
                    popover_content += "<dd><a href=\"" + ugl_url + "\">Uglymol (beta)</a></dd>";
                }
            }
            popover_content += "</dl>";
            li.querySelector("a").setAttribute("data-content", popover_content);
        }
    }

    // Test if messages is empty
    if ('messages' in response) {
        var messages = response['messages'];
        var pl_messages = document.querySelector('#messages_placeholder');
        for (var m in messages) {
            if (messages.hasOwnProperty(m)) {
                var message_id = "message_" + m;
                var previous_message = document.querySelector("#" + message_id);

                console.log(previous_message);
                if (previous_message == null) {
                    var div = document.createElement("div");
                    div.setAttribute("class", "alert alert-info fade in");
                    div.setAttribute("id", message_id);
                    var a = document.createElement("a");
                    a.setAttribute("href", "#");
                    a.setAttribute("class", "close");
                    a.setAttribute("data-dismiss", "alert");
                    a.setAttribute("aria-label", "close");
                    a.innerHTML = "&times";

                    var strong = document.createElement("strong");
                    strong.innerHTML = "Info! ";

                    div.append(a);
                    div.append(strong);
                    div.append(messages[m]);

                    pl_messages.append(div);
                }
            }
        }
    }
}

loadResults();

window.setInterval(function(){
    loadResults();
}, 60000)
