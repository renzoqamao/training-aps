"""Despliega eventListenersDemo y eventListenersError (archivos separados) y comprueba "Reiniciar evento" y "Tipo de entidad". Limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import deploy, undeploy, start, tasks, complete, hist_vars, ended, check, done

dep = deploy(os.path.join(HERE, 'eventListenersDemo.bpmn20.xml'))
dep2 = deploy(os.path.join(HERE, 'eventListenersError.bpmn20.xml'))
try:
    pi = start('eventListenersDemo')['id']
    t = tasks(pi)
    check(len(t) == 1 and t[0]['name'] == 'Trabajar', f"una sola tarea pendiente -> {[x['name'] for x in t]}")
    complete(t[0]['id'])
    hv = hist_vars(pi)
    check(hv.get('senalTarea') is True, f"TASK_COMPLETED relanzado como señal: el evento intermedio la recibió -> {hv.get('senalTarea')}")
    check('senalNunca' not in hv, f"ACTIVITY_STARTED + entityType=task nunca se dispara (no es evento de entidad) -> {hv.get('senalNunca')}")
    check(ended(pi), 'la instancia terminó: la señal liberó la rama paralela')

    pe = start('eventListenersError')['id']
    he = hist_vars(pe)
    check(he.get('errorCapturado') is True, f"TASK_CREATED relanzado como error BPMN: lo capturó el evento de borde -> {he.get('errorCapturado')}")
    check(not tasks(pe) and ended(pe), 'la tarea se canceló junto con el subproceso y la instancia terminó')
finally:
    undeploy(dep)
    undeploy(dep2)
done()
