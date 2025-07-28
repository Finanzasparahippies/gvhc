from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from .tasks import send_order_notification_email

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
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.dish.vendor.contact_email]
        )
        instance.sent_to_vendor = True
        instance.save()
        print(f"Notificación enviada al vendedor: {instance.dish.vendor.name} sobre el pedido de {instance.user.username}.") 
        
        send_order_notification_email.delay(
            instance.dish.vendor.contact_email,
            subject,
            message
        )