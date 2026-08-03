"""Deployment guide for Hotel Management app with Supabase PostgreSQL.

This document covers deployment to Render.com, PythonAnywhere, and VPS.
"""

# DEPLOYMENT GUIDE: Hotel Management + Supabase PostgreSQL

## Quick Reference

- **Database:** Supabase PostgreSQL (cloud)
- **Web Server:** Render.com, PythonAnywhere, or self-hosted VPS
- **Driver:** psycopg2-binary
- **WSGI Server:** Gunicorn

---

## Deployment Option 1: Render.com (Recommended)

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit: Flask hotel app with Supabase"
git remote add origin https://github.com/YOUR_USERNAME/hotel-management.git
git push -u origin main
```

### Step 2: Connect to Render

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Fill in:
   - **Name:** hotel-management
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:5000 run:app`

### Step 3: Set Environment Variables

In Render dashboard, go to "Environment":

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=generate-a-secure-key-here
FLASK_ENV=production
```

### Step 4: Deploy

Click "Create Web Service" and Render will deploy automatically.

---

## Deployment Option 2: PythonAnywhere

### Step 1: Create Account
- Sign up at [pythonanywhere.com](https://pythonanywhere.com)

### Step 2: Upload Code
```bash
# From your computer
git clone your-repo.git /path/to/pythonanywhere
cd /path/to/pythonanywhere
```

Or use web console to git clone.

### Step 3: Create Virtual Environment
```bash
# In PythonAnywhere web console
mkvirtualenv --python=/usr/bin/python3.9 hotel
pip install -r requirements.txt
```

### Step 4: Configure Web App

1. Go to Web tab → Add a new web app
2. Choose Manual configuration → Python 3.9
3. Set WSGI file to:

```python
# /path/to/mysite/wsgi.py
import sys
path = '/home/your_username/hotel-management'
if path not in sys.path:
    sys.path.append(path)

from run import app as application
```

### Step 5: Set Environment Variables

In Web app config, add to "Web app security":

```
DATABASE_URL=postgresql://...
SECRET_KEY=...
```

### Step 6: Reload

Click "Reload" and visit your PythonAnywhere URL.

---

## Deployment Option 3: Self-Hosted VPS (DigitalOcean, Linode, AWS EC2)

### Step 1: SSH to Server
```bash
ssh root@your.server.ip
```

### Step 2: Install Dependencies
```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv git nginx supervisor -y
```

### Step 3: Clone Repository
```bash
cd /home
git clone https://github.com/YOUR_USERNAME/hotel-management.git
cd hotel-management
```

### Step 4: Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Step 5: Create .env File
```bash
cat > .env <<EOF
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production
EOF
```

### Step 6: Run Database Setup
```bash
python setup.py
```
Run this once before starting Gunicorn so the tables and admin seed are created.

### Step 7: Configure Supervisor (Process Manager)

```bash
cat > /etc/supervisor/conf.d/hotel.conf <<EOF
[program:hotel]
directory=/home/hotel-management
command=/home/hotel-management/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/hotel.err.log
stdout_logfile=/var/log/hotel.out.log
EOF

supervisorctl reread
supervisorctl update
supervisorctl start hotel
```

### Step 8: Configure Nginx (Web Server)

```bash
cat > /etc/nginx/sites-available/hotel <<EOF
server {
    listen 80;
    server_name your.domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /home/hotel-management/app/static/;
    }

    location /uploads/ {
        alias /home/hotel-management/uploads/;
    }
}
EOF

ln -s /etc/nginx/sites-available/hotel /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 9: Setup SSL (HTTPS)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your.domain.com
```

### Step 10: Check Status
```bash
systemctl status hotel-management
systemctl status nginx
curl http://127.0.0.1:8000
```

---

## Database Backups (Supabase)

Supabase automatically backs up your database daily. To manually backup:

1. Go to Supabase Dashboard
2. Database → Backups
3. Click "Request backup"

To restore:
- Project Settings → Restore from backup

---

## Monitoring & Logs

### Render.com
- Logs visible in dashboard

### PythonAnywhere
- Logs in Web app tab → Log files

### VPS (Supervisor)
```bash
tail -f /var/log/hotel.out.log
tail -f /var/log/hotel.err.log
```

---

## Troubleshooting

### Connection refused
```bash
# Check if app is running
ps aux | grep gunicorn

# Restart
supervisorctl restart hotel
```

### Database connection error
```bash
# Verify DATABASE_URL
cat .env | grep DATABASE_URL

# Test psql connection
psql postgresql://...
```

### Static files not loading
```bash
# Nginx cache
nginx -t && systemctl reload nginx
```

### 502 Bad Gateway
```bash
# Check supervisor status
supervisorctl status hotel

# View logs
tail -f /var/log/hotel.err.log
```

---

## Performance Tips

1. **Connection Pooling:** Already configured in config.py
2. **Static Files:** Use CDN (Cloudflare, AWS CloudFront)
3. **Caching:** Add Redis for session caching
4. **Database:** Use Supabase indexes for faster queries

---

## Security Checklist

- [ ] Set strong SECRET_KEY (not default)
- [ ] Use HTTPS/SSL certificate
- [ ] Set DEBUG=False in production
- [ ] Use strong database password
- [ ] Configure firewall rules
- [ ] Keep dependencies updated
- [ ] Enable CORS only for trusted domains
- [ ] Rate limit login attempts

---

## Support

- **Supabase Issues:** [supabase.com/docs](https://supabase.com/docs)
- **Flask Issues:** [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **Render Issues:** [render.com/docs](https://render.com/docs)

