from Aleucos.celery import app
# from .services import NotificationService

# @app.task(bind=True, max_retries=3)
# def send_new_answer_notification_task(self, recipient_user_id: int, question_id: int) -> None: 
#     try:
#         NotificationService.send_new_answer_notification(recipient_user_id, question_id)
#     except SMTPException as ex: 
#         raise self.retry(exc=ex, countdown=5) 