"""
SISTEMA DE LESIONES Y TARJETAS
Monitorea jugadores lesionados y suspendidos
"""

import requests
import psycopg2
from datetime import datetime, timedelta

API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

DB_CONFIG = {
    'dbname': 'premier_predictor',
    'user': 'postgres',
    'password': 'Sarita2017',
    'host': 'localhost'
}

def obtener_lesiones(liga_nombre, liga_id):
    """Obtiene lesiones actuales de una liga"""
    print(f"\n🤕 Obteniendo lesiones de {liga_nombre}...")
    
    url = f"{BASE_URL}/injuries"
    params = {"league": liga_id, "season": 2025}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        lesionados = []
        for injury in data.get('response', []):
            player = injury.get('player', {})
            team = injury.get('team', {})
            
            lesionados.append({
                'jugador': player.get('name', 'Desconocido'),
                'equipo': team.get('name', 'Desconocido'),
                'tipo': injury.get('type', 'Lesión'),
                'fecha_inicio': injury.get('date_start'),
                'fecha_retorno': injury.get('date_return')
            })
        
        return lesionados
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def obtener_tarjetas_suspensiones(liga_nombre, liga_id):
    """Obtiene acumulación de tarjetas y suspensiones"""
    print(f"\n🟨 Obteniendo tarjetas de {liga_nombre}...")
    
    # Los jugadores con 5 amarillas se suspenden 1 partido
    url = f"{BASE_URL}/players"
    params = {"league": liga_id, "season": 2025}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        suspendidos = []
        for player_data in data.get('response', []):
            player = player_data.get('player', {})
            statistics = player_data.get('statistics', [{}])[0]
            cards = statistics.get('cards', {})
            
            amarillas = cards.get('yellow', 0)
            rojas = cards.get('red', 0)
            
            if amarillas >= 5 or rojas >= 1:
                suspendidos.append({
                    'jugador': player.get('name', 'Desconocido'),
                    'equipo': statistics.get('team', {}).get('name', 'Desconocido'),
                    'amarillas': amarillas,
                    'rojas': rojas,
                    'suspendido': amarillas >= 5 or rojas >= 1,
                    'partidos_suspension': 1 if amarillas >= 5 else (2 if rojas >= 1 else 0)
                })
        
        return suspendidos
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def calcular_factor_lesiones_equipo(equipo, liga_nombre):
    """Calcula el factor de impacto por lesiones para un equipo"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT api_team_id FROM equipos WHERE nombre = %s AND liga = %s", (equipo, liga_nombre))
    resultado = cur.fetchone()
    conn.close()
    
    if not resultado:
        return 1.0
    
    team_id = resultado[0]
    
    lesionados = obtener_lesiones(liga_nombre, team_id)
    num_lesionados = len(lesionados)
    
    # Cada lesionado reduce la fuerza del equipo en 2-3%
    factor = max(0.75, 1.0 - (num_lesionados * 0.025))
    
    return factor