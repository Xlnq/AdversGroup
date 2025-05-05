from locust import HttpUser, task, between
from bs4 import BeautifulSoup

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # пауза между действиями

    def on_start(self):
        self.login()

    def login(self):
        # Получим CSRF токен со страницы locustлогина
        response = self.client.get("/login/")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        # Данные пользователя (заранее зарегистрируй пользователя с такими данными)
        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "username": "mr.poremskiy@mail.ru",  # email
            "password": "Max2200221",      # пароль
        }

        headers = {"Referer": self.client.base_url + "/login/"}

        self.client.post("/login/", data=payload, headers=headers)

    @task(2)
    def view_products(self):
        self.client.get("/products/")

    @task(1)
    def view_product_detail(self):
        self.client.get("/products/6/")  # Заменить на существующий product_id

    @task(1)
    def add_to_cart(self):
        self.client.post("/add-to-cart/6/")  # Заменить на существующий product_id

    @task(1)
    def view_cart(self):
        self.client.get("/cart/")
