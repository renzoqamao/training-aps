"""Comprueba el efecto de beans-whitelist.conf en service tasks con expresiones. Limpia al final.
APS_WHITELIST=true (por defecto, como el producto) o false si el servidor tiene beans.whitelisting.enabled=false."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, check, done, T, TENANT

dep = deploy(os.path.join(HERE, 'serviceTaskWhitelist.bpmn20.xml'))
try:
    WL = os.environ.get('APS_WHITELIST', 'true').lower() == 'true'
    # La instancia actual aún no está en BD cuando corre la expresión: la 1.ª cuenta 0, la 2.ª cuenta 1
    p1, p2 = start('serviceTaskPermitido')['id'], start('serviceTaskPermitido')['id']
    n1, n2 = hist_vars(p1).get('instancias'), hist_vars(p2).get('instancias')
    check((n1, n2) == (0, 1), f"bean permitido (historyService) -> 1.ª instancia={n1}, 2.ª instancia={n2}")
    for p in (p1, p2): complete(tasks(p)[0]['id'])

    st, r = call('POST', f'runtime/process-instances?{T}',
                 {'processDefinitionKey': 'serviceTaskBloqueado', 'tenantId': TENANT}, ok=None)
    check(st == (500 if WL else 201), f"bean fuera de la lista (runtimeService), whitelist={'activa' if WL else 'desactivada'} -> HTTP {st}")

    pi = start('serviceTaskExpresion', {'monto': 100})['id']
    v = hist_vars(pi)
    check(abs(v.get('total', 0) - 118) < 1e-9, f"expresión sin beans -> total={v.get('total')}")
finally:
    undeploy(dep)
done()
