"""Definiciones, versiones, instancias y ejecuciones. Despliega el mismo archivo dos veces y limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, ended, check, done, T, TENANT

F = os.path.join(HERE, 'ejecuciones.bpmn20.xml')
deps = [deploy(F)]
try:
    print('1. Un despliegue crea una definición por cada <process>')
    d = call('GET', f'repository/process-definitions?{T}&deploymentId={deps[0]}')[1]['data']
    check(sorted((x['key'], x['version']) for x in d) == [('ejLimite', 1), ('ejParalelo', 1), ('ejSecuencial', 1)],
          f"definiciones -> {sorted(x['id'] for x in d)}")

    print('2. Ejecuciones: siempre una raíz + una hija por cada camino activo')
    for key, esperado in [('ejSecuencial', 2), ('ejParalelo', 3), ('ejLimite', 3)]:
        pi = start(key)['id']
        ex = call('GET', f'runtime/executions?{T}&processInstanceId={pi}')[1]['data']
        forma = sorted(('raíz' if e['parentId'] is None else 'hija', e.get('activityId') or '-') for e in ex)
        check(len(ex) == esperado, f'{key}: {len(ex)} ejecuciones {forma}')
        call('DELETE', f'runtime/process-instances/{pi}')

    print('3. Versiones: redesplegar crea la v2; las instancias existentes no migran')
    a = start('ejSecuencial')
    deps.append(deploy(F))
    b = start('ejSecuencial')
    check(a['processDefinitionId'].startswith('ejSecuencial:1:'), f"A (iniciada antes) sigue en {a['processDefinitionId']}")
    check(b['processDefinitionId'].startswith('ejSecuencial:2:'), f"B (por clave, después) usa {b['processDefinitionId']}")
    latest = call('GET', f'repository/process-definitions?{T}&key=ejSecuencial&latest=true')[1]['data']
    check([x['version'] for x in latest] == [2], 'latest=true sólo devuelve la v2')

    print('4. Iniciar por id elige una versión concreta (sin tenantId en el body)')
    v1 = call('GET', f'repository/process-definitions?{T}&key=ejSecuencial&version=1')[1]['data'][0]['id']
    c = call('POST', f'runtime/process-instances?{T}', {'processDefinitionId': v1})[1]
    check(c['processDefinitionId'] == v1, f"C por id de v1 -> {c['processDefinitionId']}")
    st = call('POST', f'runtime/process-instances?{T}', {'processDefinitionId': v1, 'tenantId': TENANT}, ok=None)[0]
    check(st == 400, f'por id + tenantId en el body -> HTTP {st}')

    print('5. Suspender una definición impide iniciarla; las instancias existentes siguen')
    call('PUT', f'repository/process-definitions/{v1}', {'action': 'suspend'})
    st = call('POST', f'runtime/process-instances?{T}', {'processDefinitionId': v1}, ok=None)[0]
    check(st == 500, f'iniciar la v1 suspendida -> HTTP {st}')
    check(not ended(a['id']), 'la instancia A (v1) sigue existiendo')
    call('PUT', f'repository/process-definitions/{v1}', {'action': 'activate'})
    check(call('POST', f'runtime/process-instances?{T}', {'processDefinitionId': v1})[0] == 201, 'reactivada: se puede iniciar otra vez')
finally:
    for d in deps:
        undeploy(d)
done()
