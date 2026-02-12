// Inicializar el mapa
var map = L.map('map').setView([37.8882, -4.7794], 12); // Córdoba como ejemplo

// Capa base de OpenStreetMap (puedes cambiarla luego por SIGPAC)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Mensaje de prueba
console.log("Mapa cargado correctamente");
``
