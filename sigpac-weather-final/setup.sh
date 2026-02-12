#!/bin/bash

echo "🌾 SIGPAC Weather - Script de Configuración"
echo "==========================================="
echo ""

# Verificar que estamos en la carpeta correcta
if [ ! -f "app.py" ]; then
    echo "❌ Error: Ejecuta este script desde la carpeta sigpac-weather-final"
    exit 1
fi

echo "✅ Carpeta correcta detectada"
echo ""

# Preguntar por la URI de MongoDB
echo "📋 PASO 1: Configuración de MongoDB"
echo "Ingresa tu MONGODB_URI de MongoDB Atlas:"
read -p "mongodb+srv://...:" MONGODB_URI

# Preguntar por AEMET API key
echo ""
echo "📋 PASO 2: API Key de AEMET"
echo "Ingresa tu AEMET_API_KEY:"
read -p "API Key: " AEMET_KEY

# Generar secrets aleatorios
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Crear archivo .env
cat > .env << EOF
# MongoDB Atlas
MONGODB_URI=${MONGODB_URI}

# Secrets (generados automáticamente)
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# AEMET
AEMET_API_KEY=${AEMET_KEY}

# Puerto
PORT=5000
EOF

echo ""
echo "✅ Archivo .env creado"
echo ""

# Preguntar si quiere inicializar git
echo "📋 PASO 3: Git"
read -p "¿Inicializar repositorio Git? (s/n): " init_git

if [ "$init_git" = "s" ]; then
    git init
    git add .
    git commit -m "SIGPAC Weather - Setup inicial"
    echo "✅ Git inicializado"
    echo ""
    echo "Ahora ejecuta:"
    echo "  git remote add origin https://github.com/TU_USUARIO/sigpac-weather.git"
    echo "  git push -u origin main"
fi

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📝 Variables de entorno para Render:"
echo "MONGODB_URI=${MONGODB_URI}"
echo "SECRET_KEY=${SECRET_KEY}"
echo "JWT_SECRET=${JWT_SECRET}"
echo "AEMET_API_KEY=${AEMET_KEY}"
echo ""
echo "Copia estas variables en Render → Environment"
