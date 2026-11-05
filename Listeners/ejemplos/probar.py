"""Despliega listenersDemo, lo recorre y comprueba que cada listener se ejecutó. Limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, ended, check, done, T

dep = deploy(os.path.join(HERE, 'listenersDemo.bpmn20.xml'))
try:
    pi = start('listenersDemo')['id']
    t = tasks(pi)[0]
    v = call('GET', f"runtime/tasks/{t['id']}/variables?scope=local")[1]
    check(t['priority'] == 80, f"task listener create (javascript) cambió la prioridad -> {t['priority']}")
    check({'name': 'creadaPor', 'value': 'javascript: create'}.items() <= {**v[0]}.items() if v else False,
          f"task listener create dejó la variable local creadaPor -> {v}")
    complete(t['id'], {'decision': 'aprobado'})
    hv = hist_vars(pi)
    check(hv.get('inicio') == 'groovy: start', f"execution listener start del proceso (groovy) -> {hv.get('inicio')}")
    check(hv.get('flujoTomado') is True, f"execution listener take del flujo (expresión) -> {hv.get('flujoTomado')}")
    check(hv.get('decisionFinal') == 'aprobado', f"task listener complete (expresión) -> {hv.get('decisionFinal')}")
    check(hv.get('fin') == 'expresion: end', f"execution listener end del proceso (expresión) -> {hv.get('fin')}")
    check(ended(pi), 'la instancia terminó')
finally:
    undeploy(dep)
done()
