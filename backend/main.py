from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conexao = sqlite3.connect("historico_irrigacao.db", check_same_thread=False)
cursor = conexao.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS irrigacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        chuva_mm REAL,
        precisa_irrigar BOOLEAN
    )
""")
conexao.commit()

LATITUDE = "-26.22"
LONGITUDE = "-52.67"

@app.get("/")
def home():
    return {"mensagem": "API da Irrigação rodando perfeitamente!"}

@app.get("/api/status-irrigacao")
def verificar_status():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=precipitation"
    
    try:
        resposta = requests.get(url).json()
        chuva_atual = resposta["current"]["precipitation"]
        
        precisa_irrigar = True if chuva_atual < 0.5 else False
        
        cursor.execute(
            "INSERT INTO irrigacao (chuva_mm, precisa_irrigar) VALUES (?, ?)", 
            (chuva_atual, precisa_irrigar)
        )
        conexao.commit()
        
        return {
            "chuva_mm": chuva_atual,
            "precisa_irrigar": precisa_irrigar
        }
    except Exception as e:
        return {"erro": "Falha ao consultar a API do tempo", "detalhe": str(e)}