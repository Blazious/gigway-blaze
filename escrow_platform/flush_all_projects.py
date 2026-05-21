#!/usr/bin/env python
"""
Flush All Projects Script
Deletes all projects and related data (proposals, contracts, escrows, deliverables, disputes)
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.models import Project, Proposal, Contract, Escrow, Deliverable, Dispute

def flush_all_projects():
    """Delete all projects and related data"""
    print("\n" + "="*60)
    print("FLUSHING ALL PROJECTS")
    print("="*60 + "\n")
    
    # Count before deletion
    project_count = Project.objects.count()
    proposal_count = Proposal.objects.count()
    contract_count = Contract.objects.count()
    escrow_count = Escrow.objects.count()
    deliverable_count = Deliverable.objects.count()
    dispute_count = Dispute.objects.count()
    
    print(f"Found:")
    print(f"  Projects: {project_count}")
    print(f"  Proposals: {proposal_count}")
    print(f"  Contracts: {contract_count}")
    print(f"  Escrow Transactions: {escrow_count}")
    print(f"  Deliverables: {deliverable_count}")
    print(f"  Disputes: {dispute_count}\n")
    
    if project_count == 0:
        print("[OK] No projects to delete. Database is already clean.")
        return
    
    # Confirm deletion
    confirm = input("Are you sure you want to delete ALL projects? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("[CANCELLED] Deletion cancelled.")
        return
    
    print("\nDeleting...")
    
    # Delete in order (respecting foreign key constraints)
    # Disputes first (they reference projects)
    disputes_deleted = Dispute.objects.all().delete()[0]
    print(f"[OK] Deleted {disputes_deleted} disputes")
    
    # Deliverables
    deliverables_deleted = Deliverable.objects.all().delete()[0]
    print(f"[OK] Deleted {deliverables_deleted} deliverables")
    
    # Escrow transactions
    escrows_deleted = Escrow.objects.all().delete()[0]
    print(f"[OK] Deleted {escrows_deleted} escrow transactions")
    
    # Contracts
    contracts_deleted = Contract.objects.all().delete()[0]
    print(f"[OK] Deleted {contracts_deleted} contracts")
    
    # Proposals
    proposals_deleted = Proposal.objects.all().delete()[0]
    print(f"[OK] Deleted {proposals_deleted} proposals")
    
    # Projects (this will cascade delete related data)
    projects_deleted = Project.objects.all().delete()[0]
    print(f"[OK] Deleted {projects_deleted} projects")
    
    print("\n" + "="*60)
    print("[SUCCESS] All projects and related data have been deleted!")
    print("="*60 + "\n")
    
    # Verify
    remaining = Project.objects.count()
    if remaining == 0:
        print("[OK] Verification: No projects remaining in database.")
    else:
        print(f"[WARNING] {remaining} projects still exist!")

if __name__ == '__main__':
    flush_all_projects()
