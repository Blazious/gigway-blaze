from django.contrib import admin
from core.models import CustomUser, Project, Contract, Escrow, Deliverable, Dispute, Proposal, Notification, NotificationPreference

admin.site.register(CustomUser)
admin.site.register(Project)
admin.site.register(Contract)
admin.site.register(Escrow)
admin.site.register(Deliverable)
admin.site.register(Dispute)
admin.site.register(Proposal)
admin.site.register(Notification)
admin.site.register(NotificationPreference)
