# Mensajes y señales

El ``RuntimeService`` se utiliza para informar al motor de procesos que se ha recibido un mensaje o una señal.

## ¿Para qué sirven?

Los dos permiten que un proceso **reaccione a algo que pasa fuera de él**: un sistema externo, otro proceso o código Java avisa al motor y el proceso continúa, se cancela o arranca. Mientras espera, el proceso no consume nada, y el diagrama muestra claramente dónde depende de un evento externo (sin tareas manuales del tipo "Confirmar pago" ni temporizadores que consulten cada cierto tiempo).

La diferencia está en **a quién va dirigido el aviso**:

- **Mensaje** = carta con dirección: lo recibe **una sola** instancia (o arranca **un** proceso).
- **Señal** = alarma por megafonía: la reciben **todas** las instancias del tenant que la esperan, a la vez; quien la lanza no sabe quién escucha.

| Pregunta | Mensaje | Señal |
|---|---|---|
| ¿El aviso es para **un** caso concreto (un pedido, un cliente)? | ✅ | |
| ¿Afecta a **todos** los casos que lo esperan? | | ✅ |
| ¿Necesito saber si alguien lo recibió? | ✅ (si nadie lo espera no hay ejecución a la que enviarlo) | ❌ (si nadie escucha, se pierde sin error) |
| ¿Quiero arrancar exactamente **un** proceso? | ✅ (el nombre es único entre procesos) | arranca **todos** los que empiezan con esa señal |

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

## Casos típicos y cómo se implementan

| # | Caso | Construcción BPMN | Quién dispara | Ejemplo probado |
|---|---|---|---|---|
| 1 | Esperar una respuesta externa (el pago de **un** pedido) | evento intermedio de **captura de mensaje** | sistema externo por REST o Java | `pedidoDemo` en [`mensajesSenales.bpmn20.xml`](./ejemplos/mensajesSenales.bpmn20.xml) |
| 2 | Arrancar un proceso desde otro sistema (llega una solicitud del portal) | evento de **inicio de mensaje** | REST `{"message":...}` o `startProcessInstanceByMessage` | `solicitudDemo` en [`mensajesSenales.bpmn20.xml`](./ejemplos/mensajesSenales.bpmn20.xml) |
| 3 | Interrumpir **una** tarea concreta (el cliente retira su solicitud) | evento de **límite de mensaje** interrumpidor | REST o Java, a esa ejecución | [`solicitudCredito.bpmn20.xml`](./ejemplos/solicitudCredito.bpmn20.xml) |
| 4 | Comunicar dos procesos (facturación avisa al pedido) | captura de mensaje en el receptor + **service task Java** en el emisor | el otro proceso | [`MensajeriaBean`](../EjemplosJava/README.md#mensajeriabean) + `pedidoJava`/`pagadorJava` |
| 5 | Cancelación masiva (se cerró la convocatoria) | evento de **límite de señal** interrumpidor | REST, Java u otro proceso | `pedidoDemo` (límite `alertaGlobal`) |
| 6 | Cambio de condiciones generales (cambió la tasa: recalcular sin cancelar) | evento de **límite de señal NO interrumpidor** | otro proceso con **lanzamiento de señal** | [`solicitudCredito`](./ejemplos/solicitudCredito.bpmn20.xml) + [`anuncioCambioTasa`](./ejemplos/anuncioCambioTasa.bpmn20.xml) |
| 7 | Disparar varios procesos a la vez (alerta de seguridad) | evento de **inicio de señal** en cada proceso | cualquiera que lance la señal | `atenderAlertaDemo` (una señal también inició un 2.º proceso con la misma señal de inicio) |

### 1. Esperar una respuesta externa

```
  ○ ──▶ (✉) Esperar pago ──▶ [Despachar pedido] ──▶ ●
```

```xml
<intermediateCatchEvent id="esperarPago"><messageEventDefinition messageRef="msgPago"/></intermediateCatchEvent>
```

La instancia queda parada en el evento. Para avisarle, busca su ejecución y entrégale el mensaje (puede llevar variables):

```
GET /api/runtime/executions?tenantId=tenant_1&processInstanceId=<id>&messageEventSubscriptionName=pagoRecibido
PUT /api/runtime/executions/<executionId>
    {"action":"messageEventReceived","messageName":"pagoRecibido","variables":[{"name":"importe","value":250}]}
```

### 2. Arrancar un proceso con un mensaje

Ver [Proceso que arranca con un mensaje](#proceso-que-arranca-con-un-mensaje).

### 3. Interrumpir una tarea concreta (límite de mensaje)

```
  ○ ──▶ [Evaluar crédito] ──────────────▶ ● Evaluada
              ⦿✉ Cliente retira
              └────────────────────────▶ ● Retirada
```

```xml
<boundaryEvent id="porRetiro" attachedToRef="evaluar" cancelActivity="true">
  <messageEventDefinition messageRef="msgRetiro"/>
</boundaryEvent>
```

Se envía igual que en el caso 1, a la ejecución de **esa** solicitud. **Comprobado:** la solicitud A terminó por "Retirada" y la B, en la misma tarea, no se enteró.

### 4. Comunicar dos procesos

Un evento intermedio de *lanzamiento* de mensaje **no entrega nada**. **Comprobado:** el proceso que lo lanza termina sin error, pero el pedido sigue esperando `pagoRecibido`. Por eso el emisor lo envía con un **service task** que llama a `RuntimeService`. Con las listas blancas activas, `${runtimeService...}` en una expresión está bloqueado, así que se hace con un bean propio ([`MensajeriaBean.notificarPago`](../EjemplosJava/README.md#mensajeriabean)):

```xml
<serviceTask id="pagar" activiti:expression="${mensajeriaBean.notificarPago(pedidoId, importe)}" activiti:resultVariable="entregado"/>
```

El bean busca el pedido por *business key*, luego la ejecución que espera `pagoRecibido`, y devuelve `false` si nadie lo espera.

El mismo bean también **inicia** un proceso por mensaje (`iniciarPorMensaje`, probado con `iniciadorJava` → `solicitudJava`).

**Sin compilar Java: script task en groovy.** Desde un script se llega al `RuntimeService` del motor y se hacen los mismos pasos. **Comprobado:** entregó el mensaje al pedido `P-777` (pasó a "Despachar pedido" con `importe=99`) e inició `solicitudDemo`:

```groovy
def rs = org.activiti.engine.impl.context.Context.getProcessEngineConfiguration().getRuntimeService()
// entregar a una instancia en espera
def pi = rs.createProcessInstanceQuery().processInstanceBusinessKey(pedidoId).singleResult()
def ex = pi == null ? null : rs.createExecutionQuery().processInstanceId(pi.getId())
                                 .messageEventSubscriptionName('pagoRecibido').singleResult()
if (ex != null) rs.messageEventReceived('pagoRecibido', ex.getId(), [importe: 99])
// iniciar un proceso por mensaje, en el tenant de esta ejecución
rs.startProcessInstanceByMessageAndTenantId('nuevaSolicitud', [origen: 'script'], execution.getTenantId())
```

Es útil para prototipos; para producción es mejor el bean Java (se prueba, se versiona y no depende de clases internas `impl` del motor).

### 5. Cancelación masiva (límite de señal interrumpidor)

```
  ○ ──▶ (✉) ──▶ [Despachar pedido] ──────▶ ● Despachado
                     ⦿△ alertaGlobal
                     └─────────────────────▶ ● Cancelado por alerta
```

```xml
<boundaryEvent id="porAlerta" attachedToRef="despachar" cancelActivity="true">
  <signalEventDefinition signalRef="sigAlerta"/>
</boundaryEvent>
```

```
POST /api/runtime/signals?tenantId=tenant_1   {"signalName":"alertaGlobal","tenantId":"tenant_1"}
```

### 6. Cambio de condiciones sin cancelar (límite de señal NO interrumpidor + lanzamiento)

```
  ○ ──▶ [Evaluar crédito] ──────────────▶ ● Evaluada
              ⦿△ Cambio de tasa (borde discontinuo: no interrumpe)
              └──▶ [Recalcular cuota] ──▶ ● Cuota recalculada

  ○ ──▶ (▲) Anunciar cambio de tasa ──▶ ●        ← otro proceso LANZA la señal
```

```xml
<!-- receptor: cancelActivity="false" -> la tarea sigue activa y además se ejecuta la otra rama -->
<boundaryEvent id="porTasa" attachedToRef="evaluar" cancelActivity="false">
  <signalEventDefinition signalRef="sigTasa"/>
</boundaryEvent>

<!-- emisor: evento intermedio de LANZAMIENTO de señal, sin REST ni Java -->
<intermediateThrowEvent id="anunciar"><signalEventDefinition signalRef="sigTasa"/></intermediateThrowEvent>
```

**Comprobado:** al iniciar `anuncioCambioTasa`, la solicitud B calculó `cuota = 220` y su tarea "Evaluar crédito" siguió activa.

### 7. Disparar varios procesos a la vez (inicio de señal)

Cada proceso que deba arrancar pone un evento de inicio de señal con el mismo nombre:

```xml
<startEvent id="inicioSenal"><signalEventDefinition signalRef="sigAlerta"/></startEvent>
```

**Comprobado:** con dos procesos distintos que empiezan con `alertaGlobal`, una sola señal creó una instancia de cada uno (y además canceló los pedidos del caso 5).

## Proceso que arranca con un mensaje

```
   ┌───┐          ┌──────────────────┐          ┌───┐
   │ ✉ │ ───────▶ │ Revisar solicitud│ ───────▶ │ ● │
   └───┘          └──────────────────┘          └───┘
 inicio de        tarea de usuario               fin
 mensaje "nuevaSolicitud"   (círculo de borde fino con un sobre vacío)
```

```xml
<message id="msgSolicitud" name="nuevaSolicitud"/>   <!-- fuera del <process> -->

<process id="solicitudDemo" name="Solicitud por mensaje" isExecutable="true">
  <startEvent id="inicioMsg">
    <messageEventDefinition messageRef="msgSolicitud"/>   <!-- referencia el id; se envía por el name -->
  </startEvent>
  <sequenceFlow id="h1" sourceRef="inicioMsg" targetRef="revisar"/>
  <userTask id="revisar" name="Revisar solicitud"/>
  <sequenceFlow id="h2" sourceRef="revisar" targetRef="finSol"/>
  <endEvent id="finSol"/>
</process>
```

En el modeler: define el mensaje en las propiedades del proceso (*Message definitions*: id `msgSolicitud`, nombre `nuevaSolicitud`), arrastra un *Message start event* desde *Start Events* y elige el mensaje en *Message reference*.

No se inicia por clave: se envía el mensaje y el motor busca qué proceso arranca con él.

```
POST /api/runtime/process-instances?tenantId=tenant_1
{"message":"nuevaSolicitud","tenantId":"tenant_1","variables":[{"name":"origen","value":"api"}]}
```

En Java: `runtimeService.startProcessInstanceByMessage("nuevaSolicitud", variables)`.

### ¿Por qué no se pueden desplegar dos procesos con el mismo mensaje de inicio?

Al desplegar, el motor registra en la tabla `ACT_RU_EVENT_SUBSCR` una **suscripción** por cada evento de inicio de mensaje o de señal. Consultada tras desplegar el ejemplo:

```
 event_type_ |  event_name_   |       proc_def_id_        | execution_id_ | tenant_id_
-------------+----------------+---------------------------+---------------+------------
 message     | nuevaSolicitud | solicitudDemo:1:40898     |               | tenant_1
 signal      | alertaGlobal   | atenderAlertaDemo:1:40897 |               | tenant_1
```

- Un mensaje tiene **un único destinatario**: `{"message":"nuevaSolicitud"}` debe saber exactamente qué proceso iniciar. Si dos procesos distintos estuvieran suscritos al mismo nombre, el arranque sería ambiguo. Por eso el motor **rechaza el segundo despliegue** (HTTP 500): `there already is a message event subscription for the message with name 'nuevaSolicitud'`.
- Una **nueva versión del mismo proceso** sí se despliega: reemplaza la suscripción (tras redesplegar, la fila pasó a `solicitudDemo:2:40905`) y el mensaje inicia la última versión.
- Las **señales** son de difusión, así que no hay ambigüedad: dos procesos distintos con la misma señal de inicio se despliegan sin problema y la señal arranca los dos.
- Las suscripciones de mensajes de **captura y de límite** (casos 1 y 3) son de cada ejecución en espera (`execution_id_` relleno), así que el mismo nombre puede usarse en muchas instancias y procesos.

Si necesitas que dos procesos reaccionen al mismo aviso de inicio, usa una **señal**, o un mensaje distinto para cada uno.

## Ejemplos probados en APS 24.4

> **Cómo desplegar estos BPMN a mano** (curl o App Designer) y qué necesita cada uno: [README → Cómo poner en funcionamiento un `.bpmn20.xml`](../README.md#cómo-poner-en-funcionamiento-un-bpmn20xml).

**Por API REST y BPMN** — [`mensajesSenales`](./ejemplos/mensajesSenales.bpmn20.xml), [`solicitudCredito`](./ejemplos/solicitudCredito.bpmn20.xml) y [`anuncioCambioTasa`](./ejemplos/anuncioCambioTasa.bpmn20.xml) + [`ejemplos/probar.py`](./ejemplos/probar.py):

```
  OK    la instancia espera el mensaje pagoRecibido (aún sin tareas)
  OK    tras el mensaje se creó la tarea -> ['Despachar pedido']
  OK    el mensaje entregó la variable importe=250
  OK    la señal disparó el evento de límite: el pedido terminó (cancelado)
  OK    la misma señal inició atenderAlertaDemo (0 -> 1)
  OK    el pedido terminó por el camino finCancelado
  OK    el mensaje inició solicitudDemo:1:30040
  OK    otro proceso con el mismo mensaje de inicio nuevaSolicitud -> HTTP 500 (rechazado)
  OK    señal sin ?tenantId en la URL -> HTTP 403
Casos típicos sobre una tarea (solicitudCredito + anuncioCambioTasa)
  OK    mensaje de límite: la solicitud A se canceló por el camino Retirada
  OK    la solicitud B no se enteró (el mensaje va a una sola ejecución)
  OK    señal lanzada por otro proceso: B recalculó cuota=220.0
  OK    límite no interrumpidor: la tarea de B sigue activa
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
