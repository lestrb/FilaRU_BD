import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

# Configurações de conexão obtidas via .env (veja .env.example ou README)
token = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN", "TOKEN_DO_INFLUXDB")
org = os.getenv("DOCKER_INFLUXDB_INIT_ORG", "ufpe")
bucket = os.getenv("DOCKER_INFLUXDB_INIT_BUCKET", "ru_ufpe")
url = os.getenv("INFLUXDB_URL", "http://localhost:8086")

# Tenta conectar/checar saúde do InfluxDB antes de escrever (retry simples)
max_retries = 10
for attempt in range(1, max_retries + 1):
    try:
        client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)
        health = client.health()
        status = None
        if isinstance(health, dict):
            status = health.get("status")
        else:
            status = getattr(health, "status", None)
        if status == "pass" or status == "pass":
            break
        else:
            raise Exception("InfluxDB health not passing")
    except Exception:
        print(f"Tentativa {attempt}/{max_retries}: InfluxDB indisponível em {url}, aguardando 3s...")
        time.sleep(3)
else:
    raise SystemExit("Não foi possível conectar ao InfluxDB. Verifique o container Docker e as variáveis de ambiente.")

write_api = client.write_api(write_options=SYNCHRONOUS)

# Função auxiliar pra determinar o status da fila
def obter_status_fila(qtd):
    if qtd <= 30:
        return "baixa"
    elif qtd <= 70:
        return "moderada"
    elif qtd <= 100:
        return "alta"
    else:
        return "critica"

# Mapeamento dos dias da semana (0 = segunda, 6 = domingo)
nomes_dias = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

# Simulação de dados fictícios (Gerando registros de 15 em 15 minutos)
data_inicio = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)  # 1º de Junho de 2026 (Segunda-feira)

# Simula 1 semana inteira: 7 dias * 24 horas * 4 medições/hora = 672 medições
for i in range(672):
    tempo_atual = data_inicio + timedelta(minutes=15 * i)
    hora = tempo_atual.hour

    # Define o dia da semana atual dinamicamente
    dia_semana_atual = nomes_dias[tempo_atual.weekday()]

    # Opcional: Pula a geração de dados nos fins de semana (sábado = 5, domingo = 6)
    if tempo_atual.weekday() >= 5:
        continue

    # Define se é almoço, jantar ou intervalo
    if 10 <= hora <= 14:
        refeicao = "almoco"
        turno = "tarde" if hora >= 12 else "manha"
        qtd_pessoas = 115 if (12 <= hora <= 13) else 40  # Pico no meio do almoço
    elif 16 <= hora <= 19:
        refeicao = "jantar"
        turno = "noite"
        qtd_pessoas = 60
    else:
        continue  # RU fechado, não registra

    status = obter_status_fila(qtd_pessoas)

    # Cria o ponto no modelo InfluxDB
    point = Point("fila_ru") \
        .tag("refeicao", refeicao) \
        .tag("dia_semana", dia_semana_atual) \
        .tag("turno", turno) \
        .tag("periodo_mes", "inicio") \
        .tag("status_fila", status) \
        .field("quantidade_pessoas", qtd_pessoas) \
        .field("tempo_espera_minutos", int(qtd_pessoas * 0.3)) \
        .field("tempo_atendimento_minutos", 2) \
        .time(tempo_atual, WritePrecision.NS)

    # Envio para o InfluxDB
    write_api.write(bucket=bucket, org=org, record=point)

print("Dados de uma semana inteira simulados e inseridos com sucesso no InfluxDB!")
client.close()