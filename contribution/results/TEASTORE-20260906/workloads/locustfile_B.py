import random
from locust import HttpUser, TaskSet, task, between
P="/tools.descartes.teastore.webui"
def login(l):
    l.client.get(P+"/", name="/")
    l.client.post(P+"/loginAction", data={"username":"user"+str(random.randint(1,90)),"password":"password"}, name="/loginAction")
def browse(l):
    cat=random.randint(2,6); l.client.get(P+"/category?category=%d&page=1"%cat, name="/category")
    pid=random.randint(1,100); l.client.get(P+"/product?id=%d"%pid, name="/product")
    l.client.post(P+"/cartAction", data={"addToCart":"","productid":str(pid)}, name="/cartAction-add")

class BuyTasks(TaskSet):
    def on_start(self): login(self)
    @task(5)
    def t(self): browse(self)
    @task(4)
    def buy(self):
        browse(self)
        self.client.get(P+"/order", name="/order")
        self.client.post(P+"/cartAction", data={"firstname":"U","lastname":"U","address1":"R","address2":"C","cardtype":"visa","cardnumber":"314159265359","expirydate":"12/2050","confirm":"Confirm"}, name="/confirm")
class JourneyBUser(HttpUser):
    tasks=[BuyTasks]; wait_time=between(1,3)
