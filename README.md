# FilaRU_BD (InfluxDB)

Este projeto usa **InfluxDB** em Docker (porta padrão **8086**) para armazenar e consultar as medições da fila do RU.

## Configuração do InfluxDB (Docker)

1) Pré-requisito: ter **Docker Desktop** instalado.

2) Crie o arquivo de variaveis de ambiente:

- Copie `.env.example` para `.env`
- Edite `.env` e ajuste `USERNAME`, `PASSWORD`, `ORG`, `BUCKET` e principalmente o `ADMIN_TOKEN`

Para gerar um token forte rapidamente:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3) Suba o container:

```bash
docker compose up -d
```

4) Acesse a UI do InfluxDB:

- http://localhost:8086

Observação: as variáveis `DOCKER_INFLUXDB_INIT_*` só são aplicadas na **primeira** vez que o InfluxDB sobe (quando os volumes ainda estão vazios). Se você alterar o `.env` depois, pode precisar executar `docker compose down -v` para recriar tudo do zero.

## Persistência de dados (volumes)

O `docker-compose.yml` usa **volumes nomeados** para persistir dados e configuração:

- `influxdb2-data` → `/var/lib/influxdb2`
- `influxdb2-config` → `/etc/influxdb2`

Isso significa que, mesmo que você pare e suba novamente, os dados continuam.

## Parar / remover

Parar mantendo os dados:

```bash
docker compose down
```

Remover **e apagar os dados** (cuidado):

```bash
docker compose down -v
```

## Variáveis importantes

As variaveis usadas no setup automatico (primeira subida) estao no `.env`:

- `DOCKER_INFLUXDB_INIT_USERNAME` / `DOCKER_INFLUXDB_INIT_PASSWORD`
- `DOCKER_INFLUXDB_INIT_ORG`
- `DOCKER_INFLUXDB_INIT_BUCKET`
- `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`
