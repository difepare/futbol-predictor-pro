"""
ACTUALIZACIÓN DIARIA DE DATOS PREMIER LEAGUE
Ejecutar: python actualizar_datos.py
Se puede programar para que corra automático cada día
"""

import requests
import psycopg2
from datetime import datetime

API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"  # Tu key real
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def obtener_nuevos_partidos():
    """Obtiene partidos de los últimos 7 días"""
    print(f"📡 Buscando nuevos partidos...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": 39,
        "season": 2025,
        "status": "FT",
        "last": 20
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if not data.get('response'):
            print("   No hay partidos nuevos")
            return 0
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        nuevos = 0
        
        for match in data['response']:
            fixture = match['fixture']
            teams = match['teams']
            goals = match['goals']
            
            # Verificar si ya existe
            cur.execute("SELECT id FROM partidos WHERE api_fixture_id = %s", (fixture['id'],))
            if cur.fetchone():
                continue
            
            # Obtener IDs de equipos
            cur.execute("SELECT id FROM equipos WHERE nombre ILIKE %s", (f"%{teams['home']['name']}%",))
            local_id = cur.fetchone()
            cur.execute("SELECT id FROM equipos WHERE nombre ILIKE %s", (f"%{teams['away']['name']}%",))
            visitante_id = cur.fetchone()
            
            if local_id and visitante_id and goals['home'] is not None:
                resultado = 'local' if goals['home'] > goals['away'] else ('visitante' if goals['away'] > goals['home'] else 'empate')
                
                cur.execute("""
                    INSERT INTO partidos 
                    (api_fixture_id, local_id, visitante_id, fecha, goles_local, goles_visitante, resultado_codigo, temporada)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (fixture['id'], local_id[0], visitante_id[0], fixture['date'],
                      goals['home'], goals['away'], resultado, '2025/2026'))
                nuevos += 1
                
                print(f"   ✅ {teams['home']['name']} {goals['home']} - {goals['away']} {teams['away']['name']}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"\n✅ {nuevos} nuevos partidos guardados")
        return nuevos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

def actualizar_fuerzas():
    """Recalcula fuerzas de equipos basado en todos los partidos"""
    print(f"\n📈 Recalculando fuerzas de equipos...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Elo simplificado: ajustar fuerza según resultados
    cur.execute("""
        UPDATE equipos e
        SET fuerza_actual = (
            SELECT AVG(
                CASE 
                    WHEN p.resultado_codigo = 'local' AND p.local_id = e.id THEN 0.7
                    WHEN p.resultado_codigo = 'visitante' AND p.visitante_id = e.id THEN 0.7
                    WHEN p.resultado_codigo = 'empate' THEN 0.4
                    ELSE 0.3
                END
            ) + 0.3
            FROM partidos p
            WHERE p.local_id = e.id OR p.visitante_id = e.id
        )
        WHERE EXISTS (SELECT 1 FROM partidos WHERE local_id = e.id OR visitante_id = e.id)
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Fuerzas actualizadas")

def guardar_estadisticas():
    """Guarda estadísticas diarias para seguimiento"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Contar partidos
    df = pd.read_sql("SELECT COUNT(*) as total FROM partidos", conn)
    total_partidos = df.iloc[0, 0]
    
    # Contar equipos
    df = pd.read_sql("SELECT COUNT(*) as total FROM equipos", conn)
    total_equipos = df.iloc[0, 0]
    
    conn.close()
    
    # Guardar en archivo de log
    with open('actualizacion_log.txt', 'a') as f:
        f.write(f"{datetime.now()} - Partidos: {total_partidos}, Equipos: {total_equipos}\n")
    
    print(f"\n📊 Estadísticas actuales: {total_partidos} partidos, {total_equipos} equipos")

if __name__ == "__main__":
    print("="*50)
    print("🔄 ACTUALIZACIÓN PREMIER LEAGUE")
    print("="*50)
    
    nuevos = obtener_nuevos_partidos()
    if nuevos > 0:
        actualizar_fuerzas()
    
    guardar_estadisticas()
    print("\n✅ Actualización completada")