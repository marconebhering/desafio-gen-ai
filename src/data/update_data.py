import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingestor import SRAGIngestor

def main():
    print("🚀 Atualizando dados SRAG...")
    print("="*60)
    
    ingestor = SRAGIngestor()
    
    ingestor.update_database(force=True)
    
    # Mostrar estatísticas
    print("\n" + "="*60)
    print("📊 RESUMO")
    print("="*60)
    
    stats = ingestor.get_stats()
    
    print(f"\n✅ Total: {stats['total_registros']:,} registros")
    print(f"📅 Período: {stats['periodo']['inicio']} a {stats['periodo']['fim']}")
    print(f"🕒 Última atualização: {stats['ultima_atualizacao']}")
    
    print("\n📊 Por ano:")
    for item in stats['por_ano']:
        print(f"   {item['ano']}: {item['casos']:,} casos")


if __name__ == "__main__":
    main()