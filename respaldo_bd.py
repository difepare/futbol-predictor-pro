"""
RESPALDO AUTOMÁTICO DE BASE DE DATOS
Ejecutar: python respaldo_bd.py
"""

import psycopg2
import pandas as pd
from datetime import datetime
import os

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def respaldar():
    """Exporta todas las tablas a CSV"""
    
    # Crear carpeta de respaldos
    carpeta = f"respaldos_{datetime.now().strftime('%Y%m%d')}"
    os.makedirs(carpeta, exist_ok=True)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Respaldar equipos
    df = pd.read_sql("SELECT * FROM equipos", conn)
    df.to_csv(f"{carpeta}/equipos.csv", index=False)
    print(f"✅ Equipos: {len(df)} registros")
    
    # Respaldar partidos
    df = pd.read_sql("SELECT * FROM partidos", conn)
    df.to_csv(f"{carpeta}/partidos.csv", index=False)
    print(f"✅ Partidos: {len(df)} registros")
    
    # Respaldar predicciones
    try:
        df = pd.read_sql("SELECT * FROM predicciones", conn)
        df.to_csv(f"{carpeta}/predicciones.csv", index=False)
        print(f"✅ Predicciones: {len(df)} registros")
    except:
        print("⚠️ No hay tabla de predicciones aún")
    
    conn.close()
    
    print(f"\n💾 Respaldo guardado en: {carpeta}/")

if __name__ == "__main__":
    print("📀 RESPALDANDO BASE DE DATOS")
    print("="*30)
    respaldar()