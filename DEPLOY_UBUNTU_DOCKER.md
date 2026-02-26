# Deploy Tren Ubuntu Bang Docker

## 1. Cai Docker va Docker Compose Plugin
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

## 2. Lay source code len server
```bash
git clone <REPO_URL> thuyvan_congtrinh_ubuntu
cd thuyvan_congtrinh_ubuntu
```

## 3. Dat bien moi truong
```bash
cat > .env << 'EOF'
SECRET_KEY=thay-secret-key-rat-manh-tai-day
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=thay-mat-khau-rat-manh-tai-day
MONGO_DB_NAME=thuyvan_db
EOF
```

## 4. Build va chay
```bash
docker compose up -d --build
```

## 4.1 Chay voi MongoDB Remote (du lieu cu)
Cap nhat file `.env`:
```bash
MONGO_URI=mongodb://user:password@remote-host:27017/thuyvan_db?authSource=admin
```

Chay web app voi file compose remote:
```bash
docker compose -f docker-compose.remote.yml up -d --build
```

## 5. Kiem tra
```bash
docker compose ps
docker compose logs -f web
```
Truy cap: `http://<IP_SERVER>:5000`

## 6. Lenh van hanh thuong dung
```bash
# Dung
docker compose down

# Cap nhat phien ban moi
git pull
docker compose up -d --build

# Neu dang dung MongoDB remote
docker compose -f docker-compose.remote.yml up -d --build
```

## 7. Mo cong firewall (neu dung UFW)
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```
