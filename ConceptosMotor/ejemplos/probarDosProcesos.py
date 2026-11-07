"""Un .bpmn20.xml con dos <process>: qué pasa al desplegarlo con la API del motor y al importarlo en el App Designer.
Limpia al final."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, publish_app, unpublish_app, start, tasks, hist_vars, check, done, T

ARCHIVO = os.path.join(HERE, 'dosProcesos.bpmn20.xml')
APP = 'Training dos procesos'

# --- B. API del motor: despliega todos los <process> del archivo
dep = deploy(ARCHIVO)
try:
    defs = call('GET', f'repository/process-definitions?{T}&deploymentId={dep}')[1]['data']
    check(sorted(d['key'] for d in defs) == ['dosA', 'dosB'], f"API del motor: un despliegue, dos definiciones -> {[d['key'] for d in defs]}")
    pb = start('dosB')['id']
    check(hist_vars(pb).get('listenerDeA') is True, "el event listener definido en dosA también se ejecutó en dosB (mismo archivo)")
    check([t['name'] for t in tasks(pb)] == ['Tarea de B'], 'dosB sigue en su tarea (la señal sólo disparó el borde no interruptor)')
finally:
    undeploy(dep)

# --- C. App Designer: importar el archivo como modelo
with open(ARCHIVO, 'rb') as f:
    mid = call('POST', 'enterprise/process-models/import', files={'file': ('dosProcesos.bpmn20.xml', f.read())})[1]['id']
try:
    modelo = call('GET', f'enterprise/models/{mid}')[1]
    xml = call('GET', f'enterprise/models/{mid}/bpmn20')[1]
    xml = xml.decode() if isinstance(xml, bytes) else str(xml)
    procesos = re.findall(r'<(?:bpmn2:)?process\s[^>]*id="([^"]+)"', xml)
    check(procesos == ['dosA'], f"App Designer: el modelo importado ({modelo.get('name')}) conserva sólo el primer <process> -> {procesos}")
    oyente = re.search(r'<activiti:eventListener[^>]*>', xml)
    check(oyente is not None and 'entityType' not in oyente.group(0),
          f"⚠ el import quita entityType del event listener -> {oyente.group(0) if oyente else None}")
finally:
    call('DELETE', f'enterprise/models/{mid}?cascade=true', ok=None)

# --- C. ... y publicado en una app: la app despliega sólo ese proceso
try:
    r = publish_app(ARCHIVO, APP)
    defs = call('GET', f"repository/process-definitions?{T}&deploymentId={r['deploymentId']}")[1]['data']
    check([d['key'] for d in defs] == ['dosA'], f"app publicada: sólo se despliega dosA -> {[d['key'] for d in defs]}")
finally:
    unpublish_app(APP)
done()
