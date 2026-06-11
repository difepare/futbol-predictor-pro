"""
EXPORTAR DATOS DE POSTGRESQL A SQLITE
Ejecutar en tu computadora local
"""

import sqlite3
import psycopg2
import pandas as pd

# Conexión PostgreSQL (local)
PG_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

# Conectar a PostgreSQL
pg_conn = psycopg2.connect(**PG_CONFIG)

# Conectar a SQLite (archivo)
sqlite_conn = sqlite3.connect('futbol_data.db')

# Exportar equipos
print("📋 Exportando equipos...")
df_equipos = pd.read_sql("SELECT id, nombre, api_team_id, fuerza_actual, liga FROM equipos", pg_conn)
df_equipos.to_sql('equipos', sqlite_conn, if_exists='replace', index=False)
print(f"   ✅ {len(df_equipos)} equipos")

# Exportar partidos
print("📊 Exportando partidos...")
df_partidos = pd.read_sql("""
    SELECT id, api_fixture_id, local_id, visitante_id, fecha, 
           goles_local, goles_visitante, resultado_codigo, temporada, liga
    FROM partidos
""", pg_conn)
df_partidos.to_sql('partidos', sqlite_conn, if_exists='replace', index=False)
print(f"   ✅ {len(df_partidos)} partidos")

# Cerrar conexiones
pg_conn.close()
sqlite_conn.close()

print("\n🎉 DATOS EXPORTADOS CORRECTAMENTE")
print("   Archivo creado: futbol_data.db")