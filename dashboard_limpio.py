"""
DASHBOARD PREMIER LEAGUE - SOLO STREAMLIT
Ejecutar: streamlit run dashboard_limpio.py
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import joblib
import numpy as np

st.set_page_config(page_title="Premier Predictor", page_icon="⚽", layout="wide")

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

@st.cache_data
def obtener_equipos():
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT nombre, fuerza_actual FROM equipos ORDER BY fuerza_actual DESC", conn)
    conn.close()
    return df

@st.cache_resource
def cargar_modelo():
    try:
        rf = joblib.load('modelo_premier.pkl')
        scaler = joblib.load('scaler_premier.pkl')
        return rf, scaler
    except:
        return None, None

def obtener_fuerza_equipo(nombre):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT fuerza_actual FROM equipos WHERE nombre = %s", (nombre,))
    resultado = cur.fetchone()
    conn.close()
    return float(resultado[0]) if resultado else 0.50

def predecir(local, visitante, modelo, scaler):
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
    return [p/total for p in probas]

# HEADER
st.title("⚽ PREMIER PREDICTOR")
st.markdown("---")

# SIDEBAR
st.sidebar.header("🎯 Selecciona el Partido")
equipos_df = obtener_equipos()
equipos_lista = equipos_df['nombre'].tolist()

local = st.sidebar.selectbox("Equipo Local", equipos_lista)
visitante = st.sidebar.selectbox("Equipo Visitante", equipos_lista)

if st.sidebar.button("🔮 Predecir", use_container_width=True):
    modelo, scaler = cargar_modelo()
    prob_local, prob_empate, prob_visitante = predecir(local, visitante, modelo, scaler)
    
    st.session_state['pred'] = {
        'local': local, 'visitante': visitante,
        'prob_local': prob_local, 'prob_empate': prob_empate, 'prob_visitante': prob_visitante
    }

# RANKING EN SIDEBAR
st.sidebar.markdown("---")
st.sidebar.header("📊 Ranking de Fuerza")
for _, row in equipos_df.head(10).iterrows():
    st.sidebar.text(f"{row['nombre']}: {row['fuerza_actual']:.0%}")
    st.sidebar.progress(row['fuerza_actual'])

# PREDICCION
if 'pred' in st.session_state:
    pred = st.session_state['pred']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(pred['local'], f"{pred['prob_local']:.1%}", delta="Local")
    with col2:
        st.metric("EMPATE", f"{pred['prob_empate']:.1%}", delta="")
    with col3:
        st.metric(pred['visitante'], f"{pred['prob_visitante']:.1%}", delta="Visitante")
    
    fig = go.Figure(data=[
        go.Bar(name=pred['local'], x=[pred['local']], y=[pred['prob_local']], marker_color='#1f77b4'),
        go.Bar(name='Empate', x=['Empate'], y=[pred['prob_empate']], marker_color='#ff7f0e'),
        go.Bar(name=pred['visitante'], x=[pred['visitante']], y=[pred['prob_visitante']], marker_color='#2ca02c')
    ])
    fig.update_layout(yaxis_title="Probabilidad", yaxis_tickformat=".0%", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    if pred['prob_local'] > pred['prob_empate'] and pred['prob_local'] > pred['prob_visitante']:
        st.success(f"🏆 PREDICCIÓN: {pred['local']} GANA")
    elif pred['prob_visitante'] > pred['prob_local'] and pred['prob_visitante'] > pred['prob_empate']:
        st.success(f"🏆 PREDICCIÓN: {pred['visitante']} GANA")
    else:
        st.warning("🤝 PREDICCIÓN: EMPATE")

# TABLA DE EQUIPOS
st.markdown("---")
st.header("📋 Tabla de Fuerza de Equipos")
st.dataframe(equipos_df.style.format({'fuerza_actual': '{:.0%}'}), use_container_width=True)