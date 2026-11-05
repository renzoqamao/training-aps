# Mensajes y señales

El ``RuntimeService`` se utiliza para informar al motor de procesos que se ha recibido un mensaje o una señal.

## Mensajes

Los mensajes siempre están dirigidos a una instancia de proceso específica (execution).
```
runtimeService.messageEventReceived(messageName, executionId);
runtimeService.messageEventReceived(messageName, executionId, processVariables);
```

## Señales

Las señales son de naturaleza de difusión predeterminada; las recibe todo el motor de procesos. Alfresco Process Services también permite que una señal esté dirigida a una instancia de proceso específica (esta es una extensión que no es de BPMN 2).

```
runtimeService.signalEventReceived(signalName);
runtimeService.signalEventReceived(signalName, processVariables);
runtimeService.signalEventReceived(signalName, executionId);
runtimeService.signalEventReceived(signalName, executionId, processVariables);
```

Las siguientes construcciones BPMN que se pueden incluir en una definición de proceso se activan "informando" al motor de proceso que se han recibido:

- Evento de señal de límite (Boundary Signal Event)
- Evento de mensaje de límite (Boundary Message Event)
- Evento de captura de señal intermedia (Intermediate Signal Catching Event)
- Evento de lanzamiento de señal intermedia (Intermediate Signal Throwing Event)


## Mensaje vs señal

| | Mensaje | Señal |
|---|---|---|
| Destino | **una** ejecución concreta (o arranca **un** proceso) | **todas** las que la esperan en el tenant (difusión) |
| Java | `runtimeService.messageEventReceived(nombre, executionId, vars)` | `runtimeService.signalEventReceivedWithTenantId(nombre, tenantId)` |
| Iniciar proceso | `runtimeService.startProcessInstanceByMessage(nombre)` | evento de inicio de señal: se inicia solo al difundirla |
| API REST del motor | `PUT /api/runtime/executions/{executionId}` `{"action":"messageEventReceived","messageName":"...","variables":[...]}` | `POST /api/runtime/signals?tenantId=tenant_1` `{"signalName":"...","tenantId":"tenant_1"}` |
| Iniciar por REST | `POST /api/runtime/process-instances?tenantId=tenant_1` `{"message":"...","tenantId":"tenant_1"}` | (la misma llamada de señal) |
| Buscar quién espera | `GET /api/runtime/executions?tenantId=tenant_1&processInstanceId=...&messageEventSubscriptionName=...` | — |

La API pública (`/api/enterprise`) **no** tiene endpoints de mensajes ni señales: se usa la API del motor (requiere la capacidad *tenant-admin* o *tenant-admin-api*, ver [API ReST](../API-ReST/apiRest.md)) o código Java.

## Definición en BPMN

```xml
<message id="msgPago" name="pagoRecibido"/>      <!-- se referencia por id, se envía por name -->
<signal  id="sigAlerta" name="alertaGlobal"/>

<!-- Espera un mensaje -->
<intermediateCatchEvent id="esperarPago"><messageEventDefinition messageRef="msgPago"/></intermediateCatchEvent>

<!-- Cancela la tarea si llega la señal (evento de límite interrumpidor) -->
<boundaryEvent id="porAlerta" attachedToRef="despachar" cancelActivity="true">
  <signalEventDefinition signalRef="sigAlerta"/>
</boundaryEvent>

<!-- Procesos que arrancan con una señal o un mensaje -->
<startEvent id="inicioSenal"><signalEventDefinition signalRef="sigAlerta"/></startEvent>
<startEvent id="inicioMsg"><messageEventDefinition messageRef="msgSolicitud"/></startEvent>
```

## Ejemplos probados en APS 24.4

> **Cómo desplegar estos BPMN a mano** (curl o App Designer) y qué necesita cada uno: [README → Cómo poner en funcionamiento un `.bpmn20.xml`](../README.md#cómo-poner-en-funcionamiento-un-bpmn20xml).

**Por API REST** — [`ejemplos/mensajesSenales.bpmn20.xml`](./ejemplos/mensajesSenales.bpmn20.xml) + [`ejemplos/probar.py`](./ejemplos/probar.py):

```
  OK    la instancia espera el mensaje pagoRecibido (aún sin tareas)
  OK    tras el mensaje se creó la tarea -> ['Despachar pedido']
  OK    el mensaje entregó la variable importe=250
  OK    la señal disparó el evento de límite: el pedido terminó (cancelado)
  OK    la misma señal inició atenderAlertaDemo (0 -> 1)
  OK    el pedido terminó por el camino finCancelado
  OK    el mensaje inició solicitudDemo:1:30040
  OK    señal sin ?tenantId en la URL -> HTTP 403
```

**Desde Java** — [`MensajeriaBean`](../EjemplosJava/README.md#mensajeriabean): un Service Task entrega el mensaje al pedido con cierto *business key* y otro difunde la señal.

### Lo comprobado

- Una sola señal hace **todo a la vez**: cancela la tarea con evento de límite y además inicia los procesos con evento de inicio de esa señal.
- En la API del motor, `tenantId` va **en la URL** (sin él: 403) y también en el body.
- En Java usa `signalEventReceivedWithTenantId`: las definiciones de APS viven en `tenant_1`.
- ⚠ El *business key* está sólo en la ejecución **raíz** y la suscripción al mensaje en una ejecución **hija**: `createExecutionQuery().processInstanceBusinessKey(bk).messageEventSubscriptionName(m)` devuelve vacío (y por REST, `POST /api/query/executions` con `processBusinessKey` + `messageEventSubscriptionName` también). Busca primero la instancia por business key y luego su ejecución por `processInstanceId`.

```bash
cd MessageAndSignals/ejemplos && APS_USER=... APS_PASS=... python probar.py
```
