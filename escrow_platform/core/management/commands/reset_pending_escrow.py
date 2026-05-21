"""
Set pending escrow(s) to 'failed' so you can retry deposit (e.g. after a hung or expired M-Pesa STK).
Usage:
  python manage.py reset_pending_escrow
  python manage.py reset_pending_escrow --project <project-uuid>
"""
from django.core.management.base import BaseCommand
from core.models import Escrow


class Command(BaseCommand):
    help = "Set pending escrow to 'failed' so the client can retry M-Pesa deposit."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            type=str,
            help="Project UUID to reset. If omitted, all pending escrows are reset.",
        )
        parser.add_argument("--no-input", action="store_true", help="Skip confirmation.")

    def handle(self, *args, **options):
        qs = Escrow.objects.filter(status="pending")
        if options.get("project"):
            qs = qs.filter(contract__project_id=options["project"])
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No pending escrow found."))
            return

        if not options.get("no_input"):
            confirm = input(f"Reset {count} pending escrow(s) to 'failed'? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write("Aborted.")
                return

        for e in qs:
            self.stdout.write(f"  {e.contract.project.title} (project={e.contract.project_id})")
        qs.update(status="failed")
        self.stdout.write(self.style.SUCCESS(f"Reset {count} escrow(s) to 'failed'. You can retry deposit in the app."))
