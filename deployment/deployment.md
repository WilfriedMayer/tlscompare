Deployment
==========

Overview:
```
HTTP Client <--> HTTP Server (nginx) <--> Socket (/opt/tlscompare/tlscompare.sock) <--> UWSGI Server <--> tlscompare.py   
```

Prereq
------
* Install uwsgi / uwsgi-plugin-python
* Install virtualenv / python-pip

Install application
-------------------

1) git clone to /opt/tlscompare
2) Install virtualenv

```
cd /opt/tlscompare
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

Configure uwsgi
---------------

* uwsgi is the application server
* Copy tlscompare.ini to /etc/uwsgi/apps-enabled and create symlink

Configure nginx
----------------

* Copy tlscompare.nginx to /etc/nginx/apps-available and create symlink
