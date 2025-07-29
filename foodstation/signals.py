#signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from .tasks import send_order_notification_email
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def notify_vendor_on_order(sender, instance, created, **kwargs):
    if created and not instance.sent_to_vendor:
        subject = f"Nuevo pedido: {instance.dish.name}"
        message = (
            f"Pedido:\n\n"
            f"Usuario: {instance.user.username}\n"
            f"Platillo: {instance.dish.name}\n"
            f"Cantidad: {instance.quantity}\n"
            f"Notas: {instance.notes or 'Ninguna'}\n"
            f"Fecha: {instance.created_at}\n"
        )
        
        send_order_notification_email.delay(
            instance.dish.vendor.contact_email,
            subject,
            message
        )

        instance.sent_to_vendor = True
        instance.save(update_fields=['sent_to_vendor']) # Only update this field for efficiency
        
        logger.info(f"Celery task enqueued for vendor notification: {instance.dish.vendor.name} about order from {instance.user.username}.")