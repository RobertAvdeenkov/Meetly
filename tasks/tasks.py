from fastapi import Depends,Query, Body
from fastapi.responses import FileResponse, Response
from fastapi.routing import APIRouter
from auth import create_token,get_user
from sqlalchemy.orm import Session
from database import get_db
from taskrepo import TasksRepositry
from taskservice import TaskService
from models import User, Event,AutLog,Message
from fastapi import HTTPException
from fastapi import Form
from jose import jwt
from config import SECRET,ALGORITHM
from audit import log_action
import bcrypt
import time

router=APIRouter()

@router.get('/')
def root():
    return FileResponse('templates/reglog.html')

@router.post('/reglog')
def reglog(data=Body(), db:Session=Depends(get_db)):
    repo=TasksRepositry(db)
    service=TaskService(repo)
    user=db.query(User).filter(User.name==data['name']).first()
    if not(user is None):
        print(user.password, type(user.password))
    try:
        if user is None:
            service.check_add_user(data['name'], data['password'])
            user=db.query(User).filter(User.name==data['name']).first()
            if user:
                log_action(user_id=user.id, entity='user', details='Создание аккаунта')
        elif not(bcrypt.checkpw(password=data['password'].encode('utf-8'), hashed_password=user.password)):
            raise HTTPException(401)
        token=create_token(user.name)
        return {'status':'ok', 'redirect_url':f'/account?token={token}'}
    except Exception as e:
        print('ERROR:',e)
        raise HTTPException(401)

@router.get('/account')
def account(token:str=Query(...)):
    return FileResponse('templates/mainpage.html')

@router.post('/add')
def add(name: str = Form(...),date: str = Form(...),place: str = Form(...),type: str = Form(...),desc: str = Form(...),token: str = Query(...), tags:str=Form(...),db: Session = Depends(get_db),):
    try:
        data=jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==data['sub']).first()
        repo=TasksRepositry(db)
        service=TaskService(repo)
    
        service.check_add_event(name=name, type=type, user_id=user.id, desc=desc, place=place, end_at=date, tags=tags)
        log_action(user_id=user.id, entity='event', details=f'Добавление мероприятия {name}')
    except Exception as e:
        print('ERROR:',e)
        raise HTTPException(401)

@router.post('/deletemenuRED')
def deletemenuRED(token=Body()):
    try:
        n=token['token']
        data=jwt.decode(n,SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/deletemenu?token={n}'}
    except:
        raise HTTPException(401)

@router.get('/deletemenu')
def deletemenu(token:str=Query(...)):
    try:
        data=jwt.decode(token,SECRET,algorithms=[ALGORITHM])
        return FileResponse('templates/deletemenu.html')
    except:
        raise HTTPException(401)
    
@router.post('/rename')
def rename(token=Body(), db:Session=Depends(get_db)):
    try:
        print(token)
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==data['sub']).first()
        target=db.query(Event).filter(Event.name==token['current'], Event.creator_id==user.id).first()
        old=target.name
        target.name=token['new']
        db.commit()
        log_action(user_id=user.id, entity='event', details=f'Переименование мероприятия {old} на {target.name}')
    except Exception as e:
        print("ERROR:",e)
    
@router.post('/deleteevent')
def deleteEvent(token=Body(), db:Session=Depends(get_db)):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        user=db.query(User).filter(User.name==data['sub']).first()
        service.check_delete_event(user_id=user.id, name=token['deletename'])
        log_action(user_id=user.id, entity='event', details=f'Удаление мероприятия {token['deletename']}')
    except Exception as e:
        print('ERROR:',e)

@router.post('/addplayer')
def addplayer(token=Body(), db:Session=Depends(get_db)):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        user=db.query(User).filter(User.name==data['sub']).first()
        event=db.query(Event).filter(Event.name==token['eventname']).first()
        if event is None:
            raise HTTPException(401, 'Такого мероприятия нету')
        service.check_add_player(name=data['sub'], event_id=event.id)
        log_action(user_id=user.id, entity='player', details=f'Запись в {event.name}')
    except Exception as e:
        print('ERROR:',e)

@router.post('/deletePLAYER')
def deleteplayer(token=Body(), db:Session=Depends(get_db)):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        repo=TasksRepositry(db)
        service=TaskService(repo)
        print('checking')
        user=db.query(User).filter(User.name==data['sub']).first()
        event=db.query(Event).filter(Event.name==token['eventname'], Event.creator_id==user.id).first()
        if not user or not event:
            raise HTTPException(401)
        service.check_delete_player(name=token['player'], event_id=event.id)
        log_action(user_id=user.id, entity='event', details=f'Удаление участника {token['player']} из {event.name}')
    except Exception as e:
        print('ERROR:',e)

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
    try:
        n=token['token']
        data=jwt.decode(n,SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/list?token={n}'}
    except:
        raise HTTPException(401)

@router.get('/list')
def lists():
    return FileResponse('templates/llist.html')

@router.post('/showlist')
def showlist(db:Session=Depends(get_db), token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        repo=TasksRepositry(db)
        service=TasksRepositry(repo)
        message=''
        print('started')
        events=db.query(Event).all()
        users=db.query(User).filter(User.name==data['sub']).first()
        for i in events:
            if users in i.users:
                message+=str(i.name)+f'(дата окончания:{i.end_at})'+f'Место:{i.place}'+f'<br>Информация: {i.desc}<br>Участники'+'{'+'<br>'
                for j in i.users:
                    message+=''+str(j.name)+','+'<br>'
                message+='}'+'<br><br>'
        print(message)
        return {'status':'ok', 'message':message}
    except Exception as e:
        print('ERROR:',e)
    
@router.post('/topmenuRED')
def topRED(token=Body()):
    try:
        n=token['token']
        data=jwt.decode(n,SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/topmenu?token={n}'}
    except:
        raise HTTPException(401)
    
@router.get('/topmenu')
def topmenu():
    return FileResponse('templates/topmenu.html')

@router.post('/topmenuSHOW')
def showtopmenu(db:Session=Depends(get_db), token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        repo=TasksRepositry(db)
        service=TasksRepositry(repo)
        l=db.query(User).filter(User.name==data['sub']).first()
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
    try:
        n=token['token']
        data=jwt.decode(n,SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/history?token={n}'}
    except:
        raise HTTPException(401)
    
@router.get('/history')
def history():
    return FileResponse('templates/history.html')

@router.post('/historySHOW')
def historySHOW(db:Session=Depends(get_db), token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==data['sub']).first()
        l=db.query(AutLog).filter(AutLog.user_id==user.id).all()
        txt=''
        for i in l:
            txt+=str(i.info)+str(i.created_at)+'<br>'
        return {'status':'ok', 'message':txt}
    except Exception as e:
        print('ERROR:',e)
        raise HTTPException(401)
    
@router.get('/logs')
def logs(db:Session=Depends(get_db), token=Query(...)):
    try:
        data=jwt.decode(token,SECRET,algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==data['sub']).first()
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
    except Exception as e:
        print("ERROR:",e)
        raise e
    
@router.post('/globalRED')
def globalRED(token=Body()):
    try:
        return {'status':'ok', 'redirect_url':f'/global?token={token['token']}'}
    except Exception as e:
        print("ERROR:",e)

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
                    txt=f'<br>Мероприятие:{i.name}\tДата окончания:{i.end_at}\tМесто:{i.place}<br>Кол-во участников:{len(i.users)}<br>Информация: {i.desc}<br><br>'
                
            already.add(name)
            top+=txt
        print(top)
        return {'status':'ok', 'message':top}
    except Exception as e:
        print("ERROR:",e)

@router.post('/searchRED')
def searchRED(token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/search?token={token['token']}'}
    except Exception as e:
        print("ERROR:",e)
        raise HTTPException(401)
    
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
            txt+=f'<br>Мероприятие:{i.name}\tДата окончания:{i.end_at}<br>Место:{i.place}\tКол-во участников:{len(i.users)}<br>Информация: {i.desc}<br><br>'
    if txt:
        return {'status':'ok', 'message':txt}
    else:
        return {'status':'ok', 'message':'Ничего не найдено!'}

@router.post('/profileRED')
def profileRED(token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/profiles?token={token['token']}'}
    except Exception as e:
        print("ERROR:",e)

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
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        sendto=db.query(User).filter(User.name==token['user']).first()
        if sendto is None:
            raise HTTPException(401, 'Такого пользователя нету')
        mess=Message(sender_name=data['sub'], info=token['info'], to_id=sendto.id)
        db.add(mess)
        db.commit()
        return {'status':'ok', 'message':'yes'}
    except Exception as e:
        print('ERROR:',e)
        raise HTTPException(401)

@router.post('/profileSEARCHING')
def searchingprof(token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/profile?user={token['name']}&token={token['token']}'}
    except Exception as e:
        print("ERROR:",e)
        raise HTTPException(401)

@router.post('/uvedRED')
def uvedRED(token=Body()):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        return {'status':'ok', 'redirect_url':f'/uved?token={token['token']}'}
    except Exception as e:
        print("ERROR:",e)
        raise HTTPException(401)

@router.get('/uved')
def uved():
    return FileResponse('templates/uved.html')

@router.post('/uvedSHOW')
def uvedSHOW(token=Body(), db:Session=Depends(get_db)):
    try:
        data=jwt.decode(token['token'],SECRET,algorithms=[ALGORITHM])
        user=db.query(User).filter(User.name==data['sub']).first()
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
        
    except Exception as e:
        print("ERROR:",e)
        raise HTTPException(401)