"""Recorrido comprobado de la API pública (/api/enterprise) y la del motor (/api/{repository,runtime,history,...}).
Opcional: APS_TEST_PASS=<clave> crea/reutiliza el usuario capacitacion.api@local.test (sin capacidades)
para comprobar quién puede usar cada API; al final lo deja inactivo (APS no permite borrar usuarios)."""
import base64, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
import aps
from aps import call, publish_app, unpublish_app, hist_vars, check, done, T

print('1. ¿Pública o motor? Se distingue por la URL')
check(call('GET', 'enterprise/app-version')[0] == 200, 'pública: GET /api/enterprise/app-version -> 200')
check(call('GET', 'management/engine')[0] == 200, 'motor:   GET /api/management/engine -> 200')

print('2. La API del motor exige ?tenantId en la URL')
check(call('GET', 'repository/process-definitions', ok=None)[0] == 403, 'sin tenantId -> 403')
check(call('GET', f'repository/process-definitions?{T}')[0] == 200, 'con tenantId -> 200')

APP = 'Capacitacion API'
print('3a. Publicar como app (import modelo -> app -> publish); desplegar con la API del motor NO sirve para la pública')
app = publish_app(os.path.join(HERE, 'procesoApi.bpmn20.xml'), APP)
pd = app['processDefinitionId']
check(pd.startswith('procesoApi:'), f'app publicada -> {pd}')
pis = []
try:

    print('3b. Ciclo completo con la API pública')
    for i in range(3):
        r = call('POST', 'enterprise/process-instances', {'processDefinitionId': pd, 'name': f'Solicitud {i}',
                                                          'variables': [{'name': 'monto', 'value': 100 * (i + 1)}]})[1]
        pis.append(r['id'])
    check(len(pis) == 3, f'POST /enterprise/process-instances x3 -> {pis}')
    v = call('GET', f'enterprise/process-instances/{pis[0]}/variables')[1]
    check(any(x.get('name', x.get('id')) == 'monto' and x['value'] == 100 for x in v), f'GET .../variables -> {v}')
    for pi in pis:
        t = call('POST', 'enterprise/tasks/query', {'processInstanceId': pi})[1]['data'][0]
        call('PUT', f"enterprise/tasks/{t['id']}/action/complete")
    h = call('POST', 'enterprise/historic-process-instances/query', {'processDefinitionId': pd, 'finished': True})[1]
    check(h['total'] == 3, f"historic-process-instances finished=true -> total={h['total']}")

    print('4. Paginación: en la pública start = nº de PÁGINA; en la del motor start = DESPLAZAMIENTO')
    e = call('POST', 'enterprise/historic-process-instances/query', {'processDefinitionId': pd, 'size': 2, 'start': 1})[1]
    m = call('GET', f'history/historic-process-instances?{T}&processDefinitionId={pd}&size=2&start=1')[1]
    check(len(e['data']) == 1, f"pública size=2 start=1 -> {len(e['data'])} fila (página 2 de 2)")
    check(len(m['data']) == 2, f"motor   size=2 start=1 -> {len(m['data'])} filas (desde la 2.ª)")

    print('5. Tareas históricas con variables (bug PostgreSQL): falla si la página sale llena')
    q = {'processDefinitionId': pd, 'includeProcessVariables': True}
    st_llena = call('POST', 'enterprise/historic-tasks/query', {**q, 'size': 2}, ok=None)[0]
    st_sobra = call('POST', 'enterprise/historic-tasks/query', {**q, 'size': 25}, ok=None)[0]
    st_motor = call('POST', f'query/historic-task-instances?{T}', {'processDefinitionId': pd, 'includeProcessVariables': True}, ok=None)[0]
    print(f'  info  pública size=2 (llena) -> {st_llena} | pública size=25 (sobra) -> {st_sobra} | motor -> {st_motor}')
    check(st_sobra == 200, 'con la página holgada la pública responde 200')
    tareas = call('POST', 'enterprise/historic-tasks/query', {'processDefinitionId': pd, 'size': 2})[1]
    check(tareas['total'] == 3 and len(tareas['data']) == 2, 'workaround: sin include y paginando -> 200')
    check(hist_vars(pis[0]).get('monto') == 100, 'workaround: variables aparte con /history/historic-variable-instances')

    pw = os.environ.get('APS_TEST_PASS')
    if pw:
        print('6. Usuario SIN capacidades: puede usar la pública, no la del motor')
        email = 'capacitacion.api@local.test'
        found = call('GET', f'enterprise/admin/users?tenantId=1&filter={email}')[1]['data']
        if found:
            uid = found[0]['id']
            # la contraseña se cambia con la actualización masiva (PUT /admin/users/{id} no la aplica: 401 al entrar)
            call('PUT', 'enterprise/admin/users', {'users': [uid], 'status': 'active', 'password': pw})
        else:
            uid = call('POST', 'enterprise/admin/users', {'email': email, 'firstName': 'Capacitacion', 'lastName': 'API',
                                                          'password': pw, 'tenantId': 1, 'type': 'enterprise', 'status': 'active'})[1]['id']
        try:
            saved = aps.AUTH
            aps.AUTH = 'Basic ' + base64.b64encode(f'{email}:{pw}'.encode()).decode()
            check(call('GET', 'enterprise/profile')[0] == 200, 'pública GET /enterprise/profile -> 200')
            st = call('GET', f'repository/process-definitions?{T}', ok=None)[0]
            check(st == 403, f'motor GET /repository/process-definitions -> {st} (necesita tenant-admin o tenant-admin-api)')
        finally:
            aps.AUTH = saved
            call('PUT', 'enterprise/admin/users', {'users': [uid], 'status': 'inactive'})
    else:
        print('6. (omitido: define APS_TEST_PASS para probar un usuario sin capacidades)')
finally:
    unpublish_app(APP)
done()
