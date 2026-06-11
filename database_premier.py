"""
BASE DE DATOS PARA PREMIER LEAGUE
Ejecutar UNA SOLA VEZ para crear tablas específicas de Premier
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuración (usa tu contraseña)
DB_NAME = "premier_predictor"
DB_USER = "postgres"
DB_PASSWORD = "Sarita2017"  # CAMBIA A TU CONTRASEÑA
DB_HOST = "localhost"

def crear_base_datos():
    """Crea la base de datos si no existe"""
    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
    exists = cur.fetchone()
    
    if not exists:
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✅ Base de datos '{DB_NAME}' creada")
    else:
        print(f"✅ Base de datos '{DB_NAME}' ya existe")
    
    cur.close()
    conn.close()

def crear_tablas():
    """Crea todas las tablas para Premier League"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cur = conn.cursor()
    
    # Tabla de equipos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) UNIQUE NOT NULL,
            api_team_id INT UNIQUE,
            fuerza_actual DECIMAL(3,2) DEFAULT 0.50,
            valor_plantilla DECIMAL(10,2),
            promedio_edad DECIMAL(3,1)
        )
    """)
    
    # Tabla de partidos históricos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY,
            api_fixture_id INT UNIQUE,
            temporada VARCHAR(9),
            jornada INT,
            local_id INT REFERENCES equipos(id),
            visitante_id INT REFERENCES equipos(id),
            fecha TIMESTAMP,
            goles_local INT,
            goles_visitante INT,
            posesion_local DECIMAL(5,2),
            posesion_visitante DECIMAL(5,2),
            xg_local DECIMAL(4,2),
            xg_visitante DECIMAL(4,2),
            tiros_local INT,
            tiros_visitante INT,
            resultado_codigo VARCHAR(10)
        )
    """)
    
    # Tabla de predicciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY,
            partido_id INT REFERENCES partidos(id),
            fecha_prediccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prob_local DECIMAL(5,2),
            prob_empate DECIMAL(5,2),
            prob_visitante DECIMAL(5,2),
            confianza DECIMAL(5,2),
            prediccion_resultado VARCHAR(20),
            modelo_version VARCHAR(20)
        )
    """)
    
    # Tabla de lesiones (historico)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lesiones (
            id SERIAL PRIMARY KEY,
            equipo_id INT REFERENCES equipos(id),
            jugador VARCHAR(100),
            tipo_lesion VARCHAR(50),
            fecha_inicio DATE,
            fecha_retorno DATE,
            gravedad INT DEFAULT 1
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tablas creadas exitosamente")

if __name__ == "__main__":
    print("🏆 CREANDO BASE DE DATOS PARA PREMIER LEAGUE")
    print("="*50)
    crear_base_datos()
    crear_tablas()