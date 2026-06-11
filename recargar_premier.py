"""
RECARGAR PREMIER LEAGUE CON API REAL - VERSION CORREGIDA
"""

import requests
import psycopg2
import time

API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"  # <-- PON TU API KEY AQUÍ
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def limpiar_liga(liga_nombre):
    """Elimina datos existentes de una liga"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM partidos WHERE liga = %s", (liga_nombre,))
    cur.execute("DELETE FROM equipos WHERE liga = %s", (liga_nombre,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Datos antiguos de {liga_nombre} eliminados")

def cargar_premier():
    print("🏴󠁧󠁢󠁥󠁮󠁧󠁿 CARGANDO PREMIER LEAGUE")
    print("=" * 50)
    
    # Limpiar datos existentes
    limpiar_liga('Premier League')
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. OBTENER EQUIPOS
    print("\n📡 Obteniendo equipos de Premier League...")
    url_teams = f"{BASE_URL}/teams"
    params_teams = {"league": 39, "season": 2024}
    
    response = requests.get(url_teams, headers=HEADERS, params=params_teams)
    data = response.json()
    
    if not data.get('response'):
        print("❌ No se encontraron equipos. Verifica tu API Key.")
        return
    
    equipos_guardados = {}
    for team in data['response']:
        nombre = team['team']['name']
        api_id = team['team']['id']
        
        cur.execute("""
            INSERT INTO equipos (nombre, api_team_id, liga, fuerza_actual)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (nombre, api_id, 'Premier League', 0.50))
        
        equipo_id = cur.fetchone()[0]
        equipos_guardados[nombre] = equipo_id
        print(f"   ✅ {nombre}")
    
    conn.commit()
    print(f"\n✅ {len(equipos_guardados)} equipos guardados")
    
    # 2. OBTENER PARTIDOS DE MÚLTIPLES TEMPORADAS
    temporadas = [2020, 2021, 2022, 2023, 2024]
    total_partidos = 0
    
    for temporada in temporadas:
        print(f"\n📊 Cargando temporada {temporada}/{temporada+1}...")
        
        url_fixtures = f"{BASE_URL}/fixtures"
        params_fixtures = {
            "league": 39,
            "season": temporada,
            "status": "FT"
        }
        
        try:
            response = requests.get(url_fixtures, headers=HEADERS, params=params_fixtures, timeout=30)
            data = response.json()
            
            partidos_tmp = 0
            
            for match in data.get('response', []):
                fixture = match['fixture']
                teams = match['teams']
                goals = match['goals']
                
                # Verificar que hay resultados
                if goals['home'] is None or goals['away'] is None:
                    continue
                
                local_nombre = teams['home']['name']
                visitante_nombre = teams['away']['name']
                
                if local_nombre in equipos_guardados and visitante_nombre in equipos_guardados:
                    # Determinar resultado
                    if goals['home'] > goals['away']:
                        resultado = 'local'
                    elif goals['home'] < goals['away']:
                        resultado = 'visitante'
                    else:
                        resultado = 'empate'
                    
                    cur.execute("""
                        INSERT INTO partidos 
                        (api_fixture_id, local_id, visitante_id, fecha, 
                         goles_local, goles_visitante, resultado_codigo, temporada, liga)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (api_fixture_id) DO NOTHING
                    """, (fixture['id'], equipos_guardados[local_nombre], equipos_guardados[visitante_nombre],
                          fixture['date'], goals['home'], goals['away'], resultado, 
                          f"{temporada}/{temporada+1}", 'Premier League'))
                    partidos_tmp += 1
            
            print(f"   ✅ Temporada {temporada}: {partidos_tmp} partidos")
            total_partidos += partidos_tmp
            time.sleep(0.5)  # Evitar rate limit
            
        except Exception as e:
            print(f"   ❌ Error temporada {temporada}: {e}")
    
    conn.commit()
    print(f"\n✅ Total partidos: {total_partidos}")
    
    # 3. CALCULAR FUERZAS
    print("\n📈 Calculando fuerzas de equipos...")
    
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
            WHERE (p.local_id = e.id OR p.visitante_id = e.id) AND p.liga = 'Premier League'
        )
        WHERE e.liga = 'Premier League'
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ PREMIER LEAGUE RECARGADA CORRECTAMENTE")
    print(f"   {len(equipos_guardados)} equipos, {total_partidos} partidos")

def cargar_laliga():
    print("\n" + "=" * 50)
    print("🇪🇸 CARGANDO LA LIGA")
    print("=" * 50)
    
    limpiar_liga('La Liga')
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. OBTENER EQUIPOS
    print("\n📡 Obteniendo equipos de La Liga...")
    url_teams = f"{BASE_URL}/teams"
    params_teams = {"league": 140, "season": 2024}
    
    response = requests.get(url_teams, headers=HEADERS, params=params_teams)
    data = response.json()
    
    if not data.get('response'):
        print("❌ No se encontraron equipos.")
        return
    
    equipos_guardados = {}
    for team in data['response']:
        nombre = team['team']['name']
        api_id = team['team']['id']
        
        cur.execute("""
            INSERT INTO equipos (nombre, api_team_id, liga, fuerza_actual)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (nombre, api_id, 'La Liga', 0.50))
        
        equipo_id = cur.fetchone()[0]
        equipos_guardados[nombre] = equipo_id
        print(f"   ✅ {nombre}")
    
    conn.commit()
    print(f"\n✅ {len(equipos_guardados)} equipos guardados")
    
    # 2. OBTENER PARTIDOS
    temporadas = [2020, 2021, 2022, 2023, 2024]
    total_partidos = 0
    
    for temporada in temporadas:
        print(f"\n📊 Cargando temporada {temporada}/{temporada+1}...")
        
        url_fixtures = f"{BASE_URL}/fixtures"
        params_fixtures = {
            "league": 140,
            "season": temporada,
            "status": "FT"
        }
        
        try:
            response = requests.get(url_fixtures, headers=HEADERS, params=params_fixtures, timeout=30)
            data = response.json()
            
            partidos_tmp = 0
            
            for match in data.get('response', []):
                fixture = match['fixture']
                teams = match['teams']
                goals = match['goals']
                
                if goals['home'] is None or goals['away'] is None:
                    continue
                
                local_nombre = teams['home']['name']
                visitante_nombre = teams['away']['name']
                
                if local_nombre in equipos_guardados and visitante_nombre in equipos_guardados:
                    if goals['home'] > goals['away']:
                        resultado = 'local'
                    elif goals['home'] < goals['away']:
                        resultado = 'visitante'
                    else:
                        resultado = 'empate'
                    
                    cur.execute("""
                        INSERT INTO partidos 
                        (api_fixture_id, local_id, visitante_id, fecha, 
                         goles_local, goles_visitante, resultado_codigo, temporada, liga)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (api_fixture_id) DO NOTHING
                    """, (fixture['id'], equipos_guardados[local_nombre], equipos_guardados[visitante_nombre],
                          fixture['date'], goals['home'], goals['away'], resultado, 
                          f"{temporada}/{temporada+1}", 'La Liga'))
                    partidos_tmp += 1
            
            print(f"   ✅ Temporada {temporada}: {partidos_tmp} partidos")
            total_partidos += partidos_tmp
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error temporada {temporada}: {e}")
    
    conn.commit()
    print(f"\n✅ Total partidos: {total_partidos}")
    
    # 3. CALCULAR FUERZAS
    print("\n📈 Calculando fuerzas de equipos...")
    
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
            WHERE (p.local_id = e.id OR p.visitante_id = e.id) AND p.liga = 'La Liga'
        )
        WHERE e.liga = 'La Liga'
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ LA LIGA RECARGADA CORRECTAMENTE")
    print(f"   {len(equipos_guardados)} equipos, {total_partidos} partidos")

if __name__ == "__main__":
    print("🏆 RECARGANDO LIGAS CON API REAL")
    print("=" * 50)
    
    # Preguntar qué liga cargar
    print("\n¿Qué liga quieres recargar?")
    print("1. Premier League")
    print("2. La Liga")
    print("3. Ambas")
    
    opcion = input("\n👉 Elige (1-3): ")
    
    if opcion == "1":
        cargar_premier()
    elif opcion == "2":
        cargar_laliga()
    elif opcion == "3":
        cargar_premier()
        cargar_laliga()
    else:
        print("Opción no válida")