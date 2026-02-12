$ sudo apt update
$ sudo apt upgrade

- Install ensurepip

$ sudo apt install -y python3.12-venv

- Create a virtual environment

$ python3 -m venv venv

- Activate the virtual environment

$ source venv/bin/activate

- Install PostgreSQL development libraries (command may require prompt input, Y/N)

$ sudo apt install libpq-dev python3-dev build-essential

- Install requirements.txt

$ pip3 install -r requirements.txt

- Create .env file
$ cat > .env << 'EOF'
<FILE CONTENTS>
EOF


$ ...

- Set up database (PostgresSQL)
- Install PostgresSQL
$ sudo apt install postgresql postgresql-contrib -y
- Log in as postgresql
$ sudo -i -u postgres psql
- Create database
postgres=# CREATE DATABASE cardlabs;

- Install a missing CV2 libraries
$ sudo apt install -y libgl1 libglib2.0-0
$ sudo apt install -y libsm6 libxrender1 libxext6

```
POTENTIAL PROBLEMS WHILE TESTING GUNICORN AND SOLUTION
🔧 Fix Options
Option 1: Reset the postgres password (recommended)

Run these commands:

sudo -u postgres psql


You’ll now be inside the PostgreSQL shell (postgres=#).

Then run:

\password postgres


Enter your new password (for example 1988 again if you want to keep using it).
```

- Test gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
$ gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

possible problems: database authentication failure. In my workaround i resolved via: 

$ sudo -u postgres psql
postgres=# ALTER USER postgres PASSWORD '1988';
postgres=# \q


- Set up a Systemd service (so app runs in background)
$ sudo nano /etc/systemd/system/fastapi.service
- nano opens. paste:
```
[Unit]
Description=FastAPI app
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/cardlabsv3.0
ExecStart=/home/ubuntu/cardlabsv3.0/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```
- save and exit


- Start & enable:
$ sudo systemctl daemon-reload
$ sudo systemctl start fastapi
$ sudo systemctl enable fastapi
$ sudo systemctl status fastapi


- Set up Nginx as a reverse proxy
$ sudo apt install nginx -y
- Create config:
$ sudo nano /etc/nginx/sites-available/fastapi

- paste:
```
server {
    server_name cardlabs-sandbox.duckdns.org www.cardlabs-sandbox.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

- Enable site
$ sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled
$ sudo nginx -t
$ sudo systemctl restart nginx

- Secure with HTTPS (Let's Encrypt)
$ sudo apt install certbot python3-certbot-nginx -y

- Generate SSL
$ sudo certbot --nginx -d cardlabs-sandbox.duckdns.org -d cardlabs-sandbox.duckdns.org
- Follow prompts, first enter email then agree to terms with prompy "Y" twice

- Add Auto-renew check
$ sudo systemctl status certbot.timer

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