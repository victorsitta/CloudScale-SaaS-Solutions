#!/bin/bash
echo "🚀 Iniciando deploy do CloudScale RAG Agent na Oracle Cloud (OCI)..."

# Atualizar pacotes e instalar Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Habilitar e iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Liberar porta 8501 no firewall iptables da OCI Ubuntu
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8501 -j ACCEPT
sudo netfilter-persistent save

echo "✅ Ambiente OCI configurado com sucesso!"
echo "Execute: docker-compose up -d --build"
