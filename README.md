# LLM Chat

A chat app with a FastAPI backend that talks to Groq and a Streamlit frontend.

```
browser ──> frontend (Streamlit) ──> backend (FastAPI) ──> Groq API
```

## Run locally

```bash
pip install -r backend/requirements.txt -r frontend/requirements.txt
cp .env.example .env   # then put your Groq key in .env

cd backend && uvicorn app.main:app --reload       # http://localhost:8000
streamlit run frontend/app.py                     # http://localhost:8501
```

Or with Docker: `docker compose up --build`, then open http://localhost.

## Deploy to Railway

The app runs as two Railway services from this one repo. Only the frontend
gets a public URL; the backend is reachable only over Railway's private network.

1. On [railway.com](https://railway.com), sign in with GitHub, choose
   **New Project → Deploy from GitHub repo** and pick this repo.
2. Open the service it created and in **Settings**:
   - rename it to `backend`
   - set **Root Directory** to `/backend`
3. In the backend's **Variables** tab add:

   | Variable       | Value                  |
   |----------------|------------------------|
   | `GROQ_API_KEY` | your Groq key          |
   | `MODEL_NAME`   | `openai/gpt-oss-120b`  |
   | `MAX_TOKENS`   | `1000`                 |
   | `PORT`         | `8000`                 |
   | `HOST`         | `::`                   |

4. In the project, click **Create → GitHub Repo**, pick this repo again, and
   in that service's **Settings**:
   - rename it to `frontend`
   - set **Root Directory** to `/frontend`
5. In the frontend's **Variables** tab add:

   | Variable  | Value                                                   |
   |-----------|---------------------------------------------------------|
   | `API_URL` | `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000`       |

6. In the frontend's **Settings → Networking**, click **Generate Domain**.
   That URL is the live app.

Railway builds each service from the Dockerfile in its root directory and
redeploys on every push to the branch it watches (set under **Settings → Source**).

## Deploy to AWS EC2

One small Linux server runs all three containers with `docker compose`.
Caddy is the only container open to the internet; it serves HTTPS and passes
requests to Streamlit, which talks to the backend over Docker's private network.

```
internet ──443──> caddy ──> frontend:8501 ──> backend:8000 ──> Groq
```

### 1. Protect your credits

In the AWS console open **Billing and Cost Management → Budgets → Create budget**,
pick the **Monthly cost budget** template, set it to e.g. `$10` and enter your
email. AWS emails you before you spend more than that.

### 2. Launch the server

In the console pick a region near you (top right, e.g. **Asia Pacific (Mumbai)**),
then **EC2 → Launch instance**:

| Setting              | Value                                                     |
|----------------------|-----------------------------------------------------------|
| Name                 | `llm-chat`                                                |
| AMI                  | **Ubuntu Server 24.04 LTS** (free tier eligible)          |
| Instance type        | `t3.micro` (free tier eligible)                           |
| Key pair             | **Create new key pair** → `llm-chat`, RSA, `.pem`; save the file |
| Network settings     | tick **Allow SSH from My IP**, **Allow HTTPS**, **Allow HTTP** |
| Storage              | `20` GiB gp3                                              |

Click **Launch instance**, open the instance, and copy its **Public IPv4 address**.

Optional but recommended: **EC2 → Elastic IPs → Allocate**, then
**Associate** it with the instance. Without one the IP changes every time the
instance is stopped and started.

### 3. Connect over SSH (from PowerShell on Windows)

SSH refuses a key file other users can read, so lock it down first:

```powershell
icacls $HOME\Downloads\llm-chat.pem /inheritance:r /grant:r "$($env:USERNAME):R"
ssh -i $HOME\Downloads\llm-chat.pem ubuntu@<PUBLIC_IP>
```

### 4. Install Docker on the server

`t3.micro` has 1 GB of RAM, so add 2 GB of swap to keep builds from running out
of memory:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
exit
```

Log back in with the same `ssh` command so the `docker` group takes effect.

### 5. Get the code and configure it

```bash
git clone https://github.com/slick-v/llm_api.git
cd llm_api
nano .env
```

Put this in `.env` (save with Ctrl+O, Enter, Ctrl+X). For `DOMAIN`, take the
public IP and replace the dots with dashes: `13.201.5.7` → `13-201-5-7.sslip.io`.
sslip.io is a free DNS name that points at that IP, which lets Caddy get a real
HTTPS certificate without you buying a domain.

```
GROQ_API_KEY=your_groq_key
MODEL_NAME=openai/gpt-oss-120b
MAX_TOKENS=1000
DOMAIN=13-201-5-7.sslip.io
```

### 6. Start it

```bash
docker compose up -d --build
docker compose ps
```

All three containers should show `running` (the backend also `healthy`).
Open `https://<your-ip-with-dashes>.sslip.io` in a browser.

### Updating and troubleshooting

```bash
cd ~/llm_api && git pull && docker compose up -d --build   # deploy new code
docker compose logs -f backend                              # follow backend logs
docker compose logs caddy                                   # HTTPS certificate problems
docker compose down                                         # stop everything
```

If the IP changes (no Elastic IP), update `DOMAIN` in `.env` and run
`docker compose up -d` again. To stop paying for the server, **Terminate** the
instance and **Release** the Elastic IP.
