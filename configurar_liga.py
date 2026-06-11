"""
CONFIGURACIÓN DE NUEVA LIGA - LA LIGA
Ejecutar: python configurar_liga.py
"""

import requests
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ==================== CONFIGURACION ====================
API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"  # Tu API key de API-Football
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

# IDs de las ligas en API-Football
LIGAS = {
    'premier': 39,
    'laliga': 140,
    'seriea': 135,
    'bundesliga': 78,
    'ligue1': 61,
    'champions': 2,
    'europa': 3,
    'conference': 848
}

# ==================== FUNCIONES ====================
def crear_tabla_ligas():
    """Agrega tabla de ligas a la base de datos"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Agregar columna liga a equipos si no existe
    cur.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='equipos' AND column_name='liga') THEN
                ALTER TABLE equipos ADD COLUMN liga VARCHAR(50);
            END IF;
        END $$;
    """)
    
    # Agregar columna liga a partidos
    cur.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='partidos' AND column_name='liga') THEN
                ALTER TABLE partidos ADD COLUMN liga VARCHAR(50);
            END IF;
        END $$;
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Estructura de base de datos actualizada para múltiples ligas")

def obtener_equipos_liga(liga_nombre, liga_id, temporada=2025):
    """Obtiene equipos de una liga específica"""
    print(f"\n📡 Obteniendo equipos de {liga_nombre}...")
    
    url = f"{BASE_URL}/teams"
    params = {"league": liga_id, "season": temporada}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if not data.get('response'):
            print(f"   ❌ No se encontraron equipos para {liga_nombre}")
            return 0
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        equipos_guardados = 0
        
        for team in data['response']:
            nombre = team['team']['name']
            api_id = team['team']['id']
            
            # Calcular fuerza base (por ahora 0.50, después se ajusta)
            fuerza_base = 0.50
            
            cur.execute("""
                INSERT INTO equipos (nombre, api_team_id, fuerza_actual, liga)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nombre) DO UPDATE SET
                    api_team_id = EXCLUDED.api_team_id,
                    liga = EXCLUDED.liga
            """, (nombre, api_id, fuerza_base, liga_nombre))
            equipos_guardados += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"   ✅ Guardados {equipos_guardados} equipos de {liga_nombre}")
        return equipos_guardados
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0

def obtener_partidos_liga(liga_nombre, liga_id, temporadas=[2024, 2025]):
    """Obtiene partidos históricos de una liga"""
    print(f"\n📊 Obteniendo partidos de {liga_nombre}...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    total_partidos = 0
    
    for temporada in temporadas:
        url = f"{BASE_URL}/fixtures"
        params = {
            "league": liga_id,
            "season": temporada,
            "status": "FT"
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            data = response.json()
            
            for match in data.get('response', []):
                fixture = match['fixture']
                teams = match['teams']
                goals = match['goals']
                
                # Obtener IDs de equipos
                cur.execute("SELECT id FROM equipos WHERE nombre ILIKE %s AND liga = %s", 
                           (f"%{teams['home']['name']}%", liga_nombre))
                local_id = cur.fetchone()
                cur.execute("SELECT id FROM equipos WHERE nombre ILIKE %s AND liga = %s", 
                           (f"%{teams['away']['name']}%", liga_nombre))
                visitante_id = cur.fetchone()
                
                if local_id and visitante_id and goals['home'] is not None:
                    resultado = 'local' if goals['home'] > goals['away'] else ('visitante' if goals['away'] > goals['home'] else 'empate')
                    
                    cur.execute("""
                        INSERT INTO partidos 
                        (api_fixture_id, local_id, visitante_id, fecha, 
                         goles_local, goles_visitante, resultado_codigo, temporada, liga)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (api_fixture_id) DO NOTHING
                    """, (fixture['id'], local_id[0], visitante_id[0], fixture['date'],
                          goals['home'], goals['away'], resultado, f"{temporada}/{temporada+1}", liga_nombre))
                    total_partidos += 1
            
            print(f"   Temporada {temporada}: {len(data.get('response', []))} partidos")
            
        except Exception as e:
            print(f"   Error temporada {temporada}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"   ✅ Total {liga_nombre}: {total_partidos} partidos")
    return total_partidos

def actualizar_fuerzas_por_liga(liga_nombre):
    """Actualiza fuerzas de equipos específicos de una liga"""
    print(f"\n📈 Actualizando fuerzas de {liga_nombre}...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
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
            WHERE (p.local_id = e.id OR p.visitante_id = e.id) AND p.liga = %s
        )
        WHERE e.liga = %s AND EXISTS (SELECT 1 FROM partidos WHERE liga = %s)
    """, (liga_nombre, liga_nombre, liga_nombre))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"   ✅ Fuerzas actualizadas para {liga_nombre}")

def mostrar_resumen():
    """Muestra el estado actual de todas las ligas"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n" + "="*50)
    print("📊 RESUMEN DE LIGAS")
    print("="*50)
    
    for liga in LIGAS.keys():
        cur.execute("SELECT COUNT(*) FROM equipos WHERE liga = %s", (liga,))
        equipos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM partidos WHERE liga = %s", (liga,))
        partidos = cur.fetchone()[0]
        
        if equipos > 0:
            print(f"   {liga.upper()}: {equipos} equipos, {partidos} partidos")
    
    cur.close()
    conn.close()

# ==================== MENÚ PRINCIPAL ====================
def menu():
    print("\n" + "="*60)
    print("🏆 CONFIGURACIÓN DE LIGAS")
    print("="*60)
    
    # Crear estructura para múltiples ligas
    crear_tabla_ligas()
    
    while True:
        print("\n" + "="*50)
        print("LIGAS DISPONIBLES")
        print("="*50)
        print("1. 🇪🇸 La Liga")
        print("2. 🇮🇹 Serie A")
        print("3. 🇩🇪 Bundesliga")
        print("4. 🇫🇷 Ligue 1")
        print("5. 🇪🇺 Champions League")
        print("6. 📊 Ver resumen")
        print("7. ❌ Salir")
        
        opcion = input("\n👉 Elige (1-7): ")
        
        if opcion == "1":
            print("\n🇪🇸 CONFIGURANDO LA LIGA")
            print("-"*30)
            obtener_equipos_liga('laliga', LIGAS['laliga'])
            obtener_partidos_liga('laliga', LIGAS['laliga'])
            actualizar_fuerzas_por_liga('laliga')
            print("\n✅ La Liga configurada exitosamente!")
        
        elif opcion == "2":
            print("\n🇮🇹 CONFIGURANDO SERIE A")
            print("-"*30)
            obtener_equipos_liga('seriea', LIGAS['seriea'])
            obtener_partidos_liga('seriea', LIGAS['seriea'])
            actualizar_fuerzas_por_liga('seriea')
            print("\n✅ Serie A configurada exitosamente!")
        
        elif opcion == "3":
            print("\n🇩🇪 CONFIGURANDO BUNDESLIGA")
            print("-"*30)
            obtener_equipos_liga('bundesliga', LIGAS['bundesliga'])
            obtener_partidos_liga('bundesliga', LIGAS['bundesliga'])
            actualizar_fuerzas_por_liga('bundesliga')
            print("\n✅ Bundesliga configurada exitosamente!")
        
        elif opcion == "4":
            print("\n🇫🇷 CONFIGURANDO LIGUE 1")
            print("-"*30)
            obtener_equipos_liga('ligue1', LIGAS['ligue1'])
            obtener_partidos_liga('ligue1', LIGAS['ligue1'])
            actualizar_fuerzas_por_liga('ligue1')
            print("\n✅ Ligue 1 configurada exitosamente!")
        
        elif opcion == "5":
            print("\n🇪🇺 CONFIGURANDO CHAMPIONS LEAGUE")
            print("-"*30)
            obtener_equipos_liga('champions', LIGAS['champions'])
            obtener_partidos_liga('champions', LIGAS['champions'])
            actualizar_fuerzas_por_liga('champions')
            print("\n✅ Champions League configurada exitosamente!")
        
        elif opcion == "6":
            mostrar_resumen()
        
        elif opcion == "7":
            break

if __name__ == "__main__":
    menu()