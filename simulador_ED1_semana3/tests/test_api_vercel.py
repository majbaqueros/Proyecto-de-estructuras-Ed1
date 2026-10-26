"""Pruebas end-to-end HTTP para Vercel y localhost (SQLite aislada)."""
import pytest
from fastapi.testclient import TestClient
from portal.db import configure_db, PasswordReset, session
from portal import services as svc
import app as application
from portal import recovery


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_SECRET', 'very-long-test-secret-abcdefghijklmnopqrstuvwxyz-999')
    monkeypatch.setenv('EMAIL_BACKEND','console')
    configure_db('sqlite:///' + str(tmp_path/'api.sqlite3'))
    application._initialized=True
    adm=svc.bootstrap_admin('Organización A','admin-a@example.com','Super-Admin-Password-345')
    with TestClient(application.app) as c:
        yield c, adm
    application._initialized=False


def test_vercel_entrypoint_and_static(client):
    c,_=client
    from main import app
    assert app is application.app
    assert c.get('/').status_code == 200
    assert 'ED1 Logística' in c.get('/').text
    assert c.get('/client.js').status_code == 200
    assert c.get('/style.css').status_code == 200
    assert c.get('/api/health').json()['database'] == 'conectada'


def test_session_csrf_role_tenant_and_delivery(client):
    c,adm=client
    no=c.get('/api/orders')
    assert no.status_code==401
    auth=c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Super-Admin-Password-345'})
    assert auth.status_code==200,auth.text
    token=auth.json()['csrf']
    assert c.post('/api/routes',json={'name':'La Paz'}).status_code==403
    r=c.post('/api/routes',json={'name':'La Paz'},headers={'x-csrf-token':token})
    assert r.status_code==200,r.text
    place=r.json()['id']
    code=c.get('/api/organization').json()['codigo']
    c2=TestClient(application.app)
    reg=c2.post('/api/auth/register',json={'name':'Cliente A','email':'client-a@example.com',
        'password':'Client-Password-5678','code':code})
    assert reg.status_code==200,reg.text
    csrf_client=reg.json()['csrf']
    assert c2.get('/api/audit').status_code==403
    assert c2.post('/api/routes',json={'name':'No autorizada'},headers={'x-csrf-token':csrf_client}).status_code==403
    order=c2.post('/api/orders',json={'route_id':place,'weight':3.5,'recipient':'Abel'},headers={'x-csrf-token':csrf_client})
    assert order.status_code==200,order.text
    pid=order.json()['id']
    assert c2.get('/api/orders').json()['items'][0]['id']==pid
    assert c.post(f'/api/orders/{pid}/decision',headers={'x-csrf-token':token},json={'action':'aprobar','priority':1}).status_code==200
    delivered=c.post('/api/routes/advance',headers={'x-csrf-token':token},json={'direction':1})
    assert delivered.status_code==200,delivered.text
    assert delivered.json()['entregados']==[pid]
    assert any(x['accion']=='ENTREGAR_PAQUETE' for x in c.get('/api/audit').json()['items'])
    other_admin=svc.bootstrap_admin('Organización B','admin-b@example.com','Super-Admin-Password-345')
    c3=TestClient(application.app)
    assert c3.post('/api/auth/login',json={'email':'admin-b@example.com','password':'Super-Admin-Password-345'}).status_code==200
    assert c3.get('/api/routes').json()['items']==[]
    assert c3.get('/api/orders').json()['items']==[]
    assert all(i['usuario']!='client-a@example.com' for i in c3.get('/api/audit').json()['items'])


def test_password_email_code_and_invalidated_sessions(client,monkeypatch):
    c,_=client
    auth=c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Super-Admin-Password-345'})
    assert auth.status_code==200
    captured=[]
    monkeypatch.setattr(recovery,'deliver_code',lambda to,code: captured.append((to,code)))
    result=c.post('/api/auth/password/request',json={'email':'admin-a@example.com'})
    assert result.status_code==200
    assert captured[0][0]=='admin-a@example.com'
    code=captured[0][1]
    assert len(code)==6 and code.isdigit()
    with session() as db:
        token=db.query(PasswordReset).one()
        assert token.codigo_hash != code
    assert c.post('/api/auth/password/reset',json={'email':'admin-a@example.com','code':'000000' if code!='000000' else '111111','new_password':'Newest-Password-9876'}).status_code==400
    reset=c.post('/api/auth/password/reset',json={'email':'admin-a@example.com','code':code,'new_password':'Newest-Password-9876'})
    assert reset.status_code==200,reset.text
    assert c.get('/api/me').status_code==401
    assert c.post('/api/auth/password/reset',json={'email':'admin-a@example.com','code':code,'new_password':'Newest-Password-9876'}).status_code==400
    assert c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Super-Admin-Password-345'}).status_code==400
    assert c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Newest-Password-9876'}).status_code==200


def test_recovery_unknown_address_does_not_reveal(client,monkeypatch):
    c,_=client
    emitted=[]
    monkeypatch.setattr(recovery,'deliver_code',lambda addr,code:emitted.append(addr))
    r=c.post('/api/auth/password/request',json={'email':'unknown@example.com'})
    assert r.status_code==200
    assert 'Si la dirección pertenece' in r.json()['message']
    assert not emitted


def test_login_throttle_is_persistent(client):
    c,_=client
    for _ in range(5):
        assert c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'wrong-password'}).status_code==400
    blocked=c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Super-Admin-Password-345'})
    assert blocked.status_code==400
    assert 'Demasiados intentos' in blocked.json()['detail']


def test_metrics_benchmark_and_responsive_assets(client):
    c,_=client
    auth=c.post('/api/auth/login',json={'email':'admin-a@example.com','password':'Super-Admin-Password-345'})
    assert auth.status_code==200
    csrf=auth.json()['csrf']
    assert c.get('/api/metrics').status_code==200
    result=c.post('/api/metrics/benchmark',json={'amount':25},headers={'x-csrf-token':csrf})
    assert result.status_code==200
    assert result.json()['quantity']==25
    assert 'append_ms' not in result.json()  # clave del API público: insert_ms
    assert 'insert_ms' in result.json()
    css=c.get('/style.css')
    assert css.status_code==200 and '@media(max-width:760px)' in css.text
    assert c.head('/').status_code==200
