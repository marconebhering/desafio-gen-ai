import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SRAGIngestor:
    """Classe para ingestão e atualização de dados SRAG"""
    
    # URLs dos dados
    URLS = {
        2019: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2019/INFLUD19-26-06-2025.parquet"
        # , 2020: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2020/INFLUD20-26-06-2025.parquet"
        # , 2021: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2021/INFLUD21-26-06-2025.parquet"
        # , 2022: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2022/INFLUD22-26-06-2025.parquet"
        # , 2023: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2023/INFLUD23-26-06-2025.parquet"
        # , 2024: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2024/INFLUD24-26-06-2025.parquet"
        # , 2025: "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2025/INFLUD25-26-06-2025.parquet"
    }
    
    # Colunas relevantes
    COLUNAS = [
        "NU_NOTIFIC",
        "DT_NOTIFIC",
        "SG_UF_NOT",
        "CS_SEXO",
        "DT_NASC",
        "CS_RACA",
        "CS_ESCOL_N",
        "VACINA",
        "EVOLUCAO",
        "UTI"
    ]
    
    # Tipos de dados
    DTYPES = {
        "NU_NOTIFIC": "string",
        "SG_UF_NOT": "category",
        "CS_SEXO": "string",
        "CS_RACA": "Int8",
        "CS_ESCOL_N": "Int8",
        "VACINA": "Int8",
        "EVOLUCAO": "Int8",
        "UTI": "category"
    }
    
    # Colunas de data
    DATE_COLS = ["DT_NOTIFIC", "DT_NASC"]
    
    # Mapeamentos para categorias
    MAPS = {
        "CS_SEXO": {
            "M": "Masculino",
            "F": "Feminino",
            "I": "Ignorado"
        },
        "CS_RACA": {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indígena",
            "9": "Ignorado"
        },
        "CS_ESCOL_N": {
            "0": "Sem escolaridade / Analfabeto",
            "1": "Fundamental I",
            "2": "Fundamental II",
            "3": "Médio",
            "4": "Superior",
            "5": "Não se aplica",
            "9": "Ignorado"
        },
        "EVOLUCAO": {
            "1": "Cura",
            "2": "Óbito",
            "3": "Óbito por outras causas",
            "9": "Ignorado"
        },
        "VACINA": {
            "1": "Sim",
            "2": "Não",
            "9": "Ignorado"
        },
        "UTI": {
            "1": "Sim",
            "2": "Não",
            "9": "Ignorado"
        }
    }
    
    def __init__(self, db_path: str = "data/database/srag_database.duckdb"):
        """
        Inicializa o ingestor
        
        Args:
            db_path: Caminho para o banco DuckDB
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load_year(self, url: str, ano: int) -> pd.DataFrame:
        """
        Carrega dados de um ano específico
        
        Args:
            url: URL do arquivo CSV
            ano: Ano dos dados
            
        Returns:
            DataFrame com os dados carregados
        """
        logger.info(f"⚡ Carregando {ano}...")
        
        try:
            df = pd.read_parquet(
                url,
                columns=self.COLUNAS
            )
            
            df["ano"] = ano
            logger.info(f"✅ {ano}: {len(df):,} registros carregados")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {ano}: {e}")
            return pd.DataFrame()
    
    def apply_mappings(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("🔄 Aplicando mapeamentos de categorias...")

        for col, mapping in self.MAPS.items():
            if col not in df.columns:
                continue

            # Preencher None com "9" (Ignorado) para colunas que têm essa chave
            if "9" in mapping:
                df[col] = df[col].fillna("9")
            
            # Aplicar mapeamento direto (agora com strings)
            df[col] = df[col].map(mapping)
            
            # Converter para categoria
            df[col] = df[col].astype("category")

        return df
    
    def load_all_data(self, anos: List[int] = None) -> pd.DataFrame:
        """
        Carrega dados de todos os anos (ou anos específicos)
        
        Args:
            anos: Lista de anos para carregar (None = todos)
            
        Returns:
            DataFrame consolidado
        """
        if anos is None:
            anos = list(self.URLS.keys())
        
        logger.info(f"📥 Iniciando carregamento de {len(anos)} anos...")
        
        dfs = []
        for ano in anos:
            if ano in self.URLS:
                df = self.load_year(self.URLS[ano], ano)
                if not df.empty:
                    dfs.append(df)
        
        if not dfs:
            logger.error("❌ Nenhum dado foi carregado!")
            return pd.DataFrame()
        
        # Concatenar todos os DataFrames
        logger.info("🔗 Consolidando dados...")
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Aplicar mapeamentos
        df_final = self.apply_mappings(df_final)
        
        logger.info(f"✅ Total de registros consolidados: {len(df_final):,}")
        logger.info(f"✅ Total de colunas: {len(df_final.columns)}")
        
        return df_final
    
    def save_to_duckdb(self, df: pd.DataFrame, table_name: str = "srag_cases"):
        """
        Salva DataFrame no DuckDB
        
        Args:
            df: DataFrame para salvar
            table_name: Nome da tabela
        """
        logger.info(f"💾 Salvando no DuckDB: {self.db_path}")
        
        conn = duckdb.connect(str(self.db_path))
        
        try:
            # Criar ou substituir a tabela
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.execute(f"""CREATE TABLE {table_name} AS 
                         SELECT 
                            * EXCLUDE(DT_NASC, DT_NOTIFIC)
                            , CAST(DT_NASC AS DATE) AS DT_NASC
                            , CAST(DT_NOTIFIC AS DATE) AS DT_NOTIFIC
                         FROM df
                         """
                        )
            
            # Criar índices para melhor performance
            logger.info("📊 Criando índices...")
            conn.execute(f"CREATE INDEX idx_dt_notific ON {table_name}(DT_NOTIFIC)")
            conn.execute(f"CREATE INDEX idx_uf ON {table_name}(SG_UF_NOT)")
            conn.execute(f"CREATE INDEX idx_ano ON {table_name}(ano)")
            
            # Verificar quantidade de registros
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"✅ {count:,} registros salvos na tabela '{table_name}'")
            
            # Salvar metadados da atualização
            self._save_metadata(conn)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar no DuckDB: {e}")
            raise
        
        finally:
            conn.close()
    
    def _save_metadata(self, conn):
        """Salva metadados da última atualização"""
        metadata = {
            'ultima_atualizacao': [datetime.now()],
            'versao': ['1.0']
        }
        
        df_meta = pd.DataFrame(metadata)
        conn.execute("DROP TABLE IF EXISTS metadata")
        conn.execute("CREATE TABLE metadata AS SELECT * FROM df_meta")
        
        logger.info("📝 Metadados salvos")
    
    def get_last_update(self) -> datetime:
        """
        Retorna a data da última atualização
        
        Returns:
            Datetime da última atualização ou None
        """
        if not self.db_path.exists():
            return None
        
        conn = duckdb.connect(str(self.db_path), read_only=True)
        
        try:
            result = conn.execute(
                "SELECT ultima_atualizacao FROM metadata LIMIT 1"
            ).fetchone()
            
            if result:
                return result[0]
            return None
            
        except:
            return None
        
        finally:
            conn.close()
    
    def update_database(self, force: bool = False):
        """
        Atualiza o banco de dados
        
        Args:
            force: Se True, força atualização mesmo se já foi atualizado hoje
        """
        logger.info("🔄 Verificando necessidade de atualização...")
        
        last_update = self.get_last_update()
        
        if last_update and not force:
            hoje = datetime.now().date()
            if last_update.date() == hoje:
                logger.info("✅ Banco já está atualizado hoje. Use force=True para forçar.")
                return
        
        logger.info("🚀 Iniciando atualização completa...")
        
        # Carregar dados
        df = self.load_all_data()
        
        if df.empty:
            logger.error("❌ Nenhum dado para atualizar!")
            return
        
        # Salvar no DuckDB
        self.save_to_duckdb(df)
        
        
        logger.info("🎉 Atualização concluída com sucesso!")


def main():
    """Função principal para executar a ingestão"""
    ingestor = SRAGIngestor()

    ingestor.update_database(force=True)

if __name__ == "__main__":
    main()