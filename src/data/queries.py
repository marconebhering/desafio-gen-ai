"""
Módulo de consultas ao banco de dados SRAG usando DuckDB
"""

import duckdb
import pandas as pd
from pathlib import Path


def get_db_connection():
    """Conecta ao banco de dados DuckDB"""
    db_path = Path(__file__).parent / "database" / "srag_database.duckdb"
    return duckdb.connect(str(db_path))


def get_metrics_data():
    """Obtém todas as métricas do banco de dados"""
    conn = get_db_connection()
    
    try:
        # Taxa de Aumento (comparação últimos 7 dias vs 7 dias anteriores)
        query_aumento = """
        SELECT 
            SUM(CASE WHEN DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '7 days' AND CURRENT_DATE THEN 1 ELSE 0 END) as casos_recentes,
            SUM(CASE WHEN DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '14 days' AND CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) as casos_anteriores
        FROM srag_cases
        """
        result_aumento = conn.execute(query_aumento).fetchall()
        casos_recentes = result_aumento[0][0] or 0
        casos_anteriores = result_aumento[0][1] or 0
        
        if casos_anteriores > 0:
            taxa_aumento = ((casos_recentes - casos_anteriores) / casos_anteriores) * 100
        else:
            taxa_aumento = 0
        
        # Taxa de Mortalidade (EVOLUCAO = 2 significa óbito)
        query_mortalidade = """
        SELECT 
            COUNT(EVOLUCAO) as total_casos,
            SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END) as total_obitos
        FROM srag_cases
        """
        result_mortalidade = conn.execute(query_mortalidade).fetchall()
        total_casos = result_mortalidade[0][0] or 0
        total_obitos = result_mortalidade[0][1] or 0
        
        taxa_mortalidade = (total_obitos / total_casos * 100) if total_casos > 0 else 0
        
        # Ocupação UTI (UTI = 1 significa internação em UTI)
        query_uti = """
        SELECT 
            COUNT(*) as total_casos,
            SUM(CASE WHEN UTI = 1 THEN 1 ELSE 0 END) as casos_uti
        FROM srag_cases
        WHERE DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
        """
        result_uti = conn.execute(query_uti).fetchall()
        total_casos_uti = result_uti[0][0] or 0
        casos_uti = result_uti[0][1] or 0
        
        ocupacao_uti = (casos_uti / total_casos_uti * 100) if total_casos_uti > 0 else 0
        
        # Taxa de Vacinação (VACINA = 1 significa vacinado)
        query_vacinacao = """
        SELECT 
            COUNT(*) as total_casos,
            SUM(CASE WHEN VACINA = 1 THEN 1 ELSE 0 END) as vacinados
        FROM srag_cases
        WHERE DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
        """
        result_vacinacao = conn.execute(query_vacinacao).fetchall()
        total_casos_vac = result_vacinacao[0][0] or 0
        vacinados = result_vacinacao[0][1] or 0
        
        taxa_vacinacao = (vacinados / total_casos_vac * 100) if total_casos_vac > 0 else 0
        
        return {
            "taxa_aumento": taxa_aumento,
            "taxa_mortalidade": taxa_mortalidade,
            "ocupacao_uti": ocupacao_uti,
            "taxa_vacinacao": taxa_vacinacao,
            "casos_aumento": (casos_recentes - casos_anteriores)
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
    WHERE DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
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
    WHERE DT_NOTIFIC BETWEEN CURRENT_DATE - INTERVAL '12 months' AND CURRENT_DATE
    GROUP BY DATE_TRUNC('month', DT_NOTIFIC)
    ORDER BY mes
    """
    
    df = conn.execute(query).fetch_df()
    return df
