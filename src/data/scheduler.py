import schedule
import time
from datetime import datetime
import logging
from ingestor import SRAGIngestor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/update_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def job_atualizar_dados():
    """Job para atualizar os dados"""
    logger.info("🔔 Iniciando job de atualização...")
    
    try:
        ingestor = SRAGIngestor()
        ingestor.update_database()
        logger.info("✅ Job concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no job: {e}")


def run_scheduler():
    """
    Executa o agendador
    Atualiza os dados todos os dias às 2h da manhã
    """
    # Agendar para rodar todo dia às 2h
    schedule.every().day.at("02:00").do(job_atualizar_dados)
    
    logger.info("📅 Agendador iniciado!")
    logger.info("⏰ Próxima atualização agendada para: 02:00")
    
    # Executar imediatamente na primeira vez
    logger.info("🚀 Executando primeira atualização...")
    job_atualizar_dados()
    
    # Loop do agendador
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar a cada minuto


if __name__ == "__main__":
    run_scheduler()