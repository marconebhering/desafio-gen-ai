"""
Módulo de consultas ao banco de dados SRAG usando DuckDB
"""

import duckdb
from pathlib import Path

def get_db_connection():
    """Conecta ao banco de dados DuckDB"""
    # Caminho absoluto baseado na localização deste arquivo
    db_path = Path(__file__).parent / "database" / "srag_database.duckdb"
    return duckdb.connect(str(db_path))


def get_metrics_data():
    """Obtém todas as métricas do banco de dados"""
    conn = get_db_connection()
    
    try:
        # Taxa de Aumento (comparação últimos 7 dias vs 7 dias anteriores)
        query_aumento = """
        WITH base AS (
            SELECT
                date_trunc('month', DT_NOTIFIC) AS mes,
                MAX(DT_NOTIFIC) OVER () AS data_max
            FROM srag_cases
        ),
        filtrado AS (
            SELECT *
            FROM base
            WHERE mes >= date_trunc('month', data_max) - INTERVAL '11 months'
        )
        SELECT
            mes,
            COUNT(*) AS total_casos
        FROM filtrado
        GROUP BY mes
        ORDER BY mes;
        """
        rows = conn.execute(query_aumento).fetchall()

        meses = []
        casos_mensais = []

        for mes, total in rows:
            meses.append(mes)
            casos_mensais.append(total)
            if len(casos_mensais) >= 2 and casos_mensais[-2] > 0:
                taxa_aumento_mom = round(
                    (casos_mensais[-1] - casos_mensais[-2]) / casos_mensais[-2] * 100,
                    1
                )
            else:
                taxa_aumento_mom = 0
        
        # Taxa de Mortalidade (EVOLUCAO = 2 significa óbito)
        query_mortalidade = """
        WITH base AS (
            SELECT
                *,
                MAX(DT_NOTIFIC) OVER () AS data_max
            FROM srag_cases
        ),
        filtrado AS (
            SELECT *
            FROM base
            WHERE DT_NOTIFIC >= data_max - INTERVAL '1 year'
        ),
        mensal AS (
            SELECT
                date_trunc('month', DT_NOTIFIC) AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END) AS total_obitos,
                SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS taxa_mortalidade
            FROM filtrado
            GROUP BY periodo
        ),
        anual AS (
            SELECT
                'TOTAL_12_MESES' AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END) AS total_obitos,
                SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS taxa_mortalidade
            FROM filtrado
        )
        SELECT *
        FROM mensal

        UNION ALL

        SELECT *
        FROM anual

        ORDER BY periodo;
        """
        result_mortalidade = conn.execute(query_mortalidade).fetchall()

        taxa_mortalidade = 0
        taxa_mortalidade_mensal = []
        meses = []

        for row in result_mortalidade:
            periodo = row[0]
            taxa = round(row[3] or 0, 1)

            if periodo == "TOTAL_12_MESES":
                taxa_mortalidade = taxa
            else:
                meses.append(periodo)
                taxa_mortalidade_mensal.append(taxa)
        
        # Ocupação UTI (UTI = 1 significa internação em UTI)
        query_uti = """
        WITH base AS (
            SELECT
                *,
                MAX(DT_NOTIFIC) OVER () AS data_max
            FROM srag_cases
        ),
        filtrado AS (
            SELECT *
            FROM base
            WHERE DT_NOTIFIC >= data_max - INTERVAL '1 year'
        ),
        mensal AS (
            SELECT
                date_trunc('month', DT_NOTIFIC) AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN UTI = 'Sim' THEN 1 ELSE 0 END) AS casos_uti,
                SUM(CASE WHEN UTI = 'Sim' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS ocupacao_uti
            FROM filtrado
            GROUP BY periodo
        ),
        anual AS (
            SELECT
                'TOTAL_12_MESES' AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN UTI = 'Sim' THEN 1 ELSE 0 END) AS casos_uti,
                SUM(CASE WHEN UTI = 'Sim' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS ocupacao_uti
            FROM filtrado
        )
        SELECT *
        FROM mensal
        UNION ALL
        SELECT *
        FROM anual
        ORDER BY periodo;
        """
        result_uti = conn.execute(query_uti).fetchall()

        ocupacao_uti = 0
        ocupacao_uti_mensal = []
        meses_uti = []

        for row in result_uti:
            periodo = row[0]
            taxa = round(row[3] or 0, 1)

            if periodo == "TOTAL_12_MESES":
                ocupacao_uti = taxa
            else:
                meses_uti.append(periodo)
                ocupacao_uti_mensal.append(taxa)

        
        # Taxa de Vacinação (VACINA = 1 significa vacinado)
        query_vacinacao = """
        WITH base AS (
            SELECT
                *,
                MAX(DT_NOTIFIC) OVER () AS data_max
            FROM srag_cases
        ),
        filtrado AS (
            SELECT *
            FROM base
            WHERE DT_NOTIFIC >= data_max - INTERVAL '1 year'
        ),
        mensal AS (
            SELECT
                date_trunc('month', DT_NOTIFIC) AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN VACINA = 'Sim' THEN 1 ELSE 0 END) AS vacinados,
                SUM(CASE WHEN VACINA = 'Sim' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS taxa_vacinacao
            FROM filtrado
            GROUP BY periodo
        ),
        anual AS (
            SELECT
                'TOTAL_12_MESES' AS periodo,
                COUNT(*) AS total_casos,
                SUM(CASE WHEN VACINA = 'Sim' THEN 1 ELSE 0 END) AS vacinados,
                SUM(CASE WHEN VACINA = 'Sim' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0) * 100 AS taxa_vacinacao
            FROM filtrado
        )
        SELECT *
        FROM mensal
        UNION ALL
        SELECT *
        FROM anual
        ORDER BY periodo;
        """
        result_vacinacao = conn.execute(query_vacinacao).fetchall()

        taxa_vacinacao = 0
        taxa_vacinacao_mensal = []
        meses_vac = []

        for row in result_vacinacao:
            periodo = row[0]
            taxa = round(row[3] or 0, 1)  # 👈 arredondamento aqui

            if periodo == "TOTAL_12_MESES":
                taxa_vacinacao = taxa
            else:
                meses_vac.append(periodo)
                taxa_vacinacao_mensal.append(taxa)
        
        return {
            "taxa_mortalidade": taxa_mortalidade,
            "taxa_mortalidade_mensal": taxa_mortalidade_mensal,
            "ocupacao_uti": ocupacao_uti,
            "ocupacao_uti_mensal": ocupacao_uti_mensal,
            "taxa_vacinacao": taxa_vacinacao,
            "taxa_vacinacao_mensal": taxa_vacinacao_mensal,
            "taxa_aumento": taxa_aumento_mom,
            "casos_mensais": casos_mensais
        }
    
    except Exception as e:
        print(f"Erro ao consultar banco de dados: {e}")
        return {
            "taxa_aumento": 0,
            "taxa_mortalidade": 0,
            "ocupacao_uti": 0,
            "taxa_vacinacao": 0,
            "casos_aumento": 0
        }


def get_daily_cases():
    """Obtém casos diários dos últimos 30 dias"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        DATE(DT_NOTIFIC) as data,
        COUNT(*) as casos
    FROM srag_cases
    WHERE 1=1
        AND DT_NOTIFIC BETWEEN (SELECT MAX(DT_NOTIFIC) - INTERVAL '30 days' FROM srag_cases) AND (SELECT MAX(DT_NOTIFIC) FROM srag_cases)
    GROUP BY DATE(DT_NOTIFIC)
    ORDER BY data
    """
    
    df = conn.execute(query).fetch_df()
    return df


def get_monthly_cases():
    """Obtém casos mensais dos últimos 12 meses"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        DATE_TRUNC('month', DT_NOTIFIC) as mes,
        COUNT(*) as casos
    FROM srag_cases
    WHERE 1=1
        AND DT_NOTIFIC BETWEEN (SELECT MAX(DT_NOTIFIC) - INTERVAL '12 months' FROM srag_cases) AND (SELECT MAX(DT_NOTIFIC) FROM srag_cases)
    GROUP BY DATE_TRUNC('month', DT_NOTIFIC)
    ORDER BY mes
    """
    
    df = conn.execute(query).fetch_df()
    return df
