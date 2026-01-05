# Deploying JobPulse to AWS Free Tier

AWS Free Tier allows you to run a standard Linux Virtual Machine (EC2) for free for 12 months. This is the **best option if you want to keep your Nginx setup** exactly as it is.

## Prerequisites
1.  **AWS Account**: [Create one here](https://aws.amazon.com/free/).
2.  **SSH Client**: Terminal (Mac/Linux) or PuTTY (Windows).

## Deployment Steps

### 1. Launch Instance (EC2)
1.  Go to **EC2 Dashboard** -> **Launch Instance**.
2.  **Name**: `JobPulse-Server`.
3.  **OS Image**: Ubuntu Server 24.04 LTS (Free Tier Eligible).
4.  **Instance Type**: `t2.micro` or `t3.micro` (Free Tier Eligible).
5.  **Key Pair**: Create new key pair, download the `.pem` file (e.g., `jobpulse-key.pem`).
6.  **Network Settings**:
    *   Allow SSH traffic from Anywhere (0.0.0.0/0).
    *   Allow HTTPS traffic from the internet.
    *   Allow HTTP traffic from the internet.
7.  **Storage**: Set to 20-30 GB (Free Tier allows up to 30 GB).
8.  Click **Launch Instance**.

### 2. Connect & Setup
1.  Open your terminal.
2.  Default permissions for key: `chmod 400 jobpulse-key.pem`.
3.  Connect: `ssh -i jobpulse-key.pem ubuntu@<INSTANCE-PUBLIC-IP>`.

### 3. Install Docker
Run these commands inside the server:
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker packages:
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow running docker without sudo:
sudo usermod -aG docker $USER
# Log out and back in for this to take effect:
exit
```
(Reconnect via SSH).

### 4. Configure Swap (Crucial!)
The free instance only has 1GB RAM. You MUST add swap memory or builds will crash.
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 5. Deploy App
1.  **Clone Repo**:
    ```bash
    git clone https://github.com/YourUsername/jobPulse.git
    cd jobPulse
    ```
2.  **Setup Env**:
    *   Create `.env` file: `nano .env`
    *   Paste your environment variables.
    *   **Important**: Set `CSRF_TRUSTED_ORIGINS=http://<YOUR-INSTANCE-IP>:8002`.
3.  **Run**:
    ```bash
    docker compose up -d --build
    ```

### 6. Access
*   Access via `http://<INSTANCE-PUBLIC-IP>:8002/admin/`.
*   Note: You configured Nginx on port 8002 in `docker-compose.yml`. You might need to edit the AWS "Security Group" to allow Custom TCP Rule for port `8002` (standard HTTP rule only opens port 80).
    *   *Alternative*: Edit `docker-compose.yml` on the server to map `80:80` for Nginx.

### 7. Applying Updates (e.g., AI Fallback System)

When you have pushed new changes (like the 3-tier AI system) to GitHub, follow these steps to update your AWS server:

1.  **Connect to Server**:
    ```bash
    ssh -i jobpulse-key.pem ubuntu@<INSTANCE-IP>
    cd jobPulse
    ```

2.  **Pull Latest Code**:
    ```bash
    git pull origin main
    ```

3.  **Update Environment Variables**:
    You need to add the new API keys for the fallback system.
    ```bash
    nano .env
    ```
    Add/Update:
    ```ini
    OPENROUTER_API_KEY=your_key_here
    HF_API_KEY=your_key_here
    ```
    Save (Ctrl+O, Enter) and Exit (Ctrl+X).

4.  **Rebuild and Restart**:
    This will install the new dependencies (openai, tenacity, etc.) and apply migrations.
    ```bash
    docker compose up -d --build
    ```

5.  **Verify**:
    Check logs to ensure the new AI clients are initialized and migrations ran.
    ```bash
    docker compose logs -f web --tail=100
    ```
