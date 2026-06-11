"""
PREDICTOR PREMIER LEAGUE - VERSION CONSOLA
Ejecutar: python predictor_cli.py
"""

import psycopg2
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from prettytable import PrettyTable
import warnings
warnings.filterwarnings('ignore')

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def conectar():
    return psycopg2.connect(**DB_CONFIG)

def obtener_equipos():
    conn = conectar()
    df = pd.read_sql("SELECT id, nombre, fuerza_actual FROM equipos ORDER BY nombre", conn)
    conn.close()
    return df

def obtener_fuerza_equipo(nombre):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT fuerza_actual FROM equipos WHERE nombre = %s", (nombre,))
    resultado = cur.fetchone()
    conn.close()
    return float(resultado[0]) if resultado else 0.50

def entrenar_modelo():
    print("\n🤖 ENTRENANDO MODELO...")
    
    conn = conectar()
    df = pd.read_sql("""
        SELECT 
            p.goles_local, p.goles_visitante,
            e1.fuerza_actual as fuerza_local,
            e2.fuerza_actual as fuerza_visitante
        FROM partidos p
        JOIN equipos e1 ON p.local_id = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
        WHERE p.goles_local IS NOT NULL
    """, conn)
    conn.close()
    
    if len(df) < 10:
        print("⚠️ Datos insuficientes para entrenar")
        return None, None
    
    df['diferencia'] = df['fuerza_local'] - df['fuerza_visitante']
    
    def get_target(row):
        if row['goles_local'] > row['goles_visitante']:
            return 0
        elif row['goles_local'] == row['goles_visitante']:
            return 1
        return 2
    
    df['target'] = df.apply(get_target, axis=1)
    
    features = ['fuerza_local', 'fuerza_visitante', 'diferencia']
    X = df[features].fillna(0.5)
    y = df['target']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    
    precision = rf.score(X_test, y_test)
    print(f"✅ Modelo entrenado - Precisión: {precision:.2%}")
    
    joblib.dump(rf, 'modelo_premier.pkl')
    joblib.dump(scaler, 'scaler_premier.pkl')
    
    return rf, scaler

def cargar_modelo():
    try:
        rf = joblib.load('modelo_premier.pkl')
        scaler = joblib.load('scaler_premier.pkl')
        return rf, scaler
    except:
        return None, None

def predecir_partido(local, visitante, modelo, scaler):
    fuerza_local = obtener_fuerza_equipo(local)
    fuerza_visitante = obtener_fuerza_equipo(visitante)
    diferencia = fuerza_local - fuerza_visitante
    
    if modelo and scaler:
        X = np.array([[fuerza_local, fuerza_visitante, diferencia]])
        X_scaled = scaler.transform(X)
        probas = modelo.predict_proba(X_scaled)[0]
    else:
        prob_local = 0.35 + (diferencia * 0.25) + 0.08
        prob_empate = 0.32 - (abs(diferencia) * 0.12)
        prob_visitante = 1 - prob_local - prob_empate
        probas = [prob_local, prob_empate, prob_visitante]
    
    total = sum(probas)
    prob_local, prob_empate, prob_visitante = [p/total for p in probas]
    
    confianza = (max(probas) - sorted(probas)[-2]) * 100
    
    if prob_local > prob_empate and prob_local > prob_visitante:
        prediccion = f"🏆 GANA {local}"
    elif prob_visitante > prob_local and prob_visitante > prob_empate:
        prediccion = f"🏆 GANA {visitante}"
    else:
        prediccion = "🤝 EMPATE"
    
    return {
        'local': local, 'visitante': visitante,
        'prob_local': prob_local, 'prob_empate': prob_empate, 'prob_visitante': prob_visitante,
        'confianza': confianza, 'prediccion': prediccion,
        'fuerza_local': fuerza_local, 'fuerza_visitante': fuerza_visitante
    }

def mostrar_prediccion(pred):
    print("\n" + "="*80)
    print(f"🎯 PREDICCIÓN: {pred['local']} vs {pred['visitante']}")
    print("="*80)
    
    tabla = PrettyTable()
    tabla.field_names = ["Resultado", "Probabilidad", "Fuerza", "Barra"]
    
    barra_local = "█" * int(pred['prob_local'] * 20) + "░" * (20 - int(pred['prob_local'] * 20))
    barra_empate = "█" * int(pred['prob_empate'] * 20) + "░" * (20 - int(pred['prob_empate'] * 20))
    barra_visitante = "█" * int(pred['prob_visitante'] * 20) + "░" * (20 - int(pred['prob_visitante'] * 20))
    
    tabla.add_row([f"🏠 {pred['local']}", f"{pred['prob_local']:.1%}", f"{pred['fuerza_local']:.0%}", barra_local])
    tabla.add_row(["🤝 EMPATE", f"{pred['prob_empate']:.1%}", "-", barra_empate])
    tabla.add_row([f"✈️ {pred['visitante']}", f"{pred['prob_visitante']:.1%}", f"{pred['fuerza_visitante']:.0%}", barra_visitante])
    
    print(tabla)
    print("-"*80)
    print(f"📊 {pred['prediccion']}")
    
    confianza_nivel = int(pred['confianza'] / 10)
    barra_confianza = "█" * confianza_nivel + "░" * (10 - confianza_nivel)
    print(f"🔒 CONFIANZA: [{barra_confianza}] {pred['confianza']:.1f}%")
    print("="*80)

def menu():
    print("\n" + "="*80)
    print("🏆 PREDICTOR PREMIER LEAGUE")
    print("="*80)
    
    modelo, scaler = cargar_modelo()
    
    while True:
        print("\n" + "="*50)
        print("MENÚ")
        print("="*50)
        print("1. 🎯 Predecir partido")
        print("2. 🤖 Entrenar modelo")
        print("3. 📋 Ver equipos")
        print("4. ❌ Salir")
        
        opcion = input("\n👉 Elige (1-4): ")
        
        if opcion == "1":
            equipos = obtener_equipos()
            print("\nEquipos disponibles:")
            for i, row in equipos.iterrows():
                print(f"   {i+1}. {row['nombre']}")
            
            local = input("\nEquipo local: ").strip()
            visitante = input("Equipo visitante: ").strip()
            
            pred = predecir_partido(local, visitante, modelo, scaler)
            mostrar_prediccion(pred)
        
        elif opcion == "2":
            modelo, scaler = entrenar_modelo()
        
        elif opcion == "3":
            equipos = obtener_equipos()
            print("\n📋 EQUIPOS PREMIER LEAGUE:")
            for i, row in equipos.iterrows():
                fuerza = row['fuerza_actual']
                estrellas = "⭐" * int(fuerza * 5) + "☆" * (5 - int(fuerza * 5))
                print(f"   {estrellas} {row['nombre']:30} {fuerza:.0%}")
        
        elif opcion == "4":
            print("\n👋 ¡Hasta luego!")
            break

if __name__ == "__main__":
    menu()