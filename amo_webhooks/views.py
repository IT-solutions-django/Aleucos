from django.http import HttpResponse, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from loguru import logger
from Aleucos.crm import crm
from Aleucos import settings
from orders.models import Order, OrderStatus
from users.models import User
from configs.models import Config
from users.tasks import send_email_when_new_status_task


@require_POST
@csrf_exempt
def status_lead_view(request):
    data: QueryDict = request.POST

    lead_id = data['leads[status][0][id]']
    lead_name, new_status = crm.get_lead_and_status(lead_id)

    try:
        order: Order = Order.objects.get(id_in_amocrm=lead_id)
    except Order.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: заказа с amoCRM ID {lead_id} нет в базе данных')
        return HttpResponse("ОК", content_type="text/plain")

    new_status_name = Config.get_instance().order_status_name_mapper.get(new_status)
    new_status, created = OrderStatus.objects.get_or_create(title=new_status_name)
    if created: 
        logger.info(f'Был создан новый статус заказа: {new_status_name}')

    order.status = new_status
    order.save()
    if order.user:
        send_email_when_new_status_task.delay(
            email=order.user.email, 
            order_number=order.number, 
            new_status=new_status
        )
    logger.info(f'У заказа {order.number} новый статус: {order.status}')

    return HttpResponse("ОК", content_type="text/plain")


@require_POST
@csrf_exempt
def responsible_lead_view(request):
    data: QueryDict = request.POST
    lead_id = data['leads[responsible][0][id]']
    responsible_user_id = data['leads[responsible][0][responsible_user_id]']

    responsible_user_email = crm.get_user_email(responsible_user_id)

    try:
        order = Order.objects.get(id_in_amocrm=lead_id)
        new_manager = User.objects.get(email=responsible_user_email)
    except Order.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: заказа с номером {lead_id} нет в базе данных')
        return HttpResponse("ОК", content_type="text/plain")
    except User.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: менеджера с email {responsible_user_email} нет в базе данных')
        return HttpResponse("ОК", content_type="text/plain")

    order.manager = new_manager
    order.save()
    logger.info(f'У заказа {order.number} новый менеджер: {new_manager.email}')

    return HttpResponse("ОК", content_type="text/plain")



   