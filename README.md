# Derek - Open source quiz solution

> Derek is an open source quiz solution.

# How to setup?

## On local system (For dev / testing)

```shellscript
# Clone the repo
git clone https://github.com/PentaQube/derek.git

# Go inside the derek directory
cd derek

# Copy backend and frontend .env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.production

# Run application using docker (Install docker on your system first)
docker compose up --build

# Get backend container name to be used in next command
docker ps

# Create first user
docker exec -it <container_name> python3 cli.py # Create first user

# Access application
Go to http://localhost:5173
```

## On a server (Production)

### Step 1 - Clone the repo

```shellscript
git clone https://github.com/PentaQube/derek.git
```

This will clone the repo and a new folder called 'derek' will be created.

### Step 2 - Configure environment variables

Configure the backend and frontend environment variables.

#### Backend

Go inside the 'derek' folder and make a copy of the backend .env.example file.

```shellscript
cd derek
cp backend/.env.example backend/.env
```

Edit the new .env file as required.

```shellscript
sudo nano backend/.env
```

```shellscript
ENV=dev
DATABASE_DRIVER=postgresql
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=appdb
SECRET_KEY="highly-secret-key-change-me-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_SECONDS=86400
REFRESH_TOKEN_EXPIRE_SECONDS=604800
WEB_APP_BASE_URL=https://derek.example.com # Use your domain

# SMTP Settings (Leave blank or use a service like Mailtrap for dev)
SMTP_SERVER=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_DEFAULT_FROM_EMAIL=noreply@example.com
```

#### Frontend

Make a copy of the frontend .env.example file.

```shellscript
cp frontend/.env.example frontend/.env.production
```

Edit the new .env.production file as required.

```shellscript
sudo nano frontend/.env.production
```

```shellscript
VITE_API_URL=https://derek.example.com/api  # API endpoint (Use your domain)
VITE_WS_URL=wss://derek.example.com/ws      # WebSocket endpoint (Use your domain)
```

### Step 3 - Run application

#### Install docker

```shellscript
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the Docker apt repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Install application

```shellscript
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Verify if the containers are running.

```shellscript
docker ps    # Note the name of the derek-backend container (need in next command)
```

Create first platform admin user.

```shellscript
docker exec -it <derek-backend-container-name> python3 cli.py

Enter name: Jerin Jose
Enter email: jerin@pentaqube.com
Enter password: 
Enter password again: 
Platform admin? [y/n]: y
User created successfully.
```

### Step 4 - Serve application (nginx)

#### Install nginx

```shellscript
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

#### Create dist directory in /var/www

```shellscript
sudo mkdir -p /var/www/derek/dist
sudo chown ubuntu:ubuntu /var/www/derek/dist
```

#### Create server block for Derek

```shellscript
sudo nano /etc/nginx/sites-available/derek


server {
    listen 80;
    server_name derek.example.com;    # Use your domain

    root /var/www/derek/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;  # for SPA routing
    }

    location /api/ {
        proxy_pass http://localhost:8001;
    }

    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;  # keep long-lived connections alive
    }
}
```

Create a symbolic link & test if everything is OK.

```shellscript
sudo ln -s /etc/nginx/sites-available/derek /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

#### Setup HTTPS

```shellscript
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d derek.example.com      # Use your domain
sudo systemctl restart nginx
```

Now you can visit your domain on a browser to access Derek.
