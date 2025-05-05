import base64
import json
from io import BytesIO
from uuid import uuid4

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.db.models import Q, Prefetch
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponseServerError, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.authtoken.models import Token

from .forms import UserRegisterForm, UserLoginForm
from .models import *
from .models import Product, ShopperDesign, DesignElement


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'auth/change_password.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')

            # Аутентификация по email
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('home')
            else:
                messages.error(request, 'Ошибка при аутентификации')
    else:
        form = UserRegisterForm()
    return render(request, 'auth/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # Получаем email
            password = form.cleaned_data.get('password')

            # Аутентификация по email
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                token, _ = Token.objects.get_or_create(user=user)
                messages.success(request, f'Добро пожаловать, {email}!')
                return redirect('home')
            else:
                messages.error(request, 'Неверные учетные данные')
    else:
        form = UserLoginForm()
    return render(request, 'auth/login.html', {'form': form})

def customize_shopper(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'shop/customize_shopper.html', {'product': product})

@csrf_exempt
def save_design(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user
        product_id = data.get('product_id')
        front = data.get('front_design')
        back = data.get('back_design')

        product = get_object_or_404(Product, pk=product_id)

        ShopperDesign.objects.create(
            user=user,
            product=product,
            front_design=front,
            back_design=back
        )

        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('material', 'color', 'size')
        .prefetch_related('images'),
        pk=product_id
    )

    in_cart = 0
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(
            cart__user=request.user,
            product=product
        ).first()
        if cart_item:
            in_cart = cart_item.quantity

    context = {
        'product': product,
        'in_cart': in_cart
    }
    return render(request, 'product_detail.html', context)

def product_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-created_at')

    products = Product.objects.select_related(
        'material', 'color', 'size'
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.filter(is_additional=False),
            to_attr='main_images'
        )
    ).all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(material__name__icontains=query)
        ).distinct()

    sort_options = {
        'price': 'price',
        '-price': '-price',
        'name': 'name',
        '-created_at': '-created_at',
        'created_at': 'created_at'
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        cart_total = sum(item.quantity for item in cart_items)

        in_cart_map = {item.product_id: item.quantity for item in cart_items}

        for product in products:
            product.in_cart = in_cart_map.get(product.id, 0)
    else:
        cart = request.session.get('cart', {})
        cart_total = sum(item['quantity'] for item in cart.values())

        for product in products:
            product.in_cart = cart.get(str(product.id), {}).get('quantity', 0)

    context = {
        'products': products,
        'query': query,
        'sort': sort,
        'sort_options': sort_options,
        'cart_total': cart_total
    }
    return render(request, 'products.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"Сообщение от {name} <{email}>:\n\n{message}"

        try:
            send_mail(
                subject=subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Указываем строго MAIL.RU
                recipient_list=['mr.poremskiy@mail.ru'],
                fail_silently=False,
            )
            messages.success(request, 'Ваше сообщение отправлено!')
        except Exception as e:
            messages.error(request, f'Ошибка отправки: {e}')

        return redirect('contact')

    return render(request, 'contact.html')


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).select_related('user').prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('product'))
    ).order_by('-created_at')

    return render(request, 'profile.html', {
        'orders': orders
    })


@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        new_email = request.POST.get('email')
        new_username = request.POST.get('username')

        if new_email != user.email and User.objects.filter(email=new_email).exists():
            messages.error(request, 'Этот email уже используется другим пользователем')
            return redirect('profile')

        if new_username != user.username and User.objects.filter(username=new_username).exists():
            messages.error(request, 'Это имя пользователя уже занято')
            return redirect('profile')

        user.username = new_username
        user.email = new_email
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.save()

        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')

    return redirect('profile')


def view_cart(request):
    products_in_cart = []
    total_price = 0

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')

        for item in cart_items:
            products_in_cart.append({
                'product': item.product,
                'quantity': item.quantity,
                'total': item.quantity * float(item.product.price)
            })
            total_price += item.quantity * float(item.product.price)
    else:
        cart = request.session.get('cart', {})
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            products_in_cart.append({
                'product': product,
                'quantity': item['quantity'],
                'total': float(item['price']) * item['quantity']
            })
            total_price += float(item['price']) * item['quantity']

    context = {
        'cart_items': products_in_cart,
        'total_price': total_price
    }
    return render(request, 'cart.html', context)



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.price}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
    else:
        cart = request.session.get('cart', {})
        cart_item = cart.get(str(product_id), {'quantity': 0, 'price': str(product.price)})
        cart_item['quantity'] += quantity
        cart[str(product_id)] = cart_item
        request.session['cart'] = cart

    messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    return redirect('product_list')

def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        CartItem.objects.filter(cart=cart, product=product).delete()
        messages.success(request, 'Товар удален из корзины')
    else:
        pass

    return redirect('view_cart')


def home(request):
    example_products = Product.objects.order_by('-created_at')[:4]

    return render(request, 'home.html', {
        'example_products': example_products
    })


def update_cart_item(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.price}
        )

        if not created:
            cart_item.quantity = quantity
            cart_item.save()

        messages.success(request, 'Корзина обновлена')
    else:
        pass

    return redirect('view_cart')


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Для оформления заказа войдите в систему')
        return redirect('login')

    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product').all()

    if not cart_items:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('view_cart')

    total_price = sum(item.total_price() for item in cart_items)

    if request.method == 'POST':
        try:
            # Создаем заказ (номер сгенерируется автоматически)
            order = Order.objects.create(
                user=request.user,
                total_amount=total_price,
                delivery_address=request.POST.get('delivery_address', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                status='created'
            )

            # Переносим товары из корзины в заказ
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    quantity=item.quantity,
                    price=item.price
                )

            # Очищаем корзину
            cart.items.all().delete()

            messages.success(request, f'Заказ #{order.order_number} успешно оформлен!')
            return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
            return redirect('checkout')

    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'checkout.html', context)

@login_required
def design_editor(request, product_id, design_id=None):
    """Основной редактор дизайна"""
    product = get_object_or_404(Product, id=product_id)

    if design_id:
        design = get_object_or_404(ShopperDesign, id=design_id, user=request.user, product=product)
        elements = design.elements.all().order_by('z_index')
    else:
        design = None
        elements = []

    return render(request, 'design_editor.html', {
        'product': product,
        'design': design,
        'elements': elements,
        'media_url': settings.MEDIA_URL,
    })


@login_required
def save_design(request, product_id):
    """Сохранение дизайна"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            product = get_object_or_404(Product, id=product_id)

            # Создаем или обновляем дизайн
            if data.get('design_id'):
                design = get_object_or_404(
                    ShopperDesign,
                    id=data['design_id'],
                    user=request.user,
                    product=product
                )
                design.name = data.get('name', design.name)
                design.printing_method = data.get('printing_method', design.printing_method)
                design.printing_side = data.get('printing_side', design.printing_side)
                design.canvas_width = data.get('canvas_width', design.canvas_width)
                design.canvas_height = data.get('canvas_height', design.canvas_height)
                design.save()
            else:
                design = ShopperDesign.objects.create(
                    user=request.user,
                    product=product,
                    name=data.get('name', 'Новый дизайн'),
                    printing_method=data.get('printing_method', 'silk'),
                    printing_side=data.get('printing_side', 'front'),
                    canvas_width=data.get('canvas_width', 230),  # Ширина по умолчанию для шелкографии
                    canvas_height=data.get('canvas_height', 300)  # Высота по умолчанию
                )

            # Сохраняем элементы дизайна
            design.elements.all().delete()
            for element in data.get('elements', []):
                DesignElement.objects.create(
                    design=design,
                    element_type=element.get('type'),
                    side=element.get('side', 'front'),
                    content=element.get('content', ''),
                    x_position=element.get('x', 0),
                    y_position=element.get('y', 0),
                    width=element.get('width'),
                    height=element.get('height'),
                    rotation=element.get('rotation', 0),
                    color=element.get('color', '#000000'),
                    font_family=element.get('fontFamily', 'Arial'),
                    font_size=element.get('fontSize', 16),
                    z_index=element.get('zIndex', 1),
                    opacity=element.get('opacity', 1.0)
                )

            return JsonResponse({
                'status': 'success',
                'design_id': design.id,
                'message': 'Дизайн успешно сохранен'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Недопустимый метод запроса'
    }, status=405)


@csrf_exempt
@login_required
def upload_image(request, product_id):
    """Загрузка изображений на сервер"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']

            # Проверка типа файла
            if not image_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return JsonResponse({'status': 'error', 'message': 'Недопустимый формат файла'}, status=400)

            # Проверка размера файла (макс 5MB)
            if image_file.size > 5 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': 'Файл слишком большой (макс 5MB)'}, status=400)

            # Создаем папку для загрузки
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'design_images', str(request.user.id))
            os.makedirs(upload_dir, exist_ok=True)

            # Генерируем уникальное имя файла
            ext = os.path.splitext(image_file.name)[1].lower()
            filename = f"{uuid4().hex}{ext}"
            filepath = os.path.join(upload_dir, filename)

            # Сохраняем файл
            with open(filepath, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            # Проверяем, что это валидное изображение
            try:
                with Image.open(filepath) as img:
                    img.verify()
            except Exception as e:
                os.remove(filepath)
                return JsonResponse({'status': 'error', 'message': 'Недопустимое изображение'}, status=400)

            # Возвращаем относительный путь
            return JsonResponse({
                'status': 'success',
                'url': os.path.join('design_images', str(request.user.id), filename)
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'}, status=400)


@login_required
def preview_design(request, product_id, design_id):
    """Предпросмотр дизайна"""
    design = get_object_or_404(ShopperDesign, id=design_id, product_id=product_id, user=request.user)
    return render(request, 'preview.html', {
        'design': design,
        'product': design.product,
        'elements': design.elements.all().order_by('z_index'),
        'media_url': settings.MEDIA_URL
    })



def register_fonts():
    try:
        # Попробуем найти стандартные шрифты Windows
        font_paths = [
            "C:/Windows/Fonts/",  # Windows
            "/usr/share/fonts/truetype/msttcorefonts/",  # Linux
            "/Library/Fonts/",  # MacOS
            "/System/Library/Fonts/",
        ]

        # Маппинг названий шрифтов к файлам
        font_files = {
            'Arial': ['Arial.ttf', 'arial.ttf'],
            'TimesNewRoman': ['Times New Roman.ttf', 'Times_New_Roman.ttf', 'times.ttf'],
            'CourierNew': ['Courier New.ttf', 'Courier_New.ttf', 'cour.ttf']
        }

        registered = False

        for font_path in font_paths:
            if os.path.exists(font_path):
                for font_name, files in font_files.items():
                    for file in files:
                        full_path = os.path.join(font_path, file)
                        if os.path.exists(full_path):
                            try:
                                pdfmetrics.registerFont(TTFont(font_name, full_path))
                                registered = True
                                break
                            except:
                                continue

        if not registered:
            # Используем стандартные PDF-шрифты как fallback
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
            pdfmetrics.registerFont(TTFont('CourierNew', 'cour.ttf'))

    except Exception as e:
        print(f"Font registration error: {str(e)}")


register_fonts()

@login_required
def generate_pdf(request, product_id, design_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            front_data = data.get('front', {})
            back_data = data.get('back', {})
            printing_method = data.get('printingMethod', 'silk')
            page_size = data.get('pageSize', {'width': 21 * cm, 'height': 29.7 * cm})  # A4 по умолчанию

            buffer = BytesIO()

            # Создаем PDF с кастомным размером страницы
            pdf_canvas = canvas.Canvas(
                buffer,
                pagesize=(page_size['width'], page_size['height'])
            )

            # Масштабируем элементы для точного соответствия 1:1
            scale = 1.0  # Можете настроить при необходимости

            # Отрисовываем переднюю сторону
            _render_canvas(pdf_canvas, front_data, printing_method, scale)

            # Если нужно добавить обратную сторону
            if back_data.get('elements'):
                pdf_canvas.showPage()
                _render_canvas(pdf_canvas, back_data, printing_method, scale)

            pdf_canvas.save()

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="design_{design_id}.pdf"'
            return response

        except Exception as e:
            return HttpResponseServerError(json.dumps({
                'status': 'error',
                'message': f"Error generating PDF: {str(e)}"
            }), content_type='application/json')

    return HttpResponseNotAllowed(['POST'])


def _render_canvas(pdf_canvas, canvas_data, printing_method, scale=1.0):
    try:
        # Сначала рисуем рамку и метки размеров на отдельном слое
        pdf_canvas.saveState()
        pdf_canvas.setStrokeColorRGB(0, 0, 0)
        pdf_canvas.setLineWidth(1)

        # Рисуем основную рамку
        pdf_canvas.rect(
            0, 0,
            canvas_data['width'],
            canvas_data['height'],
            stroke=1, fill=0
        )

        # Добавляем текст с размерами
        pdf_canvas.setFont("Helvetica", 8)
        pdf_canvas.drawString(
            10, 10,
            f"Size: {canvas_data['width']}x{canvas_data['height']} cm | Method: {printing_method}"
        )
        pdf_canvas.restoreState()

        # Сортируем элементы по zIndex (от нижнего к верхнему)
        elements = sorted(canvas_data.get('elements', []), key=lambda x: x['zIndex'])

        # Маппинг шрифтов
        font_mapping = {
            'Arial': 'Helvetica',
            'Times New Roman': 'Times-Roman',
            'Courier New': 'Courier'
        }

        for element in elements:
            pdf_canvas.saveState()

            # Применяем трансформации
            # Note: координаты в PDF начинаются снизу, поэтому инвертируем Y
            x = element['x']
            y = canvas_data['height'] - element['y'] - element.get('height', 0)

            pdf_canvas.translate(x, y)

            if element.get('rotation', 0):
                pdf_canvas.rotate(element['rotation'])

            if element['type'] == 'text':
                # Обработка текста
                font_name = font_mapping.get(element.get('fontFamily', 'Arial'), 'Helvetica')
                try:
                    pdf_canvas.setFont(font_name, element['fontSize'])
                except:
                    pdf_canvas.setFont('Helvetica', element['fontSize'])  # Fallback

                try:
                    pdf_canvas.setFillColor(HexColor(element.get('color', '#000000')))
                except:
                    pdf_canvas.setFillColor(HexColor('#000000'))  # Fallback to black

                if 'opacity' in element:
                    pdf_canvas.setFillAlpha(element['opacity'])

                pdf_canvas.drawString(0, 0, element['content'])

            elif element['type'] == 'image':
                # Обработка изображения
                try:
                    if element['content'].startswith('data:'):
                        # Base64 изображение
                        header, encoded = element['content'].split(',', 1)
                        image_data = base64.b64decode(encoded)
                        img = ImageReader(BytesIO(image_data))
                    else:
                        # URL изображения
                        img = ImageReader(element['content'])

                    width = element.get('width', 100)
                    height = element.get('height', 100)

                    if 'opacity' in element:
                        pdf_canvas.setFillAlpha(element['opacity'])

                    pdf_canvas.drawImage(
                        img,
                        0, 0,
                        width=width,
                        height=height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception as img_e:
                    print(f"Error rendering image: {str(img_e)}")
                    # Рисуем placeholder
                    pdf_canvas.setFillColor(HexColor('#CCCCCC'))
                    pdf_canvas.rect(0, 0,
                                    element.get('width', 100),
                                    element.get('height', 100),
                                    fill=1, stroke=0)
                    pdf_canvas.setFillColor(HexColor('#999999'))
                    pdf_canvas.drawString(10, 10, "Image")

            pdf_canvas.restoreState()

    except Exception as e:
        print(f"Error rendering canvas: {str(e)}")
        raise e