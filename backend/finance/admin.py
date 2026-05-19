from django.contrib import admin

from .models import AccountPayable, AccountReceivable, AccountReceivableLine


class AccountReceivableLineInline(admin.TabularInline):
    model = AccountReceivableLine
    extra = 0
    raw_id_fields = ("product",)


@admin.register(AccountPayable)
class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "due_date", "status", "paid_at", "supplier")
    list_filter = ("status", "due_date")
    search_fields = ("description", "notes")
    raw_id_fields = ("supplier", "created_by")
    date_hierarchy = "due_date"


@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "issue_date",
        "amount",
        "due_date",
        "status",
        "received_at",
        "customer",
    )
    list_filter = ("status", "due_date")
    search_fields = ("description", "notes")
    raw_id_fields = ("customer", "created_by")
    date_hierarchy = "due_date"
    inlines = [AccountReceivableLineInline]
