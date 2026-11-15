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

class BrowseTasks(TaskSet):
    def on_start(self): login(self)
    @task(8)
    def t(self): browse(self)
    @task(1)
    def prof(self): self.client.get(P+"/profile", name="/profile")
class JourneyAUser(HttpUser):
    tasks=[BrowseTasks]; wait_time=between(1,3)
