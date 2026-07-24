from models import User as User,Event
import bcrypt

class TasksRepositry:
    def __init__(self,db):
        self.db=db

    def add_user(self, name,password):
        salt=bcrypt.gensalt()
        hashed=bcrypt.hashpw(password=password.encode(encoding='utf-8'), salt=salt)
        hashed=hashed.decode('utf-8')
        target=User(name=name, password=hashed)
        self.db.add(target)
        self.db.commit()
        return target

    def add_event(self,name, type, desc, end_at, place, user_id, tags=''):
        user=self.db.query(User).filter(User.id==user_id).first()
        target=Event(name=name, type=type, place=place, end_at=end_at,desc=desc, creator_id=user_id, tags=tags)
        self.db.add(target)
        self.db.commit()
        return target

    def delete_event(self,name, user_id):
        target=self.db.query(Event).filter(Event.name==name, Event.creator_id==user_id).first()
        self.db.delete(target)
        self.db.commit()
        return target

    def add_player(self,name, event_id):
        target=self.db.query(User).filter(User.name==name).first()
        event=self.db.query(Event).filter(Event.id==event_id).first()
        event.users.append(target)
        self.db.commit()
        return target

    def delete_player(self,name, event_id):
        target=self.db.query(User).filter(User.name==name).first()
        event=self.db.query(Event).filter(Event.id==event_id).first()
        if target in event.users:
            event.users.remove(target)
            self.db.commit()
            return target
    
    def check_user(self,name):
        user=self.db.query(User).filter(User.name==name).first()
        if not(user is None):return True
        else: return False

    def get_events(self,user):
        users=self.db.query(User).filter(User.name==user).first()
        return User.events