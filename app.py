# ... (Mantenemos todos tus modelos y configuración anterior) ...

@app.route('/api/parcelas/<int:id>/clima', methods=['GET'])
@login_requerido
def clima_parcela(id):
    p = Parcela.query.filter_by(id=id, user_id=request.current_user_id).first_or_404()
    
    # AUMENTO: Simulación de cruce AEMET/Mateo basado en centroide
    # En un entorno real, aquí llamaríamos a la API de AEMET con app.config['AEMET_API_KEY']
    return jsonify({
        "nombre": p.nombre,
        "municipio": p.municipio,
        "provincia": p.provincia,
        "alertas": "Riesgo de escorrentía" if 25 > 20 else "Normal",
        "graficos": {
            "diario": [{"f": "00h", "v": 0.5}, {"f": "06h", "v": 12.0}, {"f": "12h", "v": 2.1}, {"f": "18h", "v": 0}],
            "mensual": [{"f": "Ene", "v": 45}, {"f": "Feb", "v": 12}, {"f": "Mar", "v": 88}],
            "anual": [{"f": "2023", "v": 520}, {"f": "2024", "v": 490}, {"f": "2025", "v": 510}],
            "historico": [{"f": "Media 10 años", "v": 500}, {"f": "Actual", "v": 510}]
        }
    })

# ... (El resto de tus rutas de registro y login se mantienen intactas) ...
