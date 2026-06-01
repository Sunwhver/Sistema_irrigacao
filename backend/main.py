from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Conexão com o banco de dados SQLite
conexao = sqlite3.connect("historico_irrigacao.db", check_same_thread=False)
cursor = conexao.cursor()

# Passo 2: Reestruturação da tabela de log para incluir o estado do solo e alertas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS log_irrigacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        solo_seco BOOLEAN,
        chuva_prevista_mm REAL,
        decisao_irrigar BOOLEAN,
        alerta_emitido TEXT
    )
""")
conexao.commit()

LATITUDE = "-26.22"
LONGITUDE = "-52.67"

# Passo 3: Modelo de dados que o NodeMCU enviará
class LeituraSensor(BaseModel):
    solo_seco: bool  # True se o sensor detectar solo seco, False se detectar solo úmido

@app.get("/")
def home():
    return {"mensagem": "API da Irrigação rodando perfeitamente!"}

# Passo 4: Nova rota POST para receber dados do NodeMCU e processar a decisão
@app.post("/api/processar-leitura")
def processar_leitura(leitura: LeituraSensor):
    url_clima = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=precipitation_sum&timezone=America%2FSao_Paulo&forecast_days=2"
    
    try:
        # Busca a previsão do tempo real
        resposta = requests.get(url_clima).json()
        chuva_hoje = resposta["daily"]["precipitation_sum"][0]
        chuva_amanha = resposta["daily"]["precipitation_sum"][1]
        
        chuva_total_esperada = chuva_hoje + chuva_amanha
        
        # Definição do limiar de chuva (ex: acima de 0.5mm é considerado chuva relevante)
        vai_chover = chuva_total_esperada >= 0.5
        
        # Passo 1: Aplicação da Matriz de Decisão
        decisao_irrigar = False
        alerta = "Nenhum"

        if leitura.solo_seco and not vai_chover:
            decisao_irrigar = True
        elif leitura.solo_seco and vai_chover:
            decisao_irrigar = False
            alerta = "Chuva prevista. Irrigação cancelada para economizar água."
        elif not leitura.solo_seco and vai_chover:
            decisao_irrigar = False
            alerta = "ALERTA: O solo já está úmido e há previsão de chuva."
        elif not leitura.solo_seco and not vai_chover:
            decisao_irrigar = False
            alerta = "Solo possui umidade adequada no momento."

        # Inserção do log completo no banco de dados
        cursor.execute(
            """INSERT INTO log_irrigacao 
               (solo_seco, chuva_prevista_mm, decisao_irrigar, alerta_emitido) 
               VALUES (?, ?, ?, ?)""", 
            (leitura.solo_seco, chuva_total_esperada, decisao_irrigar, alerta)
        )
        conexao.commit()
        
        # Retorno da decisão para o NodeMCU e para o Frontend
        return {
            "status_solo_seco": leitura.solo_seco,
            "chuva_prevista_mm": chuva_total_esperada,
            "acao_irrigar": decisao_irrigar,
            "mensagem_alerta": alerta
        }

    except Exception as e:
        return {"erro": "Falha ao processar os dados", "detalhe": str(e)}

@app.get("/api/historico")
def obter_historico():
    # Rota auxiliar para o Frontend exibir o log completo
    cursor.execute("SELECT * FROM log_irrigacao ORDER BY id DESC LIMIT 10")
    colunas = [descricao[0] for descricao in cursor.description]
    logs = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    return {"historico": logs}