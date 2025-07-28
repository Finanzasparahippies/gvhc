from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_order_notification_email(vendor_email, subject, message):
    send_mail(
        subject,
        message,
        'noreply@yourdomain.com',
        [vendor_email],
        fail_silently=False,
    )
    print(f"Email sent to {vendor_email} with subject: {subject}")