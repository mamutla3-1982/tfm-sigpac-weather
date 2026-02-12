# ... (Se mantiene todo tu código previo de Flask, SQLAlchemy y Auth)

@app.route('/api/parcelas/<int:id>/datos_completos', methods=['GET'])
@login_requerido
def datos_completos_parcela(id):
    # Buscamos la parcela del usuario
    p = Parcela.query.filter_by(id=id, user_id=request.current_user_id).first_or_404()
    
    # AUMENTO: Simulación de datos cruzados SIGPAC + AEMET + MATEO
    # Estos datos alimentarán automáticamente los 4 gráficos solicitados
    datos_meteo = {
        "info_sigpac": {
            "provincia": p.provincia,
            "municipio": p.municipio,
            "cultivo": p.cultivo,
            "superficie": p.superficie
        },
        "graficos": {
            "diario": [{"f": "08:00", "v": 1.5}, {"f": "14:00", "v": 0.8}, {"f": "20:00", "v": 2.2}],
            "mensual": [{"f": "Sem 1", "v": 15}, {"f": "Sem 2", "v": 45}, {"f": "Sem 3", "v": 10}],
            "anual": [{"f": "2024", "v": 520}, {"f": "2025", "v": 485}],
            "historico": [{"f": "Media 10 años", "v": 500}, {"f": "Actual", "v": 510}]
        },
        "alerta": "Riesgo de helada" if -2 < 0 else "Normal"
    }
    
    return jsonify({"parcela": p.nombre, "data": datos_meteo})

# ... (Tus rutas de /api/auth/login y registro se quedan exactamente igual)
