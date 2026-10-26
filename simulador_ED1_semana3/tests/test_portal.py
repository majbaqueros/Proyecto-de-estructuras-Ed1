import pytest
from portal.db import configure_db
from portal import services as s


@pytest.fixture
def orgs(tmp_path):
    configure_db(f"sqlite:///{tmp_path / 'portal.sqlite3'}")
    a = s.bootstrap_admin("Empresa Alpha", "alpha@example.com", "Password-Alpha-123")
    b = s.bootstrap_admin("Empresa Beta", "beta@example.com", "Password-Beta-123")
    return a, b


def client_for(admin, email):
    code = s.organization(admin['id'])['codigo']
    return s.sign_up_client(code, "Cliente de prueba", email, "Password-Cliente-123")


def test_roles_and_isolation(orgs):
    a,b = orgs
    s.add_route(a['id'], "La Paz")
    s.add_route(b['id'], "Santa Cruz")
    x = client_for(a, 'client-a@example.com')
    y = client_for(b, 'client-b@example.com')
    assert [r['nombre'] for r in s.list_routes(x['id'])] == ["La Paz"]
    assert [r['nombre'] for r in s.list_routes(y['id'])] == ["Santa Cruz"]
    with pytest.raises(ValueError):
        s.create_request(x['id'], s.list_routes(y['id'])[0]['id'], 2)
    with pytest.raises(PermissionError):
        s.add_route(x['id'], "Unauthorized")
    with pytest.raises(PermissionError):
        s.audit(x['id'])
    with pytest.raises(PermissionError):
        s.audit( s.create_receptionist(a['id'], "Rec", "staff@example.com", "Password-Staff-123")['id'])
    assert len(s.list_users(a['id'])) == 3
    assert len(s.list_users(b['id'])) == 2


def test_requests_approval_and_delivery_only_on_matching_stop(orgs):
    a,_ = orgs
    north = s.add_route(a['id'], 'Norte')
    south = s.add_route(a['id'], 'Sur')
    client = client_for(a, 'client-x@example.com')
    p = s.create_request(client['id'], south['id'], 4)
    assert s.list_orders(client['id'])[0]['estado'] == 'solicitado'
    assert s.advance_and_deliver(a['id'])['entregados'] == []
    assert s.current_location(a['id']) == 'Norte'
    with pytest.raises(ValueError):
        s.delete_route(a['id'], south['id'])
    s.set_order_status(a['id'], p, 'aprobar', priority=1)
    result = s.advance_and_deliver(a['id'])
    assert result['ubicacion'] == 'Sur'
    assert result['entregados'] == [p]
    assert result['punteros_ok'] is True
    assert s.list_orders(client['id'])[0]['estado'] == 'entregado'
    assert s.advance_and_deliver(a['id'])['ubicacion'] == 'Norte'


def test_order_ownership_and_audit(orgs):
    a,b = orgs
    place = s.add_route(a['id'], 'Centro')
    c1 = client_for(a, 'one@example.com')
    c2 = client_for(a, 'two@example.com')
    p1=s.create_request(c1['id'],place['id'],1)
    p2=s.create_request(c2['id'],place['id'],2)
    assert [p['id'] for p in s.list_orders(c1['id'])] == [p1]
    assert [p['id'] for p in s.list_orders(c2['id'])] == [p2]
    with pytest.raises(PermissionError):
        s.set_order_status(c1['id'],p2,'aprobar',1)
    with pytest.raises(ValueError):
        s.set_order_status(b['id'],p1,'aprobar',1)
    s.set_order_status(a['id'],p1,'aprobar',1)
    logs=s.audit(a['id'])
    assert any(x['accion']=='SOLICITAR_PAQUETE' and x['entidad_id']==p1 for x in logs)
    assert any(x['accion']=='APROBAR_PAQUETE' and x['entidad_id']==p1 for x in logs)
    assert not any(x['usuario']=='beta@example.com' for x in logs)


def test_validations_and_login(orgs):
    a,_=orgs
    with pytest.raises(ValueError):
        s.login('alpha@example.com','wrong-password')
    assert s.login('alpha@example.com','Password-Alpha-123')['rol']=='admin'
    with pytest.raises(ValueError):
        s.add_route(a['id'],'')
    s.add_route(a['id'],'La Paz')
    with pytest.raises(ValueError):
        s.add_route(a['id'],'la paz')
    c=client_for(a,'tester@example.com')
    with pytest.raises(ValueError):
        s.create_request(c['id'],10000,1)
    with pytest.raises(ValueError):
        s.create_request(c['id'],s.list_routes(c['id'])[0]['id'],-1)


def test_priority_queue_and_linked_route_still_manual(orgs):
    a,_ = orgs
    loc=s.add_route(a['id'],'Única zona')
    c=client_for(a,'priority@example.com')
    p1=s.create_request(c['id'],loc['id'],1)
    p2=s.create_request(c['id'],loc['id'],1)
    s.set_order_status(a['id'],p1,'aprobar',3)
    s.set_order_status(a['id'],p2,'aprobar',1)
    r=s.advance_and_deliver(a['id'])
    assert r['entregados']==[p2,p1]
    assert r['punteros_ok'] is True


def test_failed_login_registered_in_admin_log(orgs):
    a,_=orgs
    with pytest.raises(ValueError):
        s.login('alpha@example.com','nope')
    logs=s.audit(a['id'])
    assert any(row['accion']=='LOGIN_FALLIDO' and row['usuario']=='alpha@example.com' for row in logs)


def test_staff_can_process_but_cannot_manage_routes(orgs):
    a,_=orgs
    route = s.add_route(a['id'],"Centro")
    clerk = s.create_receptionist(a['id'],"Recepcionista", "reception@example.com", "Password-Reception-123")
    client = client_for(a,'customera@example.com')
    p=s.create_request(client['id'],route['id'],5)
    assert s.set_order_status(clerk['id'],p,'aprobar',2)=='aprobado'
    assert s.advance_and_deliver(clerk['id'])['entregados']==[p]
    with pytest.raises(PermissionError):
        s.delete_route(clerk['id'],route['id'])
    with pytest.raises(PermissionError):
        s.list_users(clerk['id'])


def test_double_approval_rejected_and_log_benchmark(orgs):
    a,_=orgs
    route=s.add_route(a['id'],"Central")
    client=client_for(a,'customerd@example.com')
    p=s.create_request(client['id'],route['id'],1)
    s.set_order_status(a['id'],p,'aprobar',1)
    with pytest.raises(ValueError):
        s.set_order_status(a['id'],p,'aprobar',2)
    s.record_benchmark(a['id'],100,2.7)
    assert any(e['accion']=='EJECUTAR_BENCHMARK' for e in s.audit(a['id']))
