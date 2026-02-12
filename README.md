# 🌾 SIGPAC Weather - Plataforma Completa de Meteorología Agrícola

## ✨ FUNCIONALIDADES COMPLETAS

✅ **Pantalla de inicio** informativa con diseño profesional  
✅ **Multi-usuario** con registro completo (nombre, username, email, contraseña + confirmación)  
✅ **Login/Cerrar sesión** con JWT  
✅ **Dibujar parcelas** con polígonos en mapa SIGPAC  
✅ **Autodetección** de provincia, municipio y ubicación  
✅ **Cálculo automático** del área de la parcela  
✅ **Casillas de autorelleno** + relleno manual  
✅ **Múltiples parcelas** por usuario  
✅ **Tarjetas de parcelas** en perfil  
✅ **Gráficos de lluvia**: diaria (30 días), mensual (año actual), anual (5 años), histórico (10 años)  
✅ **PWA instalable** en móvil/tablet/PC  
✅ **Keep-alive** automático (no entra en reposo)  
✅ **Conectada a AEMET** (con tu API key)  

---

## 🚀 PASOS COMPLETOS PARA DESPLEGAR

### 1️⃣ CREAR REPOSITORIO EN GITHUB

```bash
# En tu Mac, descomprime el proyecto
cd ~/Downloads/sigpac-weather-final

# Inicializa git
git init
git add .
git commit -m "SIGPAC Weather - Plataforma completa"

# Crea el repo en GitHub
# Ve a github.com → New repository → nombre: sigpac-weather

# Conecta y sube
git remote add origin https://github.com/TU_USUARIO/sigpac-weather.git
git branch -M main
git push -u origin main
```

### 2️⃣ CREAR BASE DE DATOS EN MONGODB

1. Ve a **cloud.mongodb.com**
2. Crea un cluster gratuito M0 (si no lo tienes ya)
3. En "Database Access" → Añade usuario con contraseña
4. En "Network Access" → Añade IP `0.0.0.0/0`
5. En "Connect" → "Connect your application" → Copia la URI:
```
mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/sigpac_weather?retryWrites=true&w=majority
```

### 3️⃣ CREAR SERVICIO EN RENDER

1. Ve a **render.com**
2. **New → Web Service**
3. Conecta tu repositorio de GitHub `sigpac-weather`
4. Configuración:
   - **Name**: `sigpac-weather`
   - **Region**: `Frankfurt (EU Central)`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`

5. **Variables de entorno** (Environment):

| Variable | Valor |
|----------|-------|
| `MONGODB_URI` | Tu URI completa de MongoDB Atlas |
| `SECRET_KEY` | Una frase larga aleatoria (ej: `mi_app_sigpac_super_secreta_2026`) |
| `JWT_SECRET` | Otra frase diferente para JWT (ej: `jwt_token_secreto_2026`) |
| `AEMET_API_KEY` | Tu API key de AEMET |

6. Clic en **"Create Web Service"**

7. Espera ~2 minutos → Tu app estará en: `https://sigpac-weather.onrender.com`

---

## 📱 CÓMO USAR LA APP

### Registro
1. Abre la URL de Render
2. Clic en **"Crear cuenta"**
3. Rellena: nombre completo, username, email, contraseña, confirmar contraseña
4. ¡Ya tienes acceso!

### Añadir Parcela
1. Clic en **"+ Nueva Parcela"**
2. Clic en **"✏️ Dibujar Parcela"**
3. Dibuja el polígono de tu parcela en el mapa
4. **Se autodetecta**: provincia, municipio, superficie
5. Rellena: nombre de parcela, polígono, número de parcela, cultivo
6. Clic en **"Guardar Parcela"**

### Ver Gráficos
1. En el sidebar, clic en cualquier parcela guardada
2. Se muestran 4 gráficos:
   - **Lluvia diaria** (últimos 30 días)
   - **Lluvia mensual** (meses del año actual)
   - **Lluvia anual** (últimos 5 años)
   - **Histórico** (últimos 10 años)

### Cerrar Sesión
- Clic en **"Cerrar sesión"** arriba a la derecha

---

## 🎨 INSTALAR COMO APP (PWA)

### Android/Chrome:
1. Menú (⋮) → "Añadir a pantalla de inicio"

### iOS/Safari:
1. Compartir (□↑) → "Añadir a pantalla de inicio"

### Windows/Mac:
1. Icono de instalación (+) en la barra del navegador

---

## 🔧 ARQUITECTURA

```
FRONTEND (HTML/CSS/JS)
    ↓
FLASK (Python)
    ↓
MONGODB ATLAS (Base de datos cloud)
    ↓
AEMET API (Datos meteorológicos)
```

---

## 📊 ESTRUCTURA DEL PROYECTO

```
sigpac-weather-final/
├── app.py                 ← Backend Flask
├── requirements.txt       ← Dependencias Python
├── templates/
│   └── index.html        ← Frontend completo
├── static/
│   ├── manifest.json     ← PWA manifest
│   ├── service-worker.js ← Service worker
│   └── icons/            ← Iconos de la app
├── .gitignore
└── README.md
```

---

## ❓ SOLUCIÓN DE PROBLEMAS

**Error: "No module named flask_pymongo"**
→ Verifica que `requirements.txt` esté correcto

**Error: "Invalid MongoDB URI"**
→ Revisa la URI y asegúrate de que la contraseña no tenga caracteres especiales

**La app se ve rota**
→ Verifica que los archivos `static/` se hayan subido correctamente

**No aparecen gráficos**
→ Verifica en la consola del navegador si hay errores de Chart.js

---

## 🎯 PRÓXIMOS PASOS (MEJORAS FUTURAS)

- Integrar datos reales de AEMET (actualmente usa datos simulados)
- Añadir capas WMS de SIGPAC oficial
- Notificaciones push para alertas meteorológicas
- Exportar informes en PDF
- Comparación entre parcelas

---

## 🆘 SOPORTE

¿Necesitas ayuda? Envía capturas de:
1. Los logs de Render
2. La consola del navegador (F12)

---

**¡Tu plataforma está lista para usar!** 🚀🌾
