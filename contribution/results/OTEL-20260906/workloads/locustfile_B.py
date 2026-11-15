import random, uuid
from locust import HttpUser, TaskSet, task, between
products = ["0PUK6V6EV0","1YMWWN1N4O","2ZYFJ3GM2N","66VCHSJNUP","6E92ZMYYFZ","9SIQT8TOJO","L9ECAV7KIM","LS4PSXUNUM","OLJCESPC7Z","HQTGWGPNH4"]
people = [{"userId":"x","email":"a@b.co","address":{"streetAddress":"1","city":"c","state":"s","country":"US","zipCode":"1"},"userCurrency":"USD","creditCard":{"creditCardNumber":"4432801561520454","creditCardCvv":672,"creditCardExpirationYear":2030,"creditCardExpirationMonth":1}}]

def browse(l):
    l.client.get("/")
    l.client.get("/api/products/"+random.choice(products))
    l.client.get("/api/recommendations", params={"productIds":[random.choice(products)]})
    l.client.get("/api/data/", params={"contextKeys":[random.choice(products)]})
    l.client.get("/api/cart")
def add_to_cart(l, user=""):
    if not user: user=str(uuid.uuid1())
    p=random.choice(products); l.client.get("/api/products/"+p)
    l.client.post("/api/cart", json={"item":{"productId":p,"quantity":random.choice([1,2,3])},"userId":user})
    return user

class CheckoutTasks(TaskSet):
    @task(3)
    def t_browse(self): browse(self)
    @task(6)
    def t_checkout(self):
        user=add_to_cart(self)
        person=dict(random.choice(people)); person["userId"]=user
        self.client.post("/api/checkout", json=person)
class JourneyBUser(HttpUser):
    tasks=[CheckoutTasks]; wait_time=between(1,3)
