"""Prueba las clases de training-aps-ejemplos.jar desplegado en APS. Limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, ended, check, done, T

dep = deploy(os.path.join(HERE, 'procesos', 'javaDemo.bpmn20.xml'))
try:
    print('javaDemo: delegate por clase, bean en expresión, delegateExpression y listeners')
    pis = [start('javaDemo', {'monto': m})['id'] for m in (1000, 100)]
    v = hist_vars(pis[0])
    check(v.get('total') == 1180.0, f"CalcularTotalDelegate (fields tasa=0.18) -> total={v.get('total')}")
    check(v.get('categoria') == 'ORO', f"ClienteService.categoria(total) -> {v.get('categoria')}")
    check([hist_vars(p).get('instanciasPrevias') for p in pis] == [0, 1],
          f"AuditoriaDelegate (@Autowired HistoryService) -> {[hist_vars(p).get('instanciasPrevias') for p in pis]}")
    check(v.get('trazaListener') == 'start:proceso > start:calcular > end:calcular',
          f"InicioExecutionListener -> {v.get('trazaListener')}")
    t0, t1 = tasks(pis[0])[0], tasks(pis[1])[0]
    loc = call('GET', f"runtime/tasks/{t0['id']}/variables?scope=local")[1]
    check((t0['priority'], t1['priority']) == (100, 50) and t0['dueDate'] and loc and loc[0]['value'] == 'urgente',
          f"PrioridadTaskListener -> prioridades {t0['priority']}/{t1['priority']}, vence {t0['dueDate']}, local {loc}")
    for p in pis: complete(tasks(p)[0]['id'])

    print('Endpoint REST propio')
    st, r = call('GET', 'enterprise/capacitacion/resumen/javaDemo')
    check(r.get('terminadas') == 2 and r.get('enCurso') == 0, f'GET /api/enterprise/capacitacion/resumen/javaDemo -> {r}')

    print('MensajeriaBean: mensaje y señal desde Java')
    pedido = start('pedidoJava', businessKey='P-001')['id']
    pago = start('pagadorJava', {'pedidoId': 'P-001', 'importe': 250})['id']
    check(hist_vars(pago).get('entregado') is True, 'notificarPago() encontró la ejecución y entregó el mensaje')
    check([x['name'] for x in tasks(pedido)] == ['Despachar'] and hist_vars(pedido).get('importe') == 250,
          'el pedido avanzó a Despachar con importe=250')
    otro = start('pagadorJava', {'pedidoId': 'NO-EXISTE', 'importe': 1})['id']
    check(hist_vars(otro).get('entregado') is False, 'sin ejecución esperando -> entregado=false')
    start('alertadorJava')
    check(ended(pedido), 'alertar(tenantId) disparó el evento de límite: el pedido terminó')
finally:
    undeploy(dep)
done()
