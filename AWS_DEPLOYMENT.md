# 🚀 AWS Deployment - Dental Clinic AI Agent

Complete guide to deploy on AWS free tier (~free for 12 months).

## 📋 Prerequisites

1. **AWS Account**: https://aws.amazon.com/free (free tier eligible)
2. **Vonage Credentials**: Already configured
3. **GitHub Account**: For source code

---

## 💰 Cost Breakdown (Free Tier)

| Service | Free Tier | Notes |
|---------|-----------|-------|
| EC2 (t2.micro) | 750 hours/month | Runs 24/7 free |
| RDS PostgreSQL | 750 hours/month | Managed database |
| ElastiCache Redis | 1GB cache node free | Session storage |
| **Total** | **FREE** | First 12 months |

---

## Step 1: Create RDS PostgreSQL Database

### 1.1 Go to RDS Console
1. Open https://console.aws.amazon.com/rds
2. Click **"Create database"**

### 1.2 Configure Database
- **Engine**: PostgreSQL
- **Version**: PostgreSQL 15.x
- **DB instance class**: db.t3.micro (free tier)
- **Storage**: 20 GB (free tier includes 20 GB)
- **DB instance identifier**: `dental-clinic-db`
- **Master username**: `postgres`
- **Master password**: Save this! (e.g., `YourSecurePassword123`)
- **Connectivity**: Public access = Yes
- **Database name**: `dental_clinic`

### 1.3 Create
Click **"Create database"** → Wait 3-5 minutes

### 1.4 Get Connection Details
Once created, go to **Connectivity & security** tab:
- **Endpoint**: Copy this (e.g., `dental-clinic-db.xxxxx.us-east-1.rds.amazonaws.com`)
- **Port**: 5432

**DATABASE_URL**:
```
postgresql://postgres:YourSecurePassword123@dental-clinic-db.xxxxx.us-east-1.rds.amazonaws.com:5432/dental_clinic
```

---

## Step 2: Create ElastiCache Redis

### 2.1 Go to ElastiCache Console
1. Open https://console.aws.amazon.com/elasticache
2. Click **"Create cache"**

### 2.2 Configure Redis
- **Cache engine**: Redis
- **Engine version**: 7.x
- **Node type**: cache.t3.micro (free tier)
- **Cluster name**: `dental-clinic-redis`
- **Number of nodes**: 1
- **Automatic failover**: Disabled
- **Subnet group**: Create new (or use default)

### 2.3 Create
Click **"Create"** → Wait 2-3 minutes

### 2.4 Get Connection Details
Once created:
- **Primary Endpoint**: Copy this (e.g., `dental-clinic-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379`)

**REDIS_URL**:
```
redis://dental-clinic-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379/0
```

---

## Step 3: Launch EC2 Instance

### 3.1 Go to EC2 Console
1. Open https://console.aws.amazon.com/ec2
2. Click **"Launch instances"**

### 3.2 Configure Instance
- **Name**: `dental-clinic-server`
- **AMI**: Amazon Linux 2 (free tier eligible)
- **Instance type**: t2.micro (free tier)
- **Key pair**: Create new (save `.pem` file!)
  - Name: `dental-clinic-key`
- **Security group**: Create new
  - Inbound rules:
    - SSH (22) from your IP
    - HTTP (80) from anywhere
    - HTTPS (443) from anywhere
  - Outbound: Allow all

### 3.3 Launch
Click **"Launch instance"** → Wait for instance to start

### 3.4 Get Public IP
- Go to **Instances**
- Copy **Public IPv4 address** (e.g., `54.123.45.67`)

---

## Step 4: Connect to EC2 & Deploy Code

### 4.1 SSH into Instance
```bash
chmod 400 dental-clinic-key.pem
ssh -i dental-clinic-key.pem ec2-user@54.123.45.67
```

### 4.2 Install Dependencies
```bash
# Update system
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Clone repository
git clone https://github.com/oladri-renuka/dental_clinical_ai_agent.git
cd dental_clinical_ai_agent

# Install Python requirements
pip3 install -r requirements.txt
```

### 4.3 Create .env File
```bash
nano .env
```

Paste this (update with your values):
```
# Vonage Configuration
VONAGE_API_KEY=08fcadc6
VONAGE_API_SECRET=mhpegqZOKkesJp9d
VONAGE_PHONE_NUMBER=+12709069313

# Database (from RDS)
DATABASE_URL=postgresql://postgres:YourSecurePassword123@dental-clinic-db.xxxxx.us-east-1.rds.amazonaws.com:5432/dental_clinic

# Redis (from ElastiCache)
REDIS_URL=redis://dental-clinic-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379/0

# API Keys
OPENROUTER_API_KEY=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
ELEVENLABS_API_KEY=sk_5b7d067f92b226593b28d410c5dc324a97cfb97029bb4a8d
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

Save (Ctrl+O, Enter, Ctrl+X)

### 4.4 Start Application
```bash
# Install systemd service for auto-start
sudo nano /etc/systemd/system/dental-clinic.service
```

Paste:
```ini
[Unit]
Description=Dental Clinic AI Agent
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/dental_clinical_ai_agent
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dental-clinic
sudo systemctl start dental-clinic

# Check status
sudo systemctl status dental-clinic
```

### 4.5 View Logs
```bash
sudo journalctl -u dental-clinic -f
```

---

## Step 5: Configure Vonage Webhooks

Once your app is running on EC2:

1. Get your **EC2 Public IP**: `54.123.45.67`
2. Go to https://dashboard.nexmo.com/voice/your-numbers
3. Click on **+12709069313**
4. Under **"Webhooks"**:
   - **Answer URL**: `http://54.123.45.67:8000/incoming-call`
   - **Event URL**: `http://54.123.45.67:8000/vonage-speech-input`
   - Both: **POST**
5. **Save**

---

## Step 6: Test

### 6.1 Health Check
```bash
curl http://54.123.45.67:8000/health
```

Should return: `{"status": "ok"}`

### 6.2 View Dashboard
Open: `http://54.123.45.67:8000/dashboard`

### 6.3 Make a Test Call
Call **+12709069313** from your phone

---

## Troubleshooting

### 1. Can't Connect to EC2
```bash
# Check security group allows SSH from your IP
# Go to EC2 → Security Groups → Edit inbound rules
```

### 2. Application Won't Start
```bash
# Check logs
sudo journalctl -u dental-clinic -n 50

# Check port is free
sudo ss -tlnp | grep 8000
```

### 3. Can't Connect to RDS/Redis
```bash
# Check security groups allow EC2 to connect
# RDS: Allow inbound on 5432 from EC2 security group
# Redis: Allow inbound on 6379 from EC2 security group
```

### 4. Vonage Calls Not Working
- Verify webhook URLs are correct: `http://YOUR_IP:8000/incoming-call`
- Check logs: `sudo journalctl -u dental-clinic -f`
- Make sure security group allows HTTP (80) and HTTPS (443)

---

## Monitoring

### View Logs
```bash
sudo journalctl -u dental-clinic -f --lines=100
```

### Restart Service
```bash
sudo systemctl restart dental-clinic
```

### Update Code
```bash
cd ~/dental_clinical_ai_agent
git pull origin main
sudo systemctl restart dental-clinic
```

---

## Cost Optimization

- **Free tier**: 12 months free
- **After 12 months**: ~$5-15/month
- **Ways to save**:
  - Use t3.micro (smallest EC2)
  - Use cache.t3.micro (smallest Redis)
  - Clean up old database entries monthly

---

## Next Steps

1. ✅ Create RDS PostgreSQL
2. ✅ Create ElastiCache Redis
3. ✅ Launch EC2 instance
4. ✅ Deploy code
5. ✅ Configure Vonage webhooks
6. ✅ Test with real calls
7. Monitor and maintain

**Questions?** Let me know! 🚀
