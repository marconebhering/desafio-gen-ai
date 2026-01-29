import sys
sys.path.append('src')

import duckdb
from pathlib import Path

def consultar():
    db_path = Path("data/processed/srag_database.duckdb")
    
    if not db_path.exists():
        print("❌ Banco não existe. Execute: python atualizar_dados.py")
        return
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # 1. Total geral
    print("\n📊 TOTAL DE CASOS")
    print("-" * 60)
    total = conn.execute("SELECT COUNT(*) AS n_casos FROM srag_cases").fetchdf()
    print(total)
    
    # 2. Por ano
    print("\n📅 CASOS POR ANO")
    print("-" * 60)
    por_ano = conn.execute("""
        SELECT 
            ano,
            COUNT(*) as total_casos,
            SUM(CASE WHEN EVOLUCAO = 'Óbito' THEN 1 ELSE 0 END) as obitos
        FROM srag_cases
        GROUP BY ano
        ORDER BY ano
    """).fetchdf()
    print(por_ano)
    
    # 3. Por estado (top 10)
    print("\n🗺️ TOP 10 ESTADOS")
    print("-" * 60)
    por_estado = conn.execute("""
        SELECT 
            SG_UF_NOT as estado,
            COUNT(*) as casos
        FROM srag_cases
        GROUP BY SG_UF_NOT
        ORDER BY casos DESC
        LIMIT 10
    """).fetchdf()
    print(por_estado)
    
    # 4. Últimos 30 dias
    print("\n📆 ÚLTIMOS 30 DIAS")
    print("-" * 60)
    ultimos_30 = conn.execute("""
        SELECT 
            DATE_TRUNC('day', DT_NOTIFIC) as data,
            COUNT(*) as casos
        FROM srag_cases
        WHERE DT_NOTIFIC >= CURRENT_DATE - INTERVAL 30 DAY
        GROUP BY DATE_TRUNC('day', DT_NOTIFIC)
        ORDER BY data DESC
        LIMIT 10
    """).fetchdf()
    print(ultimos_30)
    
    conn.close()


if __name__ == "__main__":
    consultar()