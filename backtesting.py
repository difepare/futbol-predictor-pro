"""
BACKTESTING - MIDE LA PRECISIÓN DEL MODELO
Compara predicciones con resultados reales históricos
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def obtener_fuerza_equipo(nombre, liga):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT fuerza_actual FROM equipos WHERE nombre = %s AND liga = %s", (nombre, liga))
    resultado = cur.fetchone()
    conn.close()
    return float(resultado[0]) if resultado else 0.50

def predecir_resultado(local, visitante, liga):
    """Predice resultado basado en fuerzas"""
    fuerza_local = obtener_fuerza_equipo(local, liga)
    fuerza_visitante = obtener_fuerza_equipo(visitante, liga)
    diferencia = fuerza_local - fuerza_visitante
    
    prob_local = 0.35 + (diferencia * 0.25) + 0.08
    prob_empate = 0.32 - (abs(diferencia) * 0.12)
    prob_visitante = 1 - prob_local - prob_empate
    
    total = prob_local + prob_empate + prob_visitante
    prob_local /= total
    prob_empate /= total
    prob_visitante /= total
    
    if prob_local > prob_empate and prob_local > prob_visitante:
        return 'local'
    elif prob_visitante > prob_local and prob_visitante > prob_empate:
        return 'visitante'
    else:
        return 'empate'

def ejecutar_backtesting(liga_nombre, temporada='2024/2025'):
    """Ejecuta backtesting para una liga específica"""
    print(f"\n{'='*50}")
    print(f"📊 BACKTESTING - {liga_nombre} ({temporada})")
    print('='*50)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Obtener partidos reales
    df = pd.read_sql("""
        SELECT 
            e1.nombre as local,
            e2.nombre as visitante,
            p.resultado_codigo as resultado_real,
            p.goles_local,
            p.goles_visitante
        FROM partidos p
        JOIN equipos e1 ON p.local_id = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
        WHERE p.liga = %s AND p.temporada = %s
    """, conn, params=(liga_nombre, temporada))
    
    conn.close()
    
    if df.empty:
        print("   ❌ No hay datos para backtesting")
        return
    
    aciertos = 0
    resultados = []
    
    for _, row in df.iterrows():
        prediccion = predecir_resultado(row['local'], row['visitante'], liga_nombre)
        acerto = prediccion == row['resultado_real']
        
        if acerto:
            aciertos += 1
        
        resultados.append({
            'local': row['local'],
            'visitante': row['visitante'],
            'prediccion': prediccion,
            'realidad': row['resultado_real'],
            'acerto': acerto,
            'goles': f"{row['goles_local']} - {row['goles_visitante']}"
        })
    
    precision = (aciertos / len(df)) * 100
    
    print(f"\n📈 RESULTADOS:")
    print(f"   Partidos analizados: {len(df)}")
    print(f"   Aciertos: {aciertos}")
    print(f"   Precisión: {precision:.1f}%")
    
    # Mostrar algunos ejemplos
    print(f"\n📋 EJEMPLOS:")
    for r in resultados[:10]:
        icono = "✅" if r['acerto'] else "❌"
        print(f"   {icono} {r['local']} vs {r['visitante']} → Pred: {r['prediccion']} | Real: {r['realidad']} ({r['goles']})")
    
    return precision

if __name__ == "__main__":
    print("🏆 SISTEMA DE BACKTESTING")
    print("=" * 50)
    
    ligas = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
    
    resultados_ligas = []
    for liga in ligas:
        precision = ejecutar_backtesting(liga, '2024/2025')
        if precision:
            resultados_ligas.append({'liga': liga, 'precision': precision})
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN GENERAL")
    print("=" * 50)
    
    for r in resultados_ligas:
        estrellas = "⭐" * int(r['precision'] / 10)
        print(f"   {estrellas} {r['liga']}: {r['precision']:.1f}%")
    
    if resultados_ligas:
        promedio = sum(r['precision'] for r in resultados_ligas) / len(resultados_ligas)
        print(f"\n   🎯 PRECISIÓN PROMEDIO: {promedio:.1f}%")