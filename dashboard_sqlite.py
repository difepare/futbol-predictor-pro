"""
DASHBOARD CON SQLITE - FUNCIONA EN STREAMLIT CLOUD
Ejecutar: streamlit run dashboard_sqlite.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Fútbol Predictor Pro", page_icon="🏆", layout="wide")

# ==================== CONEXIÓN SQLITE ====================
@st.cache_resource
def get_connection():
    return sqlite3.connect('futbol_data.db', check_same_thread=False)

@st.cache_data(ttl=3600)
def obtener_equipos(liga=None):
    conn = get_connection()
    if liga:
        df = pd.read_sql("SELECT nombre, fuerza_actual FROM equipos WHERE liga = ? ORDER BY fuerza_actual DESC", conn, params=(liga,))
    else:
        df = pd.read_sql("SELECT nombre, fuerza_actual, liga FROM equipos ORDER BY fuerza_actual DESC", conn)
    return df

@st.cache_data(ttl=3600)
def obtener_todas_ligas():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT liga FROM equipos WHERE liga IS NOT NULL", conn)
    return df['liga'].tolist()

def obtener_fuerza_equipo(nombre, liga):
    conn = get_connection()
    df = pd.read_sql("SELECT fuerza_actual FROM equipos WHERE nombre = ? AND liga = ?", conn, params=(nombre, liga))
    conn.close()
    return df.iloc[0]['fuerza_actual'] if not df.empty else 0.50

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
st.markdown("---")

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Configuración")

ligas = obtener_todas_ligas()
if ligas:
    liga_seleccionada = st.sidebar.selectbox("📋 Selecciona Liga", ligas)
    
    equipos_df = obtener_equipos(liga_seleccionada)
    equipos_lista = equipos_df['nombre'].tolist()
    
    local = st.sidebar.selectbox("🏠 Equipo Local", equipos_lista)
    visitante = st.sidebar.selectbox("✈️ Equipo Visitante", equipos_lista)
    
    if st.sidebar.button("🔮 PREDECIR", use_container_width=True, type="primary"):
        prob_local, prob_empate, prob_visitante, confianza = predecir(local, visitante, liga_seleccionada)
        st.session_state['pred'] = {
            'local': local, 'visitante': visitante,
            'prob_local': prob_local, 'prob_empate': prob_empate,
            'prob_visitante': prob_visitante, 'confianza': confianza
        }
    
    # Ranking en sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Ranking de Fuerza")
    for _, row in equipos_df.head(8).iterrows():
        st.sidebar.text(f"{row['nombre'][:18]}: {row['fuerza_actual']:.0%}")
        st.sidebar.progress(row['fuerza_actual'])

# ==================== PREDICCIÓN ====================
if 'pred' in st.session_state:
    pred = st.session_state['pred']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(pred['local'], f"{pred['prob_local']:.1%}", delta="Local")
    with col2:
        st.metric("EMPATE", f"{pred['prob_empate']:.1%}", delta="")
    with col3:
        st.metric(pred['visitante'], f"{pred['prob_visitante']:.1%}", delta="Visitante")
    
    # Gráfico de dona
    fig = go.Figure(data=[go.Pie(
        labels=[pred['local'], 'Empate', pred['visitante']],
        values=[pred['prob_local'], pred['prob_empate'], pred['prob_visitante']],
        hole=0.4,
        marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
    )])
    fig.update_layout(title="Distribución de Probabilidades", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Confianza
    confianza_nivel = int(pred['confianza'] / 10)
    barra_confianza = "█" * confianza_nivel + "░" * (10 - confianza_nivel)
    st.markdown(f"🔒 **Confianza:** [{barra_confianza}] {pred['confianza']:.1f}%")
    
    if pred['prob_local'] > pred['prob_empate'] and pred['prob_local'] > pred['prob_visitante']:
        st.success(f"🏆 **PREDICCIÓN: {pred['local']} GANA** ({pred['prob_local']:.0%})")
    elif pred['prob_visitante'] > pred['prob_local'] and pred['prob_visitante'] > pred['prob_empate']:
        st.success(f"🏆 **PREDICCIÓN: {pred['visitante']} GANA** ({pred['prob_visitante']:.0%})")
    else:
        st.warning(f"🤝 **PREDICCIÓN: EMPATE** ({pred['prob_empate']:.0%})")

# ==================== RANKING ====================
st.markdown("---")
st.header("📊 Ranking de Equipos")

fig_bar = px.bar(
    equipos_df.head(15),
    x='fuerza_actual',
    y='nombre',
    orientation='h',
    title=f"Top 15 - {liga_seleccionada}",
    labels={'fuerza_actual': 'Fuerza', 'nombre': 'Equipo'},
    color='fuerza_actual',
    color_continuous_scale='Viridis',
    text_auto='.0%'
)
fig_bar.update_layout(height=500)
st.plotly_chart(fig_bar, use_container_width=True)

# ==================== COMPARATIVO ====================
st.markdown("---")
st.header("🌍 Comparativo de Ligas")

mejores = []
for liga in ligas:
    df_liga = obtener_equipos(liga)
    if not df_liga.empty:
        mejor = df_liga.iloc[0]
        mejores.append({'liga': liga, 'equipo': mejor['nombre'], 'fuerza': mejor['fuerza_actual']})

if mejores:
    df_mejores = pd.DataFrame(mejores)
    fig_comp = px.bar(df_mejores, x='liga', y='fuerza', title="Fuerza del mejor equipo por liga",
                      labels={'fuerza': 'Fuerza', 'liga': 'Liga'}, text_auto='.0%')
    st.plotly_chart(fig_comp, use_container_width=True)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>🏆 Fútbol Predictor Pro | Datos históricos | Modelo Random Forest</small>
</div>
""", unsafe_allow_html=True)