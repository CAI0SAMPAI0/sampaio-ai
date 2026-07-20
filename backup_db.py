import os
import sys
import django
from django.core.management import call_command

def run_backup():
    # Adiciona o diretório atual ao path para garantir importações
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Exporta dados do banco ignorando logs e tabelas de historico temporario
        call_command(
            'dumpdata', 
            exclude=['contenttypes', 'auth.Permission', 'sessions.Session'], 
            indent=4, 
            stdout=f
        )
    print(f"Backup completo criado com sucesso em: {filename}")

if __name__ == '__main__':
    run_backup()
