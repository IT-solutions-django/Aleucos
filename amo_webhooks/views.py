from django.http import HttpResponse, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from loguru import logger

from Aleucos.crm import crm
from Aleucos import settings
from orders.models import Order, OrderStatus
from users.models import User


@require_POST
@csrf_exempt
def status_lead_view(request):
    data: QueryDict = request.POST

    lead_id = data['leads[status][0][id]']
    lead = crm.get_lead_by_id(lead_id)

    try:
        order: Order = Order.objects.get(number=lead.name)

        if lead.status.name == settings.LEAD_STATUS_LAST: 
            for order_item in order.items.all(): 
                order_item.product.is_frozen = False 
                order_item.product.save()
    except Order.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: заказа с номером {lead.name} нет в базе данных')

    new_status_name = settings.ORDER_STATUS_NAME_CONVERTER.get(lead.status.name)
    new_status, created = OrderStatus.objects.get_or_create(title=new_status_name)

    if created: 
        logger.info(f'Был создан новый статус заказа: {new_status_name}')

    order.status = new_status
    order.save()
    logger.info(f'У заказа {order.number} новый статус: {order.status}')

    return HttpResponse("ОК", content_type="text/plain")


@require_POST
@csrf_exempt
def responsible_lead_view(request):
    data: QueryDict = request.POST
    lead_id = data['leads[responsible][0][id]']
    responsible_user_id = data['leads[responsible][0][responsible_user_id]']

    lead = crm.get_lead_by_id(lead_id)
    responsible_user = crm.get_user_by_id(responsible_user_id)

    try:
        order = Order.objects.get(number=lead.name)
        new_manager = User.objects.get(email=responsible_user.email)
    except Order.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: заказа с номером {lead.name} нет в базе данных')
    except User.DoesNotExist: 
        logger.error(f'Ошибка при обновлении статуса заказа: менеджера с email {responsible_user.email} нет в базе данных')

    order.manager = new_manager
    order.save()
    logger.info(f'У заказа {order.number} новый менеджер: {new_manager.email}')

    return HttpResponse("ОК", content_type="text/plain")



   