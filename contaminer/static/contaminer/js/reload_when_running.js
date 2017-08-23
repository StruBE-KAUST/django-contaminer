function loadResults() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            refreshIfReady(this.responseText);
        }
    };
    xhttp.open("GET", api_url);
    xhttp.send();
}

function refreshIfReady(response) {
    var response = JSON.parse(response);
    var job_status = response['status'];
    if (job_status.match("Complete|Running")) {
        location.reload();
    }
}

window.setInterval(function(){
    loadResults();
}, 10000)
