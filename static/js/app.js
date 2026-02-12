let map, drawnItems, currentGeoJSON = null;
let parcelaSeleccionadaId = null;
let graficoLluvia = null;

/* VISTAS */
function mostrarVista(nombre) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${nombre}`).classList.add('active');
}

function actualizarEstadoAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');

    document.getElementById('user-info').textContent = token ? `👤 ${username}` : "";

    document.getElementById('btn-login').style.display = token ? "none" : "inline-block";
    document.getElementById('btn-register').style.display = token ? "none" : "inline-block";
    document.getElementById('btn-logout').style.display = token ? "inline-block" : "none";
    document.getElementById('btn-parcelas').style.display = token ? "inline-block" : "none";
    document.getElementById('btn-perfil').style.display = token ? "inline-block" : "none";

    if (token) {
        mostrarVista('app');
        inicializarMapa();
    } else {
        mostrarVista('home');
    }
}

/* REGISTRO */
async function hacerRegistro() {
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const password2 = document.getElementById('reg-password2').value;

    if (password !== password2) {
        alert("Las contraseñas no coinciden");
        return;
    }

    const resp = await fetch("/api/auth/registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password, confirm_password: password2 })
    });

    const data = await resp.json();
    if (resp.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username);
        actualizarEstadoAuth();
    } else {
        alert(data.error);
    }
}

/* LOGIN */
async function hacerLogin() {
    const emailOrUsername = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emailOrUsername, password })
    });

    const data = await resp.json();
    if (resp.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username);
        actualizarEstadoAuth();
    } else {
        alert(data.error);
    }
}

/* LOGOUT */
function cerrarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    currentGeoJSON = null;
    parcelaSeleccionadaId = null;
    actualizarEstadoAuth();
}

/* MAPA */
function inicializarMapa() {
    if (map) return;

    map = L.map('map').setView([40.0, -3.5], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    L.tileLayer.wms("https://sigpac.mapa.es/fega/servicios/wms", {
        layers: "PARCELA",
        format: "image/png",
        transparent: true
    }).addTo(map);

    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
        edit: { featureGroup: drawnItems },
        draw: { polygon: true, rectangle: false, circle: false, marker: false }
    });

    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, function (event) {
        drawnItems.clearLayers();
        const layer = event.layer;
        drawnItems.addLayer(layer);
        currentGeoJSON = layer.toGeoJSON();
        calcularArea(layer);
    });

    // click SIGPAC real
    map.on("click", async function(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;

        const info = await obtenerInfoSIGPACDesdeClick(lat, lon);
        if (!info) return;

        actualizarPanelSIGPAC(info);
        cargarGraficosLluvia(info);
    });
}

function calcularArea(layer) {
    const area_m2 = turf.area(layer.toGeoJSON());
    document.getElementById("area").innerText = (area_m2 / 10000).toFixed(2);
}

/* SIGPAC INFO (centro de polígono ya existente) */
async function obtenerInfoSIGPAC(geojson) {
    const centro = turf.center(geojson).geometry.coordinates;
    const lon = centro[0], lat = centro[1];
    const bbox = `${lon-0.0005},${lat-0.0005},${lon+0.0005},${lat+0.0005}`;

    const url = `https://sigpac.mapa.es/fega/servicios/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=PARCELA&QUERY_LAYERS=PARCELA&INFO_FORMAT=application/json&FEATURE_COUNT=1&CRS=EPSG:4326&BBOX=${bbox}&WIDTH=101&HEIGHT=101&I=50&J=50`;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.features || data.features.length === 0)
        return { provincia: null, municipio: null };

    const props = data.features[0].properties;
    return {
        provincia: props.PROVINCIA,
        municipio: props.MUNICIPIO
    };
}

/* SIGPAC desde click */
async function obtenerInfoSIGPACDesdeClick(lat, lon) {
    const bbox = `${lon-0.0005},${lat-0.0005},${lon+0.0005},${lat+0.0005}`;

    const url = `https://sigpac.mapa.es/fega/servicios/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=PARCELA&QUERY_LAYERS=PARCELA&INFO_FORMAT=application/json&FEATURE_COUNT=1&CRS=EPSG:4326&BBOX=${bbox}&WIDTH=101&HEIGHT=101&I=50&J=50`;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.features || data.features.length === 0) return null;

    return data.features[0].properties;
}

function actualizarPanelSIGPAC(info) {
    document.getElementById("parcela-nombre").innerText = `Parcela ${info.PARCELA}`;
    document.getElementById("parcela-info").innerHTML = `
        <strong>Provincia:</strong> ${info.PROVINCIA}<br>
        <strong>Municipio:</strong> ${info.MUNICIPIO}<br>
        <strong>Polígono:</strong> ${info.POLIGONO}<br>
        <strong>Parcela:</strong> ${info.PARCELA}<br>
        <strong>Recinto:</strong> ${info.RECINTO}<br>
    `;
}

/* GUARDAR PARCELA DIBUJADA */
async function guardarParcela() {
    if (!currentGeoJSON) {
        alert("Dibuja una parcela primero");
        return;
    }

    const nombre = prompt("Nombre de la parcela:");
    if (!nombre) return;

    const sigpac = await obtenerInfoSIGPAC(currentGeoJSON);

    const resp = await fetch("/api/parcelas", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify({
            nombre,
            provincia: sigpac.provincia,
            municipio: sigpac.municipio,
            cultivo: "Desconocido",
            superficie: document.getElementById("area").innerText,
            geometria: currentGeoJSON
        })
    });

    if (resp.ok) alert("Parcela guardada");
    else alert("Error al guardar");
}

/* LISTAR PARCELAS */
async function cargarParcelas() {
    mostrarVista('parcelas');

    const cont = document.getElementById('parcelas-container');
    cont.innerHTML = "<p>Cargando...</p>";

    const resp = await fetch("/api/parcelas", {
        headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
    });

    const data = await resp.json();
    cont.innerHTML = "";

    data.parcelas.forEach(p => {
        const card = document.createElement("div");
        card.className = "parcela-card";

        card.innerHTML = `
            <img src="/static/img/marker-parcela.png">
            <h3>${p.nombre}</h3>
            <p><strong>Provincia:</strong> ${p.provincia || "—"}</p>
            <p><strong>Municipio:</strong> ${p.municipio || "—"}</p>
            <p><strong>Superficie:</strong> ${p.superficie} ha</p>
            <button onclick="verParcela(${p.id})">Ver detalles</button>
            <button onclick="editarParcela(${p.id})">Editar</button>
            <button onclick="eliminarParcela(${p.id})" style="background:#b30000;color:white;">Eliminar</button>
        `;

        cont.appendChild(card);
    });
}

/* VER DETALLES PARCELA GUARDADA */
async function verParcela(id) {
    parcelaSeleccionadaId = id;
    mostrarVista('app');

    const resp = await fetch(`/api/parcelas/${id}/datos_completos`, {
        headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
    });

    const data = await resp.json();

    document.getElementById('detalle-parcela').innerText =
        `Parcela: ${data.parcela} | Provincia: ${data.data.info_sigpac.provincia}`;

    const lluvia = data.data.graficos.diario[0].v;

    let icono = "/static/img/marker-clima-sol.png";
    if (lluvia > 0) icono = "/static/img/marker-clima-lluvia.png";

    document.getElementById('lluvia-info').innerHTML = `
        <h4>Lluvia hoy</h4>
        <img src="${icono}" style="width:50px;">
        <p>${lluvia} mm</p>
    `;

    const lluviaDiaria = data.data.graficos.diario.map(d => d.v);
    dibujarGrafico(lluviaDiaria);
}

/* GRÁFICO LLUVIA (antiguo, lo mantenemos) */
function dibujarGrafico(lluviaDiaria) {
    const ctx = document.getElementById("grafico-lluvia").getContext("2d");

    if (graficoLluvia) graficoLluvia.destroy();

    graficoLluvia = new Chart(ctx, {
        type: "bar",
        data: {
            labels: lluviaDiaria.map((_, i) => `Día ${i+1}`),
            datasets: [{
                label: "Lluvia (mm)",
                data: lluviaDiaria,
                backgroundColor: "#1e3d59aa",
                borderColor: "#1e3d59",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

/* NUEVOS 4 GRÁFICOS EN SIDEBAR (datos simulados por ahora) */
function cargarGraficosLluvia(info) {
    const lluvia = {
        diario: [0, 2, 5, 1, 0, 3, 4],
        mensual: [20, 35, 10, 5, 0, 50, 30, 15, 5, 0, 40, 60],
        acumulada: [20, 55, 65, 70, 70, 120, 150],
        comparativa: {
            actual: [20, 55, 65, 70, 70, 120, 150],
            anterior: [10, 40, 50, 60, 65, 90, 110]
        }
    };

    dibujarGraficoBar("grafico-diario", lluvia.diario);
    dibujarGraficoBar("grafico-mensual", lluvia.mensual);
    dibujarGraficoLinea("grafico-acumulada", lluvia.acumulada);
    dibujarGraficoComparativa("grafico-comparativa", lluvia.comparativa);
}

function dibujarGraficoBar(id, datos) {
    const ctx = document.getElementById(id).getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: datos.map((_, i) => i+1),
            datasets: [{
                label: "mm",
                data: datos,
                backgroundColor: "#1e3d59aa"
            }]
        },
        options: {
            responsive:true,
            scales:{ y:{ beginAtZero:true } }
        }
    });
}

function dibujarGraficoLinea(id, datos) {
    const ctx = document.getElementById(id).getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: datos.map((_, i) => i+1),
            datasets: [{
                label: "mm acumulados",
                data: datos,
                borderColor: "#1e3d59",
                fill: false
            }]
        },
        options:{ responsive:true }
    });
}

function dibujarGraficoComparativa(id, datos) {
    const ctx = document.getElementById(id).getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: datos.actual.map((_, i) => i+1),
            datasets: [
                {
                    label: "Año actual",
                    data: datos.actual,
                    borderColor: "#1e3d59",
                    fill: false
                },
                {
                    label: "Año anterior",
                    data: datos.anterior,
                    borderColor: "#ff9900",
                    fill: false
                }
            ]
        },
        options:{ responsive:true }
    });
}

/* PERFIL */
async function cargarPerfil() {
    mostrarVista("perfil");
    document.getElementById("perfil-username").innerText = localStorage.getItem("username");
}

document.addEventListener('DOMContentLoaded', actualizarEstadoAuth);
