from django.core.management.base import BaseCommand
from reports.utils.enviar_aht import send_teams_report

class Command(BaseCommand):
    help = 'Envía el reporte diario a Teams'

    def handle(self, *args, **kwargs):
        send_teams_report()
        self.stdout.write(self.style.SUCCESS("✅ Reporte enviado correctamente"))
