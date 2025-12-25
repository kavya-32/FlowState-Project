Deployment to a free VM (Docker Compose)

This guide shows how to deploy the FlowState project to a free VM (e.g. Oracle Cloud Always Free VM, any Ubuntu VM) using Docker and Docker Compose. It runs the Django web app with Gunicorn, serves static files via WhiteNoise, and runs a Celery worker with Redis.

Prereqs on the VM
- A Linux VM (Ubuntu 22.04+ recommended)
- Docker and Docker Compose installed
- At least 1 GB memory (2 GB recommended for Celery + Redis)

Quick steps

1. SSH into your VM and install Docker & Docker Compose
```bash
# Ubuntu example
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Install docker-compose plugin (if needed)
mkdir -p ~/.docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-linux-x86_64" -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
newgrp docker
```

2. Clone the repository
```bash
git clone <your-repo-url> flowstate
cd flowstate/FlowState
```

3. Create `.env` in the project root (FlowState/.env)
```env
# .env example
DJANGO_SECRET_KEY=replace-with-a-secure-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your.vm.ip,localhost
REDIS_URL=redis://redis:6379
DATABASE_URL=postgres://your_postgres_username:your_password@postgres:5432/flowstate_db
# If you prefer SQLite (quick demo), leave DATABASE_URL empty and app will use db.sqlite3
```

4. Start services with Docker Compose
```bash
# build images and start
docker compose up -d --build
# View logs
docker compose logs -f web
```

Notes about databases and Redis
- The provided `docker-compose.yml` starts `redis` and `postgres` containers. If you want to use an external managed Postgres, update `DATABASE_URL` and remove the postgres service.
- For a simple demo, you may keep SQLite (included) — ensure `db.sqlite3` is persisted on a volume or the host.

Admin user and migrations
- The container entrypoint runs `migrate` and `collectstatic` automatically.
- To create a superuser:
```bash
docker compose exec web python manage.py createsuperuser
```

Running Celery Flower or additional workers
- The compose file includes a `worker` service. To run Flower, add a service in `docker-compose.yml` or run a one-off container.

Firewall / Ports
- Open port `8000` or set up an Nginx reverse proxy on port 80 forwarding to 8000.

Domain and TLS
- For production, add an Nginx reverse proxy (or Caddy) to handle TLS. On a free VM you can use Let's Encrypt.

Troubleshooting
- If static files 404: ensure `collectstatic` ran and `STATIC_ROOT` is writable by container.
- If Celery fails to connect: ensure `REDIS_URL` is correct and Redis container is healthy.

Security recommendations
- Set `DJANGO_DEBUG=False` and use a secure `DJANGO_SECRET_KEY`.
- Use managed databases where possible and secure the VM (firewalls, SSH keys).

If you want, I can:
- Prepare an Nginx reverse-proxy config and TLS steps.
- Convert `docker-compose.yml` to a single Docker Swarm or systemd service.
- Provide an automated script to provision an Oracle Cloud Always Free VM and deploy automatically.
