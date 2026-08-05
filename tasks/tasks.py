from fastapi import Depends,Query, Body,Path, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.routing import APIRouter
from auth import create_token,get_user, get_by_token
from sqlalchemy.orm import Session
from database import get_db
from taskrepo import TasksRepositry
from taskservice import TaskService
from models import User, Event,AutLog,Message,Likes
from fastapi import HTTPException
from fastapi import Form
from jose import jwt
from config import SECRET,ALGORITHM
from audit import log_action
import bcrypt
import time

router=APIRouter()

@router.get('/')
def root(request:Request):
    return FileResponse('templates/reglog.html')

@router.post('/reglog')
def reglog(data=Body(), db:Session=Depends(get_db)):
        repo=TasksRepositry(db)
        service=TaskService(repo)
        user=db.query(User).filter(User.name==data['name']).first()
        if user:
            print(user.password, type(user.password))

        if user is None:
            service.check_add_user(data['name'], data['password'])
            user=db.query(User).filter(User.name==data['name']).first()
            if user:
                log_action(user_id=user.id, entity='user', details='Создание аккаунта')
        elif not(bcrypt.checkpw(password=data['password'].encode('utf-8'), hashed_password=user.password.encode('utf-8'))):
            raise HTTPException(401)
        token=create_token(user.name)
        return {'status':'ok', 'redirect_url':f'/account?token={token}'}


@router.get('/account')
def account(token:str=Query(...)):
    return FileResponse('templates/mainpage.html')

@router.post('/add')
def add(name: str = Form(...),date: str = Form(...),place: str = Form(...),type: str = Form(...),desc: str = Form(...),token: str = Query(...), tags:str=Form(...),db: Session = Depends(get_db)):
    data=get_by_token(token)
    user=db.query(User).filter(User.name==data).first()
    repo=TasksRepositry(db)
    service=TaskService(repo)
    print(tags, desc)
    if user:
        service.check_add_event(name=name, type=type, user_id=user.id, desc=desc, place=place, end_at=date, tags=tags)
        log_action(user_id=user.id, entity='event', details=f'Добавление мероприятия {name}')
    return {'message':'success'}

@router.post('/deletemenuRED')
def deletemenuRED(token=Body()):
    n=token['token']
    data=get_by_token(n)
    return {'status':'ok', 'redirect_url':f'/deletemenu?token={n}'}


@router.get('/deletemenu')
def deletemenu(token:str=Query(...)):
    data=get_by_token(token)
    return FileResponse('templates/deletemenu.html')
    
@router.post('/rename')
def rename(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        user=db.query(User).filter(User.name==data).first()
        target=db.query(Event).filter(Event.name==token['current'], Event.creator_id==user.id).first()
        old=target.name
        target.name=token['new']
        db.commit()
        log_action(user_id=user.id, entity='event', details=f'Переименование мероприятия {old} на {target.name}')
    
@router.post('/deleteevent')
def deleteEvent(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        user=db.query(User).filter(User.name==data).first()
        service.check_delete_event(user_id=user.id, name=token['deletename'])
        log_action(user_id=user.id, entity='event', details=f'Удаление мероприятия {token['deletename']}')

@router.post('/addplayer')
def addplayer(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        user=db.query(User).filter(User.name==data).first()
        event=db.query(Event).filter(Event.name==token['eventname']).first()
        if event is None:
            raise HTTPException(401, 'Такого мероприятия нету')
        service.check_add_player(name=data, event_id=event.id)
        log_action(user_id=user.id, entity='player', details=f'Запись в {event.name}')

@router.post('/deletePLAYER')
def deleteplayer(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        print('checking')
        user=db.query(User).filter(User.name==data).first()
        event=db.query(Event).filter(Event.name==token['eventname'], Event.creator_id==user.id).first()
        if not user or not event:
            raise HTTPException(401)
        service.check_delete_player(name=token['player'], event_id=event.id)
        log_action(user_id=user.id, entity='event', details=f'Удаление участника {token['player']} из {event.name}')

@router.post('/staticRED')
def staticRED(db:Session=Depends(get_db)):
    all_events=db.query(Event.id).count()
    all_users=db.query(User.id).count()
    all_player=db.query(Event.users).count()
    return {'status':'ok', 'redirect_url':f'/static?events={all_events}&users={all_users}&player={all_player}'}

@router.get('/static')
def static(events=Query(...), users=Query(...), player=Query(...)):
    return FileResponse('templates/statistics.html')

@router.post('/infoRED')
def infoRED():
    return {'status':'ok', 'redirect_url':'/info'}

@router.get('/info')
def info():
    return FileResponse('templates/info.html')

@router.post('/listRED')
def listRED(token=Body()):
        n=token['token']
        data=get_by_token(n)
        return {'status':'ok', 'redirect_url':f'/list?token={n}'}

@router.get('/list')
def lists():
    return FileResponse('templates/llist.html')

@router.post('/showlist')
def showlist(db:Session=Depends(get_db), token=Body()):
    
        data=get_by_token(token['token'])
        repo=TasksRepositry(db)
        service=TasksRepositry(repo)
        message=''
        print('started')
        events=db.query(Event).all()
        users=db.query(User).filter(User.name==data).first()
        for i in events:
            if users in i.users:
                message+=str(i.name)+f'(дата окончания:{i.end_at})'+f'Место:{i.place}'+f'<br>Информация: {i.desc}<br>Участники'+'{'+'<br>'
                for j in i.users:
                    message+=''+str(j.name)+','+'<br>'
                message+='}'+'<br><br>'+f'<p></p>'
                message+=f'{i.like_count} лайков'
                message+=f'''<button onclick="like({i.id})">Лайк</button>
                <button onclick="unlike({i.id})">Убрать лайк</button>'''
        print(message)
        return {'status':'ok', 'message':message}
    
@router.post('/topmenuRED')
def topRED(token=Body()):
    
        n=token['token']
        data=get_by_token(n)
        return {'status':'ok', 'redirect_url':f'/topmenu?token={n}'}
    
    
@router.get('/topmenu')
def topmenu():
    return FileResponse('templates/topmenu.html')

@router.post('/topmenuSHOW')
def showtopmenu(db:Session=Depends(get_db), token=Body()):
    try:
        data=get_by_token(token['token'])
        repo=TasksRepositry(db)
        service=TasksRepositry(repo)
        l=db.query(User).filter(User.name==data).first()
        top=''
        already=set()
        for j in l.events:
            count=-1
            for i in l.events:
                if len(i.users)>=count and i.name not in already:
                    count=len(i.users)
                    name=str(i.name)
                
            already.add(name)
            top+=str(i)+'\t'+str(name)+' - '+str(count)+' участника'+'<br>'
        return {'status':'ok', 'message':top}

    except Exception as e:
        print("ERROR:",e)

@router.post('/historyRED')
def historyRED(token=Body()):
        n=token['token']
        data=get_by_token(n)
        return {'status':'ok', 'redirect_url':f'/history?token={n}'}
    
@router.get('/history')
def history():
    return FileResponse('templates/history.html')

@router.post('/historySHOW')
def historySHOW(db:Session=Depends(get_db), token=Body()):
        data=get_by_token(token['token'])
        user=db.query(User).filter(User.name==data).first()
        l=db.query(AutLog).filter(AutLog.user_id==user.id).all()
        txt=''
        for i in l:
            txt+=str(i.info)+str(i.created_at)+'<br>'
        return {'status':'ok', 'message':txt}
    
@router.get('/logs')
def logs(db:Session=Depends(get_db), token=Query(...)):
        data=get_by_token(token)
        user=db.query(User).filter(User.name==data).first()
        l=db.query(AutLog).all()
        if not user:
            raise HTTPException(401)
        if str(user.role)=='user':
            raise HTTPException(401, 'NOT ALLOWED')
        else:
            txt=''
            for i in l:
                txt+=str(i.created_at)+'\t'+str(i.user_id)+'\t'+str(i.info)+'\t'+str(i.entity)
            return Response(content=txt, media_type='text/plain')

    
@router.post('/globalRED')
def globalRED(token=Body()):
        get_by_token(token['token'])
        return {'status':'ok', 'redirect_url':f'/global?token={token['token']}'}

@router.get('/global')
def globall(token=Query(...)):
    return FileResponse('templates/global.html')

@router.post('/globalSHOW')
def globalSHOW(db:Session=Depends(get_db)):
    try:
        repo=TasksRepositry(db)
        service=TasksRepositry(repo)
        l=db.query(Event).all()
        kolvo=0
        if len(l)<11:
            kolvo=len(l)
        else:
            kolvo=11
        top=''
        already=set()
        for j in range(kolvo):
            count=-1
            for i in l:
                if len(i.users)>=count and i.name not in already:
                    count=len(i.users)
                    name=str(i.name)
                    txt=f'<br>Мероприятие:{i.name}\tДата окончания:{i.end_at}\tМесто:{i.place}<br>Кол-во участников:{len(i.users)}<br>Информация: {i.desc}<br>{i.like_count} лайков<br>'
                    txt+=f'''<button onclick="like({i.id})">Лайк</button>
                    <button onclick="unlike({i.id})">Убрать лайк</button>'''
            already.add(name)
            top+=txt
        print(top)
        return {'status':'ok', 'message':top}
    except Exception as e:
        print("ERROR:",e)

@router.post('/searchRED')
def searchRED(token=Body()):
        data=get_by_token(token['token'])
        return {'status':'ok', 'redirect_url':f'/search?token={token['token']}'}
    
@router.get('/search')
def search():
    return FileResponse('templates/search.html')

def check(x,y):
    for i in x:
        if i in y and i!='':
            return True
    return False

@router.post('/searchSHOW')
def searchSHOW(token=Body(), db:Session=Depends(get_db)):
    tags=token['tags'].split('#')
    events=db.query(Event).all()
    txt=''
    for i in events:
        tag=str(i.tags).split('#')
        if check(tag, tags):
            txt+=f'<br>Мероприятие:{i.name}\tДата окончания:{i.end_at}<br>Место:{i.place}\tКол-во участников:{len(i.users)}<br>Информация: {i.desc}<br>{i.like_count} лайков<br><br>'
            txt+=f'''<button onclick="like({i.id})">Лайк</button>
                <button onclick="unlike({i.id})">Убрать лайк</button>'''
    if txt:
        return {'status':'ok', 'message':txt}
    else:
        return {'status':'ok', 'message':'Ничего не найдено!'}

@router.post('/profileRED')
def profileRED(token=Body()):
        data=get_by_token(token['token'])
        return {'status':'ok', 'redirect_url':f'/profiles?token={token['token']}'}

@router.get('/profiles')
def profile():
    return FileResponse('templates/searchmenu.html')

@router.get('/profile')
def profiles():
    return FileResponse('templates/searchRESULT.html')

@router.post('/profileSHOW')
def profileSHOW(db:Session=Depends(get_db), n=Body()):
    try:
        data=jwt.decode(n['token'],SECRET,algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==n['name']).first()
        log=db.query(AutLog).filter(AutLog.user_id==user.id, AutLog.info=='Создание аккаунта').first()
        created=db.query(Event).filter(Event.creator_id==user.id).count()

        if not user or not log:
            raise HTTPException(401, 'Не хватает некоторых данных')
        txt=f'''
        <h1>Данные аккаунта<h1>
        <h3>Отображаемое имя: {user.name}<h3>
        <h4>Аккаунт создан: {str(log.created_at)}<h4>
        <h4>Созданных мероприятий: {str(created)}<h4>
        '''
        return {'status':'ok', 'redicrect_url':f'/profile?user={user.name}&token={n['token']}', 'message':txt}

    except Exception as e:
        print('ERROR:',e)
        raise HTTPException(401, 'Такого пользователя нету!')

@router.post('/writeletter')
def writeletter(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        sendto=db.query(User).filter(User.name==token['user']).first()
        if sendto is None:
            raise HTTPException(401, 'Такого пользователя нету')
        mess=Message(sender_name=data, info=token['info'], to_id=sendto.id)
        db.add(mess)
        db.commit()
        return {'status':'ok', 'message':'yes'}

@router.post('/profileSEARCHING')
def searchingprof(token=Body()):
        data=get_by_token(token['token'])
        return {'status':'ok', 'redirect_url':f'/profile?user={token['name']}&token={token['token']}'}

@router.post('/uvedRED')
def uvedRED(token=Body()):
        data=get_by_token(token['token'])
        return {'status':'ok', 'redirect_url':f'/uved?token={token['token']}'}

@router.get('/uved')
def uved():
    return FileResponse('templates/uved.html')

@router.post('/uvedSHOW')
def uvedSHOW(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        user=db.query(User).filter(User.name==data).first()
        messages=db.query(Message).filter(Message.to_id==user.id).all()
        txt=''
        if not user:
            raise HTTPException(401)
        elif not messages:
            txt='<h2>Уведомлений нет!<h2>'
            return {'status':'ok', 'message':txt}

        for i in messages:
            txt+=f'<br>Отправитель:{i.sender_name}<br>Сообщение:{i.info}<br>Отправлено:{i.created_at}<br><br>'
        return {'status':'ok', 'message':txt}

@router.get('/{path}')
def pat(path):
    if path.endswith('.html'):
        return FileResponse(path)

@router.post('/like')
def like(token=Body(), db:Session=Depends(get_db)):
        print(token)
        data=get_by_token(token['token'])
        user=db.query(User).filter(User.name==data).first()
        target=db.query(Likes).filter(Likes.user_id==user.id, Likes.event_id==token['id']).first()
        targetEVENT=db.query(Event).filter(Event.id==token['id']).first()
        print(target)
        if target:
            raise HTTPException(401, 'Мероприятие уже лайкнуто')
        else:
            target=Likes(user_id=user.id, event_id=token['id'])
            targetEVENT.like_count+=1
            db.add(target)
            db.commit()
        return {'message':'success'}
    

@router.delete('/unlike')
def unlike(token=Body(), db:Session=Depends(get_db)):
        data=get_by_token(token['token'])
        user=db.query(User).filter(User.name==data).first()
        targetEVENT=db.query(Event).filter(Event.id==token['id']).first()
        if not user or not token['id']:
            raise ValueError('Not enough')
        target=db.query(Likes).filter(Likes.user_id==user.id, Likes.event_id==token['id']).first()
        if target is None:
            raise HTTPException(401, 'Лайк еще не поставлен')
        targetEVENT.like_count-=1
        db.delete(target)
        db.commit()
    

@router.get('/likingp')
def liking(db:Session=Depends(get_db), token=Query(...), id=Query(...)):
        print('started')
        data=get_by_token(token)
        target=db.query(Event).filter(Event.id==id).first()
        print(target.likes)
        print('ended')
        return Response(content='ended', media_type='text/plain')
