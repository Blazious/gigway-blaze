"""
Delete all projects and related data (proposals, deliverables, disputes, escrow, contracts).
Keeps users so you can run E2E: client creates project -> freelancer proposes -> accept -> deposit -> etc.
"""
from django.core.management.base import BaseCommand
from core.models import Project


class Command(BaseCommand):
    help = "Delete all projects and related data (proposals, deliverables, disputes, escrow, contracts). Keeps users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        count = Project.objects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No projects to delete. Database is already clean."))
            return

        if not options["no_input"]:
            confirm = input(f"Delete all {count} project(s) and related data? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write("Aborted.")
                return

        # CASCADE on Project deletes: Proposal, Deliverable, Dispute, Escrow, Contract
        deleted = Project.objects.all().delete()
        total = deleted[0] if isinstance(deleted, tuple) else deleted
        self.stdout.write(self.style.SUCCESS(f"Flushed {total} record(s). Projects and related data removed. Users kept."))
