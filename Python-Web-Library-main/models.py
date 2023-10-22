class User:
    def __init__(self,id,email,username):
        self.id = id
        self.email = email
        self.username = username
    def set_data(self,id,email,username):
        self.id = id
        self.email = email
        self.username = username
    def get_id(self):
        a = int(str(self.id).replace("[(", "").replace(",)]", ""))
        return a
    
class Book:
    def __init__(self,id,serial,name,owner,link,date,lastdate,stock,text,writer,category,page_count):
        self.id = id
        self.serial = serial
        self.name = name
        self.owner = owner
        self.link = link
        self.date = date
        self.lastdate = lastdate
        self.stock = stock
        self.text = text
        self.writer = writer
        self.category = category
        self.page_count = page_count
    def set_data(self,id,serial,name,owner,link,date,lastdate,stock,text,writer,category,page_count):
        self.id = id
        self.serial = serial
        self.name = name
        self.owner = owner
        self.link = link
        self.date = date
        self.lastdate = lastdate
        self.stock = stock
        self.text = text
        self.writer = writer
        self.category = category
        self.page_count = page_count