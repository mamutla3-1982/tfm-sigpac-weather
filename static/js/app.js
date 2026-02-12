// Inicializar mapa
const map = L.map('map').setView([37.88, -4.77], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
}).addTo(map);

// Capa donde dibujarás la parcela seleccionada
let parcelaLayer = L.geoJSON(null, {
    style: {
        color: '#2f6b3a',
        weight: 2,
        fillColor: '#7ccf8a',
        fillOpacity: 0.3
    }
}).addTo(map);

// -----------------------------
// SELECTORES SIGPAC (vacíos por ahora)
// -----------------------------

async function cargarProvincias() {
    // Aquí pondremos el WFS SIGPAC real
}

async function cargarMunicipios(cpro) {}
async function cargarPoligonos(cpro, cmun) {}
async function cargarParcelas(cpro, cmun, pol) {}
async function cargarRecintos(cpro, cmun, pol, par) {}

// Eventos
document.getElementById('provincia').addEventListener('change', e => {
    cargarMunicipios(e.target.value);
});

// -----------------------------
// BOTÓN CARGAR PARCELA
// -----------------------------
document.getElementById('btn-cargar').addEventListener('click', async () => {
    const cpro = provincia.value;
    const cmun = municipio.value;
    const pol = poligono.value;
    const par = parcela.value;
    const rec = recinto.value;

    const resp = await fetch(`/cargar_parcela?cpro=${cpro}&cmun=${cmun}&pol=${pol}&par=${par}&rec=${rec}`);
    const geojson = await resp.json();

    parcelaLayer.clearLayers();
    parcelaLayer.addData(geojson);
    map.fitBounds(parcelaLayer.getBounds());
});

// -----------------------------
// BOTÓN GUARDAR PARCELA
// -----------------------------
document.getElementById('btn-guardar').addEventListener('click', async () => {
    const resp = await fetch("/guardar_parcela", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            provincia: provincia.value,
            municipio: municipio.value,
            poligono: poligono.value,
            parcela: parcela.value,
            recinto: recinto.value
        })
    });

    const data = await resp.json();
    alert(data.mensaje);
});

// -----------------------------
// GRÁFICOS (vacíos por ahora)
// -----------------------------
new Chart(document.getElementById("graficoMensual"), {
    type: "bar",
    data: { labels: [], datasets: [{ label: "Lluvia (mm)", data: [], backgroundColor: "#2f6b3a" }] }
});

new Chart(document.getElementById("graficoAcumulada"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "Lluvia acumulada", data: [], borderColor: "#2f6b3a" }] }
});
