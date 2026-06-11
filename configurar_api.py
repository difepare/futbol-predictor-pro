"""
CONFIGURACIÓN DE API PARA DATOS REALES
Ejecuta esto para probar tu API Key y cargar datos reales
"""

import requests
import psycopg2
import time

# ==================== CONFIGURACION ====================
# PON AQUI TU API KEY (obtenida de dashboard.api-football.com)
API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"  # <--- REEMPLAZA CON TU KEY REAL

HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def test_api():
    """Prueba que la API Key funciona"""
    print("="*50)
    print("🔑 PROBANDO API KEY...")
    
    # Probar endpoint de status
    url = f"{BASE_URL}/status"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            print("✅ API Key válida!")
            print(f"   Plan: {response.headers.get('x-apisports-plan', 'Desconocido')}")
            print(f"   Requests restantes: {response.headers.get('x-apisports-requests-remaining', '?')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print("   Verifica que la API Key sea correcta")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def obtener_equipos_premier():
    """Obtiene equipos reales de Premier League"""
    print("\n" + "="*50)
    print("📡 OBTENIENDO EQUIPOS REALES...")
    
    url = f"{BASE_URL}/teams"
    params = {"league": 39, "season": 2024}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('response'):
            equipos = []
            for team in data['response']:
                equipos.append({
                    'nombre': team['team']['name'],
                    'id': team['team']['id'],
                    'pais': team['team']['country']
                })
            print(f"✅ Obtenidos {len(equipos)} equipos de Premier League")
            
            # Mostrar primeros 5
            for e in equipos[:5]:
                print(f"   - {e['nombre']} (ID: {e['id']})")
            
            return equipos
        else:
            print("❌ No se encontraron equipos")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def obtener_partidos_recientes():
    """Obtiene partidos recientes de Premier League"""
    print("\n" + "="*50)
    print("📊 OBTENIENDO PARTIDOS RECIENTES...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": 39,
        "season": 2024,
        "status": "FT",  # Finalizado
        "last": 50       # Últimos 50 partidos
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('response'):
            partidos = []
            for match in data['response']:
                fixture = match['fixture']
                teams = match['teams']
                goals = match['goals']
                
                partidos.append({
                    'id': fixture['id'],
                    'local': teams['home']['name'],
                    'visitante': teams['away']['name'],
                    'goles_local': goals['home'],
                    'goles_visitante': goals['away'],
                    'fecha': fixture['date']
                })
            
            print(f"✅ Obtenidos {len(partidos)} partidos recientes")
            
            # Mostrar últimos 5
            for p in partidos[:5]:
                print(f"   - {p['local']} {p['goles_local']} - {p['goles_visitante']} {p['visitante']}")
            
            return partidos
        else:
            print("❌ No se encontraron partidos")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def guardar_en_bd(equipos, partidos):
    """Guarda los datos reales en la base de datos"""
    print("\n" + "="*50)
    print("💾 GUARDANDO EN BASE DE DATOS...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Guardar equipos
        equipos_guardados = 0
        for equipo in equipos:
            # Calcular fuerza base por ahora (después se mejora)
            fuerza_base = 0.50
            
            cur.execute("""
                INSERT INTO equipos (nombre, api_team_id, fuerza_actual)
                VALUES (%s, %s, %s)
                ON CONFLICT (nombre) DO UPDATE SET
                    api_team_id = EXCLUDED.api_team_id
            """, (equipo['nombre'], equipo['id'], fuerza_base))
            equipos_guardados += 1
        
        print(f"✅ Guardados {equipos_guardados} equipos")
        
        # Guardar partidos
        partidos_guardados = 0
        for partido in partidos:
            # Obtener IDs de equipos
            cur.execute("SELECT id FROM equipos WHERE nombre = %s", (partido['local'],))
            local_id = cur.fetchone()
            cur.execute("SELECT id FROM equipos WHERE nombre = %s", (partido['visitante'],))
            visitante_id = cur.fetchone()
            
            if local_id and visitante_id and partido['goles_local'] is not None:
                resultado = 'local' if partido['goles_local'] > partido['goles_visitante'] else ('visitante' if partido['goles_visitante'] > partido['goles_local'] else 'empate')
                
                cur.execute("""
                    INSERT INTO partidos (api_fixture_id, local_id, visitante_id, fecha, 
                                         goles_local, goles_visitante, resultado_codigo, temporada)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (api_fixture_id) DO NOTHING
                """, (partido['id'], local_id[0], visitante_id[0], partido['fecha'],
                      partido['goles_local'], partido['goles_visitante'], resultado, '2024/2025'))
                partidos_guardados += 1
        
        print(f"✅ Guardados {partidos_guardados} partidos")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n🎉 ¡DATOS REALES CARGADOS CORRECTAMENTE!")
        print("   Ahora puedes reentrenar el modelo con datos reales")
        
    except Exception as e:
        print(f"❌ Error guardando: {e}")

def actualizar_fuerzas_historicas():
    """Actualiza fuerzas de equipos basado en resultados históricos"""
    print("\n" + "="*50)
    print("📈 ACTUALIZANDO FUERZAS DE EQUIPOS...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Calcular fuerza basada en goles y resultados
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
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Fuerzas actualizadas basadas en resultados reales")

# ==================== PROGRAMA PRINCIPAL ====================
def main():
    print("🏆 CONFIGURACIÓN API PREMIER LEAGUE")
    print("="*50)
    
    # Verificar API Key
    if API_KEY == "TU_API_KEY_AQUI":
        print("\n❌ PRIMERO: Obtén tu API Key")
        print("   1. Ve a https://dashboard.api-football.com/register")
        print("   2. Regístrate (es gratis)")
        print("   3. Copia tu API Key")
        print("   4. Pégala en la variable API_KEY de este script")
        return
    
    # Probar API
    if not test_api():
        return
    
    # Obtener datos
    equipos = obtener_equipos_premier()
    if not equipos:
        return
    
    partidos = obtener_partidos_recientes()
    
    # Guardar en BD
    guardar_en_bd(equipos, partidos)
    
    # Actualizar fuerzas
    actualizar_fuerzas_historicas()
    
    print("\n" + "="*50)
    print("🎉 TODO LISTO!")
    print("="*50)
    print("\nAhora puedes:")
    print("   1. Reentrenar el modelo: python premier_predictor.py (opción 3)")
    print("   2. Ver dashboard con datos reales: streamlit run dashboard_limpio.py")

if __name__ == "__main__":
    main()