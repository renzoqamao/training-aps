"""Cliente mínimo para probar los ejemplos de la capacitación contra un APS (sólo librería estándar).

Variables de entorno:
  APS_BASE  (por defecto http://localhost:8080/activiti-app)
  APS_USER  (obligatoria)   APS_PASS  (obligatoria)   APS_TENANT (por defecto tenant_1)
"""
import base64, json, os, sys, uuid, urllib.request, urllib.error

BASE = os.environ.get('APS_BASE', 'http://localhost:8080/activiti-app').rstrip('/') + '/api/'
TENANT = os.environ.get('APS_TENANT', 'tenant_1')
T = f'tenantId={TENANT}'
try:
    AUTH = 'Basic ' + base64.b64encode(f"{os.environ['APS_USER']}:{os.environ['APS_PASS']}".encode()).decode()
except KeyError:
    sys.exit('Define APS_USER y APS_PASS (ver README de la capacitación).')


def call(method, path, body=None, files=None, ok=(200, 201, 204)):
    """Devuelve (status, json|texto). Lanza AssertionError si el status no está en `ok` (ok=None: no validar)."""
    headers, data = {'Authorization': AUTH}, None
    if files:  # multipart: {'file': (nombre, bytes)}
        b = uuid.uuid4().hex
        name, content = files['file']
        data = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                f'Content-Type: application/octet-stream\r\n\r\n').encode() + content + f'\r\n--{b}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={b}'
    elif body is not None:
        data, headers['Content-Type'] = json.dumps(body).encode(), 'application/json'
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            st, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        st, raw = e.code, e.read()
    try:
        res = json.loads(raw) if raw else None
    except ValueError:
        res = raw.decode(errors='replace')
    if ok is not None:
        assert st in ok, f'{method} {path} -> {st}: {str(res)[:300]}'
    return st, res


def deploy(path):
    """Despliega un .bpmn20.xml con la API del motor y devuelve el id del deployment."""
    with open(path, 'rb') as f:
        return call('POST', f'repository/deployments?{T}', files={'file': (os.path.basename(path), f.read())})[1]['id']


def undeploy(dep_id):
    call('DELETE', f'repository/deployments/{dep_id}?cascade=true')


def publish_app(path, app_name):
    """Flujo de la API PÚBLICA (como el App Designer): importa el BPMN como modelo, crea una app con él y la publica.
    Sólo los procesos publicados en una app se pueden iniciar con /api/enterprise/process-instances.
    Devuelve dict con processDefinitionId y los ids necesarios para unpublish_app()."""
    unpublish_app(app_name)  # restos de una ejecución anterior
    with open(path, 'rb') as f:
        mid = call('POST', 'enterprise/process-models/import', files={'file': (os.path.basename(path), f.read())})[1]['id']
    aid = call('POST', 'enterprise/models', {'name': app_name, 'modelType': 3})[1]['id']  # 3 = app; 'key' da 400
    call('PUT', f'enterprise/app-definitions/{aid}', {'appDefinition': {'name': app_name, 'definition': {
        'models': [{'id': mid}], 'theme': 'theme-1', 'icon': 'glyphicon-asterisk'}}, 'publish': True})
    rt = next(a for a in call('GET', 'enterprise/runtime-app-definitions')[1]['data'] if a.get('name') == app_name)
    pd = call('GET', f"repository/process-definitions?{T}&deploymentId={rt['deploymentId']}")[1]['data'][0]['id']
    return {'processDefinitionId': pd, 'deploymentId': rt['deploymentId']}


def unpublish_app(app_name):
    """Quita la app del usuario, borra su deployment (cascade) y los modelos de app y proceso. Idempotente."""
    for a in call('GET', 'enterprise/runtime-app-definitions')[1]['data']:
        if a.get('name') == app_name:
            call('DELETE', f"enterprise/app-definitions/{a['id']}", ok=None)
            for d in call('GET', f'repository/deployments?{T}')[1]['data']:
                if d['name'] == app_name or d['id'] == a.get('deploymentId'):
                    undeploy(d['id'])
    for m in call('GET', 'enterprise/models?filter=myApps&modelType=3')[1]['data']:
        if m['name'] == app_name:
            procs = call('GET', f"enterprise/app-definitions/{m['id']}")[1]['definition']['models']
            call('DELETE', f"enterprise/models/{m['id']}?cascade=true&deleteRuntimeApp=true")
            for p in procs:  # sin cascade=true el modelo de proceso puede quedar (probado)
                call('DELETE', f"enterprise/models/{p['id']}?cascade=true")


def start(key, variables=None, **extra):
    """Inicia por clave con la API del motor (tenantId en URL y en body)."""
    body = {'processDefinitionKey': key, 'tenantId': TENANT, **extra}
    if variables:
        body['variables'] = [{'name': k, 'value': v} for k, v in variables.items()]
    return call('POST', f'runtime/process-instances?{T}', body)[1]


def tasks(pi):
    return call('GET', f'runtime/tasks?{T}&processInstanceId={pi}')[1]['data']


def complete(task_id, variables=None):
    body = {'action': 'complete'}
    if variables:
        body['variables'] = [{'name': k, 'value': v} for k, v in variables.items()]
    call('POST', f'runtime/tasks/{task_id}', body)


def hist_vars(pi):
    """Variables históricas de la instancia como dict (sirve también con el proceso terminado)."""
    d = call('GET', f'history/historic-variable-instances?{T}&processInstanceId={pi}&size=1000')[1]['data']
    return {v['variable']['name']: v['variable']['value'] for v in d}


def ended(pi):
    return call('GET', f'history/historic-process-instances/{pi}')[1].get('endTime') is not None


def check(cond, msg):
    """Imprime OK/FALLO y acumula el resultado."""
    print(('  OK    ' if cond else '  FALLO ') + msg)
    check.fails += 0 if cond else 1


check.fails = 0


def done():
    print('\nTodo OK' if not check.fails else f'\n{check.fails} comprobación(es) fallaron')
    sys.exit(1 if check.fails else 0)
