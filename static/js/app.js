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
// SELECTORES SIGPAC
// -----------------------------

async function cargarProvincias() {
    const url = "/proxy?url=" + encodeURIComponent(
        "https://wms.mapa.gob.es/sigpac/ows?service=WFS&request=GetFeature&typeName=sigpac:provincia&outputFormat=application/json"
    );

    const resp = await fetch(url);
    const data = await resp.json();

    provincia.innerHTML = "<option value=''>Seleccione provincia</option>";

    data.features.forEach(f => {
        const cpro = f.properties.CPRO;
        const nombre = f.properties.PROVINCIA;
        provincia.innerHTML += `<option value="${cpro}">${cpro} - ${nombre}</option>`;
    });
}

async function cargarMunicipios(cpro) {
    municipio.innerHTML = "";
    poligono.innerHTML = "";
    parcela.innerHTML = "";
    recinto.innerHTML = "";

    const url = "/proxy?url=" + encodeURIComponent(
        `https://wms.mapa.gob.es/sigpac/ows?service=WFS&request=GetFeature&typeName=sigpac:municipio&cpro=${cpro}&outputFormat=application/json`
    );

    const resp = await fetch(url);
    const data = await resp.json();

    municipio.innerHTML = "<option value=''>Seleccione municipio</option>";

    data.features.forEach(f => {
        const cmun = f.properties.CMUN;
        const nombre = f.properties.MUNICIPIO;
        municipio.innerHTML += `<option value="${cmun}">${cmun} - ${nombre}</option>`;
    });
}

async function cargarPoligonos(cpro, cmun) {
    poligono.innerHTML = "";
    parcela.innerHTML = "";
    recinto.innerHTML = "";

    const url = "/proxy?url=" + encodeURIComponent(
        `https://wms.mapa.gob.es/sigpac/ows?service=WFS&request=GetFeature&typeName=sigpac:poligono&cpro=${cpro}&cmun=${cmun}&outputFormat=application/json`
    );

    const resp = await fetch(url);
    const data = await resp.json();

    poligono.innerHTML = "<option value=''>Seleccione polígono</option>";

    data.features.forEach(f => {
        const pol = f.properties.POLIGONO;
        poligono.innerHTML += `<option value="${pol}">${pol}</option>`;
    });
}

async function cargarParcelas(cpro, cmun, pol) {
    parcela.innerHTML = "";
    recinto.innerHTML = "";

    const url = "/proxy?url=" + encodeURIComponent(
        `https://wms.mapa.gob.es/sigpac/ows?service=WFS&request=GetFeature&typeName=sigpac:parcela&cpro=${cpro}&cmun=${cmun}&poligono=${pol}&outputFormat=application/json`
    );

    const resp = await fetch(url);
    const data = await resp.json();

    parcela.innerHTML = "<option value=''>Seleccione parcela</option>";

    data.features.forEach(f => {
        const par = f.properties.PARCELA;
        parcela.innerHTML += `<option value="${par}">${par}</option>`;
    });
}

async function cargarRecintos(cpro, cmun, pol, par) {
    recinto.innerHTML = "";

    const url = "/proxy?url=" + encodeURIComponent(
        `https://wms.mapa.gob.es/sigpac/ows?service=WFS&request=GetFeature&typeName=sigpac:recinto&cpro=${cpro}&cmun=${cmun}&poligono=${pol}&parcela=${par}&outputFormat=application/json`
    );

    const resp = await fetch(url);
    const data = await resp.json();

    recinto.innerHTML = "<option value=''>Seleccione recinto</option>";

    data.features.forEach(f => {
        const rec = f.properties.RECINTO;
        recinto.innerHTML += `<option value="${rec}">${rec}</option>`;
    });
}

// Eventos
provincia.addEventListener("change", () => cargarMunicipios(provincia.value));
municipio.addEventListener("change", () => cargarPoligonos(provincia.value, municipio.value));
poligono.addEventListener("change", () => cargarParcelas(provincia.value, municipio.value, poligono.value));
parcela.addEventListener("change", () => cargarRecintos(provincia.value, municipio.value, poligono.value, parcela.value));

// -----------------------------
// BOTÓN CARGAR PARCELA
// -----------------------------
document.getElementById('btn-cargar').addEventListener('click', async () => {
    const cpro = provincia.value;
    const cmun = municipio.value;
    const pol = poligono.value;
    const par = parcela.value;
    const rec = recinto.value;

    const url = "/proxy?url=" + encodeURIComponent
