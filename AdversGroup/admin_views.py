from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count

from .models import Order, User


import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import localtime

@staff_member_required
def statistics_view(request):
    orders = (
        Order.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    users = (
        User.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    def serialize(data):
        return [
            {
                "month": localtime(item['month']).strftime('%Y-%m'),
                "count": item['count']
            } for item in data
        ]

    context = dict(
        title='Статистика',
        orders_data=json.dumps(serialize(orders), cls=DjangoJSONEncoder),
        users_data=json.dumps(serialize(users), cls=DjangoJSONEncoder),
    )
    return TemplateResponse(request, 'admin/statistics.html', context)



