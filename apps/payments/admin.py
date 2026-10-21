from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "booking", "amount", "currency", "status", "created_at"]
    list_filter = ["status", "currency"]
    search_fields = ["booking__guest__email", "stripe_checkout_session_id", "stripe_payment_intent_id"]
    raw_id_fields = ["booking"]
    # Payment state is owned by Stripe webhooks; don't let admins edit it by hand.
    readonly_fields = [f.name for f in Payment._meta.fields]
