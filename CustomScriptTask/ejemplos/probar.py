"""Despliega scriptTaskDemo y prueba las dos ramas (groovy y javascript). Limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, check, done, T

dep = deploy(os.path.join(HERE, 'scriptTaskDemo.bpmn20.xml'))
try:
    for usegroovy, sender, esperado in [(True, 'groovy', 'HOLA APS'), (False, 'javascript', 'SPA aloH')]:
        pi = start('scriptTaskDemo', {'message': 'Hola APS', 'usegroovy': usegroovy})['id']
        v = {x['name']: x['value'] for x in call('GET', f'runtime/process-instances/{pi}/variables')[1]}
        check(v.get('sender') == sender and v.get('resultado') == esperado,
              f"usegroovy={usegroovy}: sender={v.get('sender')!r} resultado={v.get('resultado')!r}")
        complete(tasks(pi)[0]['id'])
finally:
    undeploy(dep)
done()
