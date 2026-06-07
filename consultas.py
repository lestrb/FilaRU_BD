
import os
import time
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient

load_dotenv()

# Configurações via .env
token = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN", "TOKEN_DO_INFLUXDB")
org = os.getenv("DOCKER_INFLUXDB_INIT_ORG", "ufpe")
bucket = os.getenv("DOCKER_INFLUXDB_INIT_BUCKET", "ru_ufpe")
url = os.getenv("INFLUXDB_URL", "http://localhost:8086")

# Inicializa o cliente com retry/cheque de saúde
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
  except Exception:
    print(f"Tentativa {attempt}/{max_retries}: InfluxDB indisponível em {url}, aguardando 2s...")
    time.sleep(2)
else:
  raise SystemExit("Não foi possível conectar ao InfluxDB. Verifique o container Docker e as variáveis de ambiente.")

query_api = client.query_api()

print("=" * 60)
print("   CONECTADO AO INFLUXDB - RELATÓRIOS SEMANAIS DO RU UFPE")
print("=" * 60)

# Definindo o período completo da simulação (Janela de 1 semana)
START_TIME = "2026-06-01T00:00:00Z"
STOP_TIME = "2026-06-08T00:00:00Z"

# CONSULTA 1: Média de pessoas na fila por hora no horário do almoço
print("\n[Consulta 1] Média de pessoas na fila por hora (Almoço - Período Todo):")

query_a = f"""
from(bucket: "{bucket}")
  |> range(start: {START_TIME}, stop: {STOP_TIME})
  |> filter(fn: (r) => r["_measurement"] == "fila_ru")
  |> filter(fn: (r) => r["_field"] == "quantidade_pessoas")
  |> filter(fn: (r) => r["refeicao"] == "almoco")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "media_fila_almoco")
"""

resultado_a = query_api.query(query_a, org=org)

for tabela in resultado_a:
    for registro in tabela.records:
        horario = registro.get_time().strftime('%d/%m %H:%M')
        media_pessoas = round(registro.get_value(), 1)
        print(f" -> Horário: {horario} | Média: {media_pessoas} pessoas")

# CONSULTA 2: Identificação dos horários em que a fila ficou em estado Crítico
print("\n" + "-"*60)
print("[Consulta 2] Alerta! Horários com Fila em Estado CRÍTICO na semana:")

query_b = f"""
from(bucket: "{bucket}")
  |> range(start: {START_TIME}, stop: {STOP_TIME})
  |> filter(fn: (r) => r["_measurement"] == "fila_ru")
  |> filter(fn: (r) => r["status_fila"] == "critica")
  |> filter(fn: (r) => r["_field"] == "quantidade_pessoas")
  |> keep(columns: ["_time", "_value"])
"""

resultado_b = query_api.query(query_b, org=org)

linhas_criticas = 0
for tabela in resultado_b:
    for registro in tabela.records:
        horario = registro.get_time().strftime('%d/%m/%Y %H:%M')
        print(f" 🚨 ALERTA: Fila crítica em {horario} ({registro.get_value()} pessoas)")
        linhas_criticas += 1

if linhas_criticas == 0:
    print(" -> Nenhum horário crítico registrado no período.")

# CONSULTA 3: Comparação global de tempo de espera (Almoço vs Jantar)
print("\n" + "-"*60)
print("[Consulta 3] Comparação do Tempo Médio de Espera Geral (Minutos):")

query_c = f"""
from(bucket: "{bucket}")
  |> range(start: {START_TIME}, stop: {STOP_TIME})
  |> filter(fn: (r) => r["_measurement"] == "fila_ru")
  |> filter(fn: (r) => r["_field"] == "tempo_espera_minutos")
  |> group(columns: ["refeicao"])
  |> mean()
"""
# group() quebra os dados em múltiplas tabelas internas independentes (uma para cada tag)

resultado_c = query_api.query(query_c, org=org)

for tabela in resultado_c:
    for registro in tabela.records:
        tipo_refeicao = registro.values.get("refeicao").capitalize()
        tempo_medio = round(registro.get_value(), 1)
        print(f" -> {tipo_refeicao}: {tempo_medio} minutos de espera em média")

# NOVA CONSULTA 4: Média de pessoas por dia da semana (Aproveitando a tag dinâmica)
print("\n" + "-"*60)
print("[Consulta 4] Movimentação Média por Dia da Semana:")

query_d = f"""
from(bucket: "{bucket}")
  |> range(start: {START_TIME}, stop: {STOP_TIME})
  |> filter(fn: (r) => r["_measurement"] == "fila_ru")
  |> filter(fn: (r) => r["_field"] == "quantidade_pessoas")
  |> group(columns: ["dia_semana"])
  |> mean()
"""

resultado_d = query_api.query(query_d, org=org)

for tabela in resultado_d:
    for registro in tabela.records:
        dia = registro.values.get("dia_semana").capitalize()
        media_dia = round(registro.get_value(), 1)
        print(f" -> {dia}: média de {media_dia} pessoas na fila")

print("\n" + "=" * 60)

# Fecha a conexão de forma limpa
client.close()