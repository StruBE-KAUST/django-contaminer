# What is this ?

This repository is a Django application to interface a website with ContaMiner.
You can find ContaMiner [here](https://github.com/StruBE-KAUST/ContaMiner)
This application is used on the [StruBE
website](https://strube.cbrc.kaust.edu.sa/contaminer).

# How to install it ?
You need libffi-dev as a dependancy of paramiko, a website using
[Django](https://www.djangoproject.com/), pip and virtualenv.
Then follow these steps :
-   Clone the repository
-   Create a virtualenv
The virtualenv has to be named `venv`
>   virtualenv --no-site-packages venv
-   Activate the virtual environment
>   source venv/bin/activate
-   Install the requirements
>   pip install -r requirements.txt
-   Configure your database (Many tutorials are available through the
    Internet)
-   Copy config.template as config.ini and edit this file to fit your
    installation
-   Apply migrations to your database (from your website installation)
>   python manage.py migrate
-   Copy the finish.sh script on the ContaMiner installation on your cluster or
    supercomputer
-   Configure a passwordless SSH connection (by keys) in both directions (from
    the webserver to the cluster, and from the cluster to the webserver)
