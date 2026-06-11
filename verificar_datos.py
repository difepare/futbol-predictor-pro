"""
VERIFICAR DATOS DE LA BASE DE DATOS
"""

import psycopg2
import pandas as pd

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def verificar():
    conn = psycopg2.connect(**DB_CONFIG)
    
    print("=" * 60)
    print("VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    # 1. Ver equipos por liga
    print("\n📋 EQUIPOS POR LIGA:")
    df = pd.read_sql("SELECT liga, COUNT(*) as total FROM equipos GROUP BY liga", conn)
    print(df.to_string(index=False))
    
    # 2. Ver partidos por liga
    print("\n📊 PARTIDOS POR LIGA:")
    df = pd.read_sql("SELECT liga, COUNT(*) as total FROM partidos GROUP BY liga", conn)
    print(df.to_string(index=False))
    
    # 3. Ver fuerzas de Premier League
    print("\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 PREMIER LEAGUE - FUERZAS:")
    df = pd.read_sql("""
        SELECT nombre, fuerza_actual 
        FROM equipos 
        WHERE liga = 'Premier League' 
        ORDER BY fuerza_actual DESC
    """, conn)
    
    for i, row in df.iterrows():
        fuerza = row['fuerza_actual']
        estrellas = "⭐" * int(fuerza * 5) if fuerza else ""
        print(f"   {estrellas} {row['nombre']:30} {fuerza:.0%}")
    
    # 4. Ver fuerzas de La Liga
    print("\n🇪🇸 LA LIGA - FUERZAS:")
    df = pd.read_sql("""
        SELECT nombre, fuerza_actual 
        FROM equipos 
        WHERE liga = 'La Liga' 
        ORDER BY fuerza_actual DESC
    """, conn)
    
    for i, row in df.iterrows():
        fuerza = row['fuerza_actual']
        estrellas = "⭐" * int(fuerza * 5) if fuerza else ""
        print(f"   {estrellas} {row['nombre']:30} {fuerza:.0%}")
    
    # 5. Verificar anomalías (fuerzas muy altas en equipos débiles)
    print("\n⚠️ POSIBLES ANOMALÍAS (fuerza > 80% con pocos partidos):")
    df = pd.read_sql("""
        SELECT e.nombre, e.liga, e.fuerza_actual, COUNT(p.id) as partidos
        FROM equipos e
        LEFT JOIN partidos p ON (p.local_id = e.id OR p.visitante_id = e.id)
        WHERE e.fuerza_actual > 0.8
        GROUP BY e.id, e.nombre, e.liga, e.fuerza_actual
        HAVING COUNT(p.id) < 10
        ORDER BY e.fuerza_actual DESC
    """, conn)
    
    if not df.empty:
        for i, row in df.iterrows():
            print(f"   ⚠️ {row['nombre']} ({row['liga']}) - Fuerza: {row['fuerza_actual']:.0%} - Solo {row['partidos']} partidos")
    else:
        print("   ✅ No se encontraron anomalías")
    
    conn.close()

if __name__ == "__main__":
    verificar()