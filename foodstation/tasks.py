from celery import shared_task
# from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

# @shared_task
# def send_order_notification_email(vendor_email, subject, message):
#     try:
#         send_mail(
#             subject,
#             message,
#             'noreply@yourdomain.com',
#             [vendor_email],
#             fail_silently=False,
#         )
#         logger.info(f"Email sent to {vendor_email} with subject: {subject}")
#     except Exception as e:
#         logger.exception(f"Error sending email to {vendor_email}:")