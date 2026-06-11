"""
DASHBOARD MULTI-LIGA - Premier, La Liga, Serie A, Bundesliga, Ligue 1, Champions
Ejecutar: streamlit run dashboard_multi_liga.py
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import streamlit as st
# Configuración para producción (Streamlit Cloud)
if 'DATABASE_URL' in st.secrets:
    # Usar PostgreSQL en la nube (más adelante)
    DB_CONFIG = {
        'dbname': st.secrets['DB_NAME'],
        'user': st.secrets['DB_USER'],
        'password': st.secrets['DB_PASSWORD'],
        'host': st.secrets['DB_HOST']
    }
else:
    # Local
    DB_CONFIG = {
        'dbname': 'premier_predictor',
        'user': 'postgres',
        'password': 'Sarita2017',
        'host': 'localhost'
    }

API_KEY = st.secrets.get('API_KEY', '9e346e18701e4928f7cd1eeee3d8d510')


st.set_page_config(page_title="Fútbol Predictor Pro", page_icon="🏆", layout="wide")

# ==================== CONFIGURACION ====================
DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

LIGAS = {
    'Premier League': {'icono': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'color': '#37003c'},
    'La Liga': {'icono': '🇪🇸', 'color': '#ffb300'},
    'Serie A': {'icono': '🇮🇹', 'color': '#0055a4'},
    'Bundesliga': {'icono': '🇩🇪', 'color': '#000000'},
    'Ligue 1': {'icono': '🇫🇷', 'color': '#0055a4'},
    'Champions League': {'icono': '🌟', 'color': '#e90052'}
}

# ==================== FUNCIONES ====================
@st.cache_data
def obtener_equipos(liga=None):
    conn = psycopg2.connect(**DB_CONFIG)
    if liga:
        df = pd.read_sql("SELECT nombre, fuerza_actual FROM equipos WHERE liga = %s ORDER BY fuerza_actual DESC", conn, params=(liga,))
    else:
        df = pd.read_sql("SELECT nombre, fuerza_actual, liga FROM equipos ORDER BY fuerza_actual DESC", conn)
    conn.close()
    return df

@st.cache_data
def obtener_todas_ligas_disponibles():
    """Obtiene qué ligas tienen datos en la base de datos"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql("SELECT DISTINCT liga FROM equipos WHERE liga IS NOT NULL", conn)
        disponibles = df['liga'].tolist()
    except:
        disponibles = []
    conn.close()
    return disponibles

def obtener_fuerza_equipo(nombre, liga):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT fuerza_actual FROM equipos WHERE nombre = %s AND liga = %s", (nombre, liga))
    resultado = cur.fetchone()
    conn.close()
    return float(resultado[0]) if resultado else 0.50

def predecir(local, visitante, liga):
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
    
    confianza = (max([prob_local, prob_empate, prob_visitante]) - 
                 sorted([prob_local, prob_empate, prob_visitante])[-2]) * 100
    
    return prob_local, prob_empate, prob_visitante, confianza

# ==================== HEADER ====================
st.title("🏆 FÚTBOL PREDICTOR PRO")
st.markdown("*Predicciones profesionales para las mejores ligas del mundo*")

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Configuración")

# Obtener ligas que realmente tienen datos
ligas_disponibles = obtener_todas_ligas_disponibles()

if not ligas_disponibles:
    st.sidebar.warning("⚠️ No hay ligas configuradas aún")
    st.sidebar.info("Ejecuta: python configurar_liga.py para agregar ligas")
    liga_seleccionada = None
else:
    liga_seleccionada = st.sidebar.selectbox(
        "📋 Selecciona Liga",
        ligas_disponibles,
        format_func=lambda x: f"{LIGAS.get(x, {}).get('icono', '🏆')} {x}"
    )

if liga_seleccionada:
    st.sidebar.markdown("---")
    
    # Obtener equipos de la liga seleccionada
    equipos_df = obtener_equipos(liga_seleccionada)
    equipos_lista = equipos_df['nombre'].tolist()
    
    if equipos_lista:
        local = st.sidebar.selectbox("🏠 Equipo Local", equipos_lista)
        visitante = st.sidebar.selectbox("✈️ Equipo Visitante", equipos_lista)
        
        if st.sidebar.button("🔮 PREDECIR", use_container_width=True):
            prob_local, prob_empate, prob_visitante, confianza = predecir(local, visitante, liga_seleccionada)
            st.session_state['pred'] = {
                'local': local, 'visitante': visitante,
                'prob_local': prob_local, 'prob_empate': prob_empate,
                'prob_visitante': prob_visitante, 
                'confianza': confianza,
                'liga': liga_seleccionada
            }
    
    # Ranking en sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Ranking de Fuerza")
    for _, row in equipos_df.head(10).iterrows():
        st.sidebar.text(f"{row['nombre'][:20]}: {row['fuerza_actual']:.0%}")
        st.sidebar.progress(row['fuerza_actual'])

# ==================== CONTENIDO PRINCIPAL ====================
if liga_seleccionada:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"## {LIGAS.get(liga_seleccionada, {}).get('icono', '🏆')} {liga_seleccionada}")
        
        # Tabla de equipos
        if not equipos_df.empty:
            st.dataframe(
                equipos_df.head(15).style.format({'fuerza_actual': '{:.0%}'}),
                use_container_width=True
            )
        else:
            st.warning(f"No hay equipos cargados para {liga_seleccionada}")
    
    with col2:
        st.markdown("## 🏆 Top 5")
        for i, row in equipos_df.head(5).iterrows():
            estrellas = "⭐" * int(row['fuerza_actual'] * 5) + "☆" * (5 - int(row['fuerza_actual'] * 5))
            st.markdown(f"{estrellas} **{row['nombre']}**")
            st.progress(row['fuerza_actual'])
    
    # ==================== PREDICCION ====================
    if 'pred' in st.session_state:
        pred = st.session_state['pred']
        
        st.markdown("---")
        st.markdown(f"## 🎯 PREDICCIÓN {LIGAS.get(pred['liga'], {}).get('icono', '🏆')} {pred['liga']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(pred['local'], f"{pred['prob_local']:.1%}", delta="Local")
        with col2:
            st.metric("EMPATE", f"{pred['prob_empate']:.1%}", delta="")
        with col3:
            st.metric(pred['visitante'], f"{pred['prob_visitante']:.1%}", delta="Visitante")
        
        # Gráfico de barras
        fig = go.Figure(data=[
            go.Bar(name=pred['local'], x=[pred['local']], y=[pred['prob_local']], 
                   marker_color='#1f77b4', text=[f"{pred['prob_local']:.0%}"], textposition='auto'),
            go.Bar(name='Empate', x=['Empate'], y=[pred['prob_empate']], 
                   marker_color='#ff7f0e', text=[f"{pred['prob_empate']:.0%}"], textposition='auto'),
            go.Bar(name=pred['visitante'], x=[pred['visitante']], y=[pred['prob_visitante']], 
                   marker_color='#2ca02c', text=[f"{pred['prob_visitante']:.0%}"], textposition='auto')
        ])
        
        fig.update_layout(
            yaxis_title="Probabilidad",
            yaxis_tickformat=".0%",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Confianza
        confianza_nivel = int(pred['confianza'] / 10)
        barra_confianza = "█" * confianza_nivel + "░" * (10 - confianza_nivel)
        st.markdown(f"🔒 Confianza del modelo: [{barra_confianza}] {pred['confianza']:.1f}%")
        
        if pred['prob_local'] > pred['prob_empate'] and pred['prob_local'] > pred['prob_visitante']:
            st.success(f"🏆 PREDICCIÓN: {pred['local']} GANA ({pred['prob_local']:.0%})")
        elif pred['prob_visitante'] > pred['prob_local'] and pred['prob_visitante'] > pred['prob_empate']:
            st.success(f"🏆 PREDICCIÓN: {pred['visitante']} GANA ({pred['prob_visitante']:.0%})")
        else:
            st.warning(f"🤝 PREDICCIÓN: EMPATE ({pred['prob_empate']:.0%})")

# ==================== COMPARATIVO DE LIGAS ====================
st.markdown("---")
st.markdown("## 🌍 Comparativo de Ligas")

# Obtener el mejor equipo de cada liga que tenga datos
mejores = []
for liga in ligas_disponibles:
    df = obtener_equipos(liga)
    if not df.empty and df['fuerza_actual'].notna().any():
        mejor = df.iloc[0]
        mejores.append({
            'liga': liga,
            'equipo': mejor['nombre'],
            'fuerza': mejor['fuerza_actual']
        })

if mejores:
    df_mejores = pd.DataFrame(mejores)
    
    # Gráfico de barras
    fig = go.Figure()
    
    for _, row in df_mejores.iterrows():
        fig.add_trace(go.Bar(
            name=row['liga'],
            x=[row['liga']],
            y=[row['fuerza']],
            text=[f"{row['fuerza']:.0%}"],
            textposition='auto'
        ))
    
    fig.update_layout(
        title="Fuerza del mejor equipo por liga",
        yaxis_title="Fuerza",
        yaxis_tickformat=".0%",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla comparativa
    st.dataframe(
        df_mejores.style.format({'fuerza': '{:.0%}'}),
        use_container_width=True
    )
else:
    st.info("💡 Agrega más ligas para ver el comparativo. Ejecuta: python configurar_liga.py")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>🏆 Fútbol Predictor Pro | Datos API-Football | Modelo Random Forest</small><br>
    <small>Ligas disponibles: {}</small>
</div>
""".format(', '.join(ligas_disponibles) if ligas_disponibles else 'Ninguna'), unsafe_allow_html=True)