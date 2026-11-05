"""Envía mensajes y señales con la API REST del motor (equivalentes a RuntimeService). Limpia al final."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))
from aps import call, deploy, undeploy, start, tasks, hist_vars, ended, check, done, T, TENANT


def instancias(key):
    return call('GET', f'runtime/process-instances?{T}&processDefinitionKey={key}')[1]['data']


dep = deploy(os.path.join(HERE, 'mensajesSenales.bpmn20.xml'))
try:
    # --- Mensaje dirigido: runtimeService.messageEventReceived(messageName, executionId, variables)
    pi = start('pedidoDemo')['id']
    ex = call('GET', f'runtime/executions?{T}&processInstanceId={pi}&messageEventSubscriptionName=pagoRecibido')[1]['data']
    check(len(ex) == 1 and not tasks(pi), 'la instancia espera el mensaje pagoRecibido (aún sin tareas)')
    call('PUT', f"runtime/executions/{ex[0]['id']}", {'action': 'messageEventReceived', 'messageName': 'pagoRecibido',
                                                       'variables': [{'name': 'importe', 'value': 250}]})
    t = tasks(pi)
    check([x['name'] for x in t] == ['Despachar pedido'], f"tras el mensaje se creó la tarea -> {[x['name'] for x in t]}")
    check(hist_vars(pi).get('importe') == 250, 'el mensaje entregó la variable importe=250')

    # --- Señal de difusión: runtimeService.signalEventReceived(signalName)
    antes = len(instancias('atenderAlertaDemo'))
    call('POST', f'runtime/signals?{T}', {'signalName': 'alertaGlobal', 'tenantId': TENANT})
    check(ended(pi), 'la señal disparó el evento de límite: el pedido terminó (cancelado)')
    nuevas = instancias('atenderAlertaDemo')
    check(len(nuevas) == antes + 1, f'la misma señal inició atenderAlertaDemo ({antes} -> {len(nuevas)})')
    act = call('GET', f"history/historic-activity-instances?{T}&processInstanceId={pi}&activityId=finCancelado")[1]['total']
    check(act == 1, 'el pedido terminó por el camino finCancelado')
    for p in nuevas: call('DELETE', f"runtime/process-instances/{p['id']}")

    # --- Inicio por mensaje: runtimeService.startProcessInstanceByMessage(messageName)
    r = call('POST', f'runtime/process-instances?{T}', {'message': 'nuevaSolicitud', 'tenantId': TENANT,
                                                         'variables': [{'name': 'origen', 'value': 'api'}]})[1]
    check(r['processDefinitionId'].startswith('solicitudDemo:'), f"el mensaje inició {r['processDefinitionId']}")
    call('DELETE', f"runtime/process-instances/{r['id']}")

    # --- Variables con el mensaje: no hace falta que existan; las nuevas se crean y las existentes se sobrescriben
    pv = start('pedidoDemo', {'importe': 100, 'cliente': 'ACME'})['id']
    exv = call('GET', f'runtime/executions?{T}&processInstanceId={pv}&messageEventSubscriptionName=pagoRecibido')[1]['data'][0]['id']
    call('PUT', f'runtime/executions/{exv}', {'action': 'messageEventReceived', 'messageName': 'pagoRecibido', 'variables': [
        {'name': 'importe', 'value': 250}, {'name': 'medioPago', 'value': 'tarjeta'}, {'name': 'cuotas', 'value': 3},
        {'name': 'pagado', 'value': True}, {'name': 'fechaPago', 'value': '2026-11-05T10:00:00Z', 'type': 'date'}]})
    vs = {v['name']: (v['value'], v['type']) for v in call('GET', f'runtime/process-instances/{pv}/variables')[1]}
    check(vs.get('importe') == (250, 'integer') and vs.get('cliente') == ('ACME', 'string'), 'la existente se sobrescribió (importe 100 -> 250); cliente no se tocó')
    check(vs.get('medioPago') == ('tarjeta', 'string') and vs.get('cuotas') == (3, 'integer') and vs.get('pagado') == (True, 'boolean')
          and vs.get('fechaPago', (0, ''))[1] == 'date', 'las nuevas se crearon con su tipo (string, integer, boolean, date)')
    hijas = [e for e in call('GET', f'runtime/executions?{T}&processInstanceId={pv}')[1]['data'] if e['parentId']]
    check(all(not call('GET', f"runtime/executions/{e['id']}/variables?scope=local")[1] for e in hijas),
          'quedaron a nivel de proceso (las ejecuciones hijas no tienen variables locales)')
    call('DELETE', f'runtime/process-instances/{pv}')

    # --- Un mensaje de inicio crea una instancia por envío: puede haber muchas a la vez
    for i in range(3):
        call('POST', f'runtime/process-instances?{T}', {'message': 'nuevaSolicitud', 'tenantId': TENANT, 'businessKey': f'SOL-{i}'})
    act = call('GET', f'runtime/process-instances?{T}&processDefinitionKey=solicitudDemo')[1]['data']
    check(sorted(p['businessKey'] for p in act) == ['SOL-0', 'SOL-1', 'SOL-2'], f'3 envíos del mismo mensaje -> {len(act)} instancias activas a la vez')
    for p in act: call('DELETE', f"runtime/process-instances/{p['id']}")

    # --- Otro proceso NO puede arrancar con el mismo mensaje (la suscripción es única por nombre)
    otro = b"""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" targetNamespace="http://t">
  <message id="m" name="nuevaSolicitud"/>
  <process id="otraSolicitud" isExecutable="true">
    <startEvent id="s"><messageEventDefinition messageRef="m"/></startEvent>
    <sequenceFlow id="f" sourceRef="s" targetRef="e"/><endEvent id="e"/>
  </process>
</definitions>"""
    st, r = call('POST', f'repository/deployments?{T}', files={'file': ('otraSolicitud.bpmn20.xml', otro)}, ok=None)
    check(st == 500, f'otro proceso con el mismo mensaje de inicio nuevaSolicitud -> HTTP {st} (rechazado)')
    if st < 300: undeploy(r['id'])

    # --- Sin ?tenantId en la URL la API del motor rechaza la llamada
    st, _ = call('POST', 'runtime/signals', {'signalName': 'alertaGlobal', 'tenantId': TENANT}, ok=None)
    check(st == 403, f'señal sin ?tenantId en la URL -> HTTP {st}')
finally:
    undeploy(dep)

print('Casos típicos sobre una tarea (solicitudCredito + anuncioCambioTasa)')
deps = [deploy(os.path.join(HERE, f)) for f in ('solicitudCredito.bpmn20.xml', 'anuncioCambioTasa.bpmn20.xml')]
try:
    a = start('solicitudCredito', {'monto': 1000, 'plazo': 10})['id']
    b = start('solicitudCredito', {'monto': 2000, 'plazo': 10})['id']

    # Mensaje de límite interrumpidor: sólo la solicitud A
    ex = call('GET', f'runtime/executions?{T}&processInstanceId={a}&messageEventSubscriptionName=retiroSolicitud')[1]['data']
    call('PUT', f"runtime/executions/{ex[0]['id']}", {'action': 'messageEventReceived', 'messageName': 'retiroSolicitud'})
    fin = call('GET', f'history/historic-activity-instances?{T}&processInstanceId={a}&activityId=finRetirada')[1]['total']
    check(ended(a) and fin == 1, 'mensaje de límite: la solicitud A se canceló por el camino Retirada')
    check(len(tasks(b)) == 1, 'la solicitud B no se enteró (el mensaje va a una sola ejecución)')

    # Un proceso lanza la señal -> límite NO interrumpidor en B
    start('anuncioCambioTasa')
    v = hist_vars(b)
    check(abs(v.get('cuota', 0) - 220) < 1e-9, f"señal lanzada por otro proceso: B recalculó cuota={v.get('cuota')}")
    check([x['name'] for x in tasks(b)] == ['Evaluar crédito'], 'límite no interrumpidor: la tarea de B sigue activa')
    call('DELETE', f'runtime/process-instances/{b}')
finally:
    for d in deps: undeploy(d)
done()
