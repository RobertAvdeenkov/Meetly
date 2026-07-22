class TaskService:
    def __init__(self,repo):
        self.repo=repo

    def check_add_user(self, name,password):
        if not name or not password:
            raise ValueError('Not all')
        self.repo.add_user(name,password)

    def check_add_event(self,name, type, user_id, desc, end_at,place, tags):
        if not name or not type or not user_id or not desc or not end_at or not place or not tags:
            raise ValueError('Not all')
        self.repo.add_event(name=name, type=type,desc=desc, end_at=end_at, place=place, user_id=user_id, tags=tags)

    def check_delete_event(self,name, user_id):
        if not name or not user_id:
            raise ValueError('not all')
        self.repo.delete_event(name,user_id)

    def check_add_player(self,name, event_id):
        if not name or not event_id:
            raise ValueError('not all')
        self.repo.add_player(name,event_id)

    def check_delete_player(self,name, event_id):
        if not name or not event_id:
            raise ValueError('not all')
        self.repo.delete_player(name,event_id)
