"""Propiedades de actividad: multiinstancia, asíncrona/exclusiva, compensación y propiedades de user task.
Despliega propiedades.bpmn20.xml con la API del motor, recorre cada proceso y limpia al final.
La parte 7 (checkbox Exclusiva del editor) importa dos modelos con la API pública y los borra.
La parte 8 publica una app y usa dos usuarios de prueba (demo.iniciador / demo.asignado @demo.test), que crea
la primera vez y reutiliza después (APS no borra usuarios). Clave: APS_DEMO_PASS (por defecto Demo-Clave-2026)."""
import os, sys, time
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, ended, check, done, T, TENANT, publish_app, unpublish_app

APP = 'Demo propiedades de actividad'


def esperar(cond, segundos=90):
    fin = time.time() + segundos
    while time.time() < fin:
        r = cond()
        if r:
            return r
        time.sleep(2)
    return None


def vuelta(t):
    return {v['name']: v['value'] for v in call('GET', f"runtime/tasks/{t['id']}/variables?scope=local")[1]}.get('vuelta')


dep = deploy(os.path.join(HERE, 'propiedades.bpmn20.xml'))
modelos = []
try:
    print('1. Multiinstancia paralela: colección + variable del elemento + condición de terminación')
    pi = start('propMiParalela', {'revisoresTexto': 'ana.demo,beto.demo,carla.demo'})['id']
    ts = tasks(pi)
    check(sorted(t['assignee'] for t in ts) == ['ana.demo', 'beto.demo', 'carla.demo'],
          f"3 tareas a la vez, una por elemento: {sorted(t['assignee'] for t in ts)}")
    complete(ts[0]['id'])
    complete(ts[1]['id'])
    ts = tasks(pi)
    check([t['name'] for t in ts] == ['Siguiente paso'],
          f"con 2 de 3 completadas (nrOfCompletedInstances >= 2) se cancela la tercera: {[t['name'] for t in ts]}")
    call('DELETE', f'runtime/process-instances/{pi}')

    print('2. Multiinstancia secuencial: cardinalidad 3, loopCounter y salida anticipada')
    pi = start('propMiSecuencial')['id']
    ts = tasks(pi)
    check(len(ts) == 1 and vuelta(ts[0]) == 0, f'una tarea a la vez; loopCounter = {vuelta(ts[0])}')
    complete(ts[0]['id'], {'voto': 'SI'})
    ts = tasks(pi)
    check(len(ts) == 1 and vuelta(ts[0]) == 1, f'segunda vuelta; loopCounter = {vuelta(ts[0])}')
    complete(ts[0]['id'], {'voto': 'NO'})
    check(ended(pi), 'voto NO cumple la condición de terminación: el proceso termina sin la tercera vuelta')

    print('3. Asíncrona: el inicio responde antes de ejecutar la actividad')
    r = start('propAsyncOk')
    check(r['ended'] is False, 'la respuesta del inicio llega con la instancia detenida en la actividad asíncrona')
    check(esperar(lambda: ended(r['id'])) is True, 'el job de fondo la ejecuta y el proceso termina')
    check(hist_vars(r['id']).get('hecho') is True, 'la actividad sí se ejecutó (hecho = true)')

    print('4. Un error síncrono deshace todo; uno asíncrono queda en un job con reintentos')
    st, _ = call('POST', f'runtime/process-instances?{T}', {'processDefinitionKey': 'propSyncFalla', 'tenantId': TENANT}, ok=None)
    n = call('GET', f'history/historic-process-instances?{T}&processDefinitionKey=propSyncFalla')[1]['total']
    check(st >= 400 and n == 0, f'síncrona: el inicio da HTTP {st} y no queda ninguna instancia (rollback)')
    pi = start('propAsyncFalla', {'falla': True})['id']
    check(not ended(pi), 'asíncrona: la instancia existe aunque la actividad falle después')
    t0 = time.time()
    dl = esperar(lambda: call('GET', f'management/deadletter-jobs?{T}&processInstanceId={pi}')[1]['data'])
    check(bool(dl), f'tras agotar los reintentos el job pasa a dead letter jobs ({time.time() - t0:.0f} s)')
    if dl:
        msg = dl[0].get('exceptionMessage') or ''
        check(dl[0]['retries'] == 0 and msg != '', f"retries = {dl[0]['retries']}, exceptionMessage = {msg[:70]}")
        print('   reintentar el dead letter job después de corregir la causa')
        call('PUT', f'runtime/process-instances/{pi}/variables', [{'name': 'falla', 'value': False}])
        st, _ = call('PUT', f"management/deadletter-jobs/{dl[0]['id']}", {'action': 'move'}, ok=None)
        check(st in (200, 204), f'PUT management/deadletter-jobs/{{id}} {{"action": "move"}} -> HTTP {st}')
        check(esperar(lambda: ended(pi)) is True and hist_vars(pi).get('hecho') is True,
              'el job vuelve a la cola, se ejecuta y el proceso termina')
    if not ended(pi):
        call('DELETE', f'runtime/process-instances/{pi}')

    print('5. Compensación: el manejador sólo corre cuando se lanza el evento')
    a = start('propCompensa', {'deshacer': False})['id']
    b = start('propCompensa', {'deshacer': True})['id']
    va, vb = hist_vars(a), hist_vars(b)
    check(va.get('reservado') is True and 'anulado' not in va, 'sin lanzar: se reservó y "Anular reserva" no se ejecutó')
    check(vb.get('reservado') is True and vb.get('anulado') is True, 'lanzando la compensación: se ejecutó "Anular reserva"')

    print('6. User task: prioridad, categoría y fecha de vencimiento')
    pi = start('propUserTask', {'urgencia': 7})['id']
    t = tasks(pi)[0]
    check(t['priority'] == 0 and t.get('category') is None and t.get('dueDate') is None,
          f"sin propiedades: priority = {t['priority']}, category = {t.get('category')}, dueDate = {t.get('dueDate')}")
    complete(t['id'])
    t = tasks(pi)[0]
    dias = (datetime.fromisoformat(t['dueDate'].replace('Z', '+00:00')) - datetime.now(timezone.utc)).total_seconds() / 86400
    check(t['priority'] == 70, f"priority = ${{urgencia * 10}} con urgencia 7 -> {t['priority']}")
    check(t['category'] == 'categoriaDemo', f"category = {t['category']}")
    check(1.9 < dias < 2.1, f"dueDate = P2D -> {t['dueDate']} ({dias:.2f} días)")
    q = call('GET', f'runtime/tasks?{T}&category=categoriaDemo&processInstanceId={pi}')[1]['data']
    check([x['id'] for x in q] == [t['id']], 'la API del motor filtra tareas por categoría')
    call('DELETE', f'runtime/process-instances/{pi}')

    print('7. Editor de APS: checkbox Exclusiva')

    def importar(nombre, atributos):
        xml = ('<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
               'xmlns:activiti="http://activiti.org/bpmn" targetNamespace="t">'
               f'<process id="{nombre}" name="{nombre}"><startEvent id="i"/><sequenceFlow id="f1" sourceRef="i" targetRef="s"/>'
               f'<serviceTask id="s" name="S" activiti:expression="${{true}}" {atributos}/>'
               '<sequenceFlow id="f2" sourceRef="s" targetRef="e"/><endEvent id="e"/></process></definitions>')
        mid = call('POST', 'enterprise/process-models/import', files={'file': (nombre + '.bpmn20.xml', xml.encode())})[1]['id']
        modelos.append(mid)
        js = call('GET', f'enterprise/models/{mid}/editor/json')[1]
        return mid, next(c['properties'] for c in js['model']['childShapes'] if c['resourceId'] == 's').get('exclusivedefinition')

    _, sin = importar('propEditorSinAtributo', 'activiti:async="true"')
    mid, con = importar('propEditorNoExclusiva', 'activiti:async="true" activiti:exclusive="false"')
    check(sin is True, f'XML sin activiti:exclusive -> el editor muestra Exclusiva = {sin}')
    check(con is False, f'XML con activiti:exclusive="false" -> el editor muestra Exclusiva = {con}')
    xml = call('GET', f'enterprise/models/{mid}/bpmn20')[1]
    check('activiti:exclusive="false"' in str(xml), 'desmarcada, el editor exporta activiti:exclusive="false"')

    print('8. API pública: iniciador puede completar, reasignación desactivada y filtro por categoría')
    tenant = call('GET', 'enterprise/profile')[1]['tenantId']
    clave = os.environ.get('APS_DEMO_PASS', 'Demo-Clave-2026')
    ids = {}
    for nombre in ('iniciador', 'asignado'):  # usuarios de prueba: se crean una vez y se reutilizan
        email = f'demo.{nombre}@demo.test'
        u = call('GET', f'enterprise/admin/users?tenantId={tenant}&filter=demo.{nombre}')[1]['data']
        ids[nombre] = u[0]['id'] if u else call('POST', 'enterprise/admin/users', {
            'email': email, 'firstName': 'Demo', 'lastName': nombre.capitalize(), 'password': clave,
            'tenantId': tenant, 'type': 'enterprise', 'status': 'active'})[1]['id']
    INI, ASIG = ('demo.iniciador@demo.test', clave), ('demo.asignado@demo.test', clave)
    app = publish_app(os.path.join(HERE, 'iniciador.bpmn20.xml'), APP, share_with=[ids['iniciador']])
    pi = call('POST', 'enterprise/process-instances', {'processDefinitionId': app['processDefinitionId'], 'name': 'demo',
              'variables': [{'name': 'asignado', 'value': str(ids['asignado'])}]}, user=INI)[1]['id']
    tarea = lambda: call('GET', f'runtime/tasks?{T}&processInstanceId={pi}')[1]['data'][0]

    t = tarea()
    rep = call('GET', f"enterprise/tasks/{t['id']}", user=INI)[1]
    check(rep.get('initiatorCanCompleteTask') is True, f"la tarea informa initiatorCanCompleteTask = {rep.get('initiatorCanCompleteTask')}")
    st, res = call('POST', 'enterprise/tasks/query', {'processInstanceId': pi, 'category': 'categoriaDemo'}, user=ASIG, ok=None)
    check(st == 400, f'la API pública NO filtra por categoría: el campo category da HTTP {st} (campo no reconocido)')
    lista = call('POST', 'enterprise/tasks/query', {'processInstanceId': pi}, user=ASIG)[1]['data']
    check(lista and lista[0].get('category') == 'categoriaDemo',
          f"pero sí la devuelve en cada tarea: category = {lista[0].get('category') if lista else None}")
    st, _ = call('PUT', f"enterprise/tasks/{t['id']}/action/complete", user=INI, ok=None)
    check(st == 200, f'con la opción, el iniciador (no asignado) completa la tarea -> HTTP {st}')

    t = tarea()
    st, _ = call('PUT', f"enterprise/tasks/{t['id']}/action/complete", user=INI, ok=None)
    check(st == 403, f'sin la opción, el iniciador no puede completarla -> HTTP {st}')
    call('PUT', f"enterprise/tasks/{t['id']}/action/complete", user=ASIG)

    t = tarea()
    rep = call('GET', f"enterprise/tasks/{t['id']}", user=ASIG)[1]
    check(rep.get('deactivateUserTaskReassignment') is True,
          f"la tarea informa deactivateUserTaskReassignment = {rep.get('deactivateUserTaskReassignment')}")
    # sólo la interfaz web lo aplica (limita el selector de asignado); el backend no lo valida
    st, _ = call('PUT', f"enterprise/tasks/{t['id']}/action/assign", {'assignee': str(ids['iniciador'])}, user=ASIG, ok=None)
    check(st == 200, f'pero la API pública SÍ deja reasignarla al asignado -> HTTP {st} (no es una restricción de seguridad)')
finally:
    unpublish_app(APP)
    for m in modelos:
        call('DELETE', f'enterprise/models/{m}?cascade=true', ok=None)
    undeploy(dep)
done()
