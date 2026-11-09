# Ejemplos Java para APS

Proyecto Maven con una clase por cada mecanismo de extensión Java que se ve en la capacitación. Todas están **probadas en APS 24.4.0** con [`probar.py`](./probar.py) y el proceso [`procesos/javaDemo.bpmn20.xml`](./procesos/javaDemo.bpmn20.xml).

| Clase | Mecanismo | Cómo se usa en el BPMN / modeler | Sección |
|---|---|---|---|
| [`CalcularTotalDelegate`](#calculartotaldelegate) | `JavaDelegate` + field injection | Service Task → **Class** + **Class fields** | [Service Task](../ServiceTask/serviceTask.md) |
| [`ClienteService`](#clienteservice) | Bean de Spring en expresión | Service Task → **Expression** `${clienteService.categoria(total)}` | [Service Task](../ServiceTask/serviceTask.md) |
| [`AuditoriaDelegate`](#auditoriadelegate) | `JavaDelegate` como bean (`@Autowired`) | Service Task → **Delegate expression** `${auditoriaDelegate}` | [Service Task](../ServiceTask/serviceTask.md) |
| [`InicioExecutionListener`](#inicioexecutionlistener) | `ExecutionListener` | **Execution listeners** → Class | [Listeners](../Listeners/listeners.md) |
| [`PrioridadTaskListener`](#prioridadtasklistener) | `TaskListener` | User Task → **Task listeners** → Class | [Listeners](../Listeners/listeners.md) |
| [`MensajeriaBean`](#mensajeriabean) | `RuntimeService`: mensajes y señales | Service Task → **Expression** | [Mensajes y señales](../MessageAndSignals/messageAndSignals.md) |
| [`CapacitacionApiEndpoint`](#capacitacionapiendpoint) | Endpoint REST en la API pública | `GET /activiti-app/api/enterprise/capacitacion/resumen/{key}` | [Endpoints ReST](../CustomEndpointReST/customEndPointRest.md) |

## Estructura y paquetes

```
EjemplosJava/
├── pom.xml                      dependencia activiti-app-logic (provided), suite.version 24.4.0
├── procesos/javaDemo.bpmn20.xml procesos que usan las clases
├── probar.py                    prueba automática contra APS
└── src/main/java/
    ├── com/activiti/extension/bean/   beans de Spring (APS los detecta solo)
    │   ├── ClienteService.java
    │   ├── AuditoriaDelegate.java
    │   └── MensajeriaBean.java
    ├── com/activiti/extension/api/    endpoints REST bajo /api (Basic auth)
    │   └── CapacitacionApiEndpoint.java
    └── com/training/aps/              clases normales (activiti:class), cualquier paquete
        ├── delegate/CalcularTotalDelegate.java
        └── listener/{InicioExecutionListener, PrioridadTaskListener}.java
```

APS hace *component scan* de `com.activiti.extension.bean`, `com.activiti.extension.api` y `com.activiti.extension.rest` (UI). Las clases usadas con `activiti:class` no son beans: pueden estar en cualquier paquete, pero **no** admiten `@Autowired`.

## Compilar y desplegar

> **Cómo desplegar estos BPMN a mano** (curl o App Designer) y qué necesita cada uno: [README → Cómo poner en funcionamiento un `.bpmn20.xml`](../README.md#cómo-poner-en-funcionamiento-un-bpmn20xml).

```bash
cd EjemplosJava
mvn package            # o mvn -o package si las dependencias ya están en ~/.m2
# resultado: target/training-aps-ejemplos.jar
```

Las dependencias `com.activiti` están en el Nexus enterprise de Alfresco y requieren credenciales ([Configuración Maven](../ConfigurationMavenProject/mavenProject.md)).

**APS en contenedor.** Monta el jar en `WEB-INF/lib` de la aplicación:

```yaml
    volumes:
      - ./activiti-app/webapps/activiti-app/WEB-INF/lib/training-aps-ejemplos.jar:/usr/local/tomcat/webapps/activiti-app/WEB-INF/lib/training-aps-ejemplos.jar
```

Después **recrea** el contenedor: un simple reinicio no basta tras cambiar un archivo montado.

**Tomcat clásico.** Copia el jar a `tomcat/webapps/activiti-app/WEB-INF/lib/` y reinicia.

**Probar:**

```bash
APS_USER=admin@app.activiti.com APS_PASS=<clave> python probar.py
```

```
javaDemo: delegate por clase, bean en expresión, delegateExpression y listeners
  OK    CalcularTotalDelegate (fields tasa=0.18) -> total=1180.0
  OK    ClienteService.categoria(total) -> ORO
  OK    AuditoriaDelegate (@Autowired HistoryService) -> [0, 1]
  OK    InicioExecutionListener -> start:proceso > start:calcular > end:calcular
  OK    PrioridadTaskListener -> prioridades 100/50, vence 2026-11-06T21:09:22.566Z, local [... 'urgente' ...]
Endpoint REST propio
  OK    GET /api/enterprise/capacitacion/resumen/javaDemo -> {'enCurso': 0, 'usuario': 'admin@app.activiti.com', 'terminadas': 2, ...}
MensajeriaBean: mensaje y señal desde Java
  OK    notificarPago() encontró la ejecución y entregó el mensaje
  OK    el pedido avanzó a Despachar con importe=250
  OK    sin ejecución esperando -> entregado=false
  OK    alertar(tenantId) disparó el evento de límite: el pedido terminó
  OK    iniciarPorMensaje() creó la instancia 42731 de solicitudJava (origen=java)
Todo OK
```

Se probó con las listas blancas desactivadas y también con `beans.whitelisting.enabled=true` + `el.whitelisting.enabled=true` (valores por defecto del producto). Los beans de `com.activiti.extension.bean` se consideran permitidos: **no hace falta tocar `beans-whitelist.conf`**. Pero con `el.whitelisting.enabled=true` y `call-whitelist.conf` vacío, **`alertadorJava` falla** al iniciar (HTTP 500, `Unknown property used in expression: ${mensajeriaBean.alertar(execution.tenantId)}`): leer `execution.tenantId` es una llamada a `DelegateExecution` (`iniciadorJava` usa lo mismo). Al añadir `org.activiti.engine.delegate.DelegateExecution.*` a `call-whitelist.conf` pasa todo (comprobado el 2026-11-07).

---

## CalcularTotalDelegate

`com.training.aps.delegate.CalcularTotalDelegate` · [código](./src/main/java/com/training/aps/delegate/CalcularTotalDelegate.java)

**Qué hace:** lee la variable `monto`, aplica la tasa recibida como campo y guarda el total en la variable cuyo nombre también llega como campo.

```java
public class CalcularTotalDelegate implements JavaDelegate {

    private Expression tasa;            // el motor los rellena por reflexión (mismo nombre que el field del BPMN)
    private Expression variableSalida;

    @Override
    public void execute(DelegateExecution execution) {
        double monto = ((Number) execution.getVariable("monto")).doubleValue();
        double t = Double.parseDouble(String.valueOf(tasa.getValue(execution)));
        String salida = variableSalida != null ? String.valueOf(variableSalida.getValue(execution)) : "total";
        execution.setVariable(salida, Math.round(monto * (1 + t) * 100) / 100.0);
    }
}
```

**En el modeler:** Service Task → *Class* = `com.training.aps.delegate.CalcularTotalDelegate`; *Class fields*: `tasa` = `0.18`, `variableSalida` = `total`.

```xml
<serviceTask id="calcular" activiti:class="com.training.aps.delegate.CalcularTotalDelegate">
  <extensionElements>
    <activiti:field name="tasa" stringValue="0.18"/>
    <activiti:field name="variableSalida" stringValue="total"/>
  </extensionElements>
</serviceTask>
```

**A tener en cuenta**
- El motor crea **una sola instancia por definición** y la reutiliza en todas las ejecuciones: no guardes estado en atributos (sólo los `Expression` inyectados).
- Los campos se declaran como `Expression` y se evalúan con `getValue(execution)`: así también admiten `${...}`.
- No es un bean de Spring: `@Autowired` no funciona aquí (usa [AuditoriaDelegate](#auditoriadelegate)).
- Con `class.whitelisting.enabled=true`, la clase debe estar en `whitelisted-classes.conf`.

## ClienteService

`com.activiti.extension.bean.ClienteService` · [código](./src/main/java/com/activiti/extension/bean/ClienteService.java)

**Qué hace:** clasifica el pedido en ORO / PLATA / BRONCE según el total. El valor devuelto se guarda con *result variable*.

```java
@Component("clienteService")
public class ClienteService {
    public String categoria(Number total) {
        double t = total.doubleValue();
        return t >= 1000 ? "ORO" : t >= 300 ? "PLATA" : "BRONCE";
    }
}
```

**En el modeler:** Service Task → *Expression* = `${clienteService.categoria(total)}`, *Result variable* = `categoria`.

**A tener en cuenta**
- El nombre del `@Component` es el que se usa en la expresión.
- Las expresiones admiten variables del proceso por nombre (`total`) y los objetos `execution` (en listeners de tarea, también `task`).
- Recibe `Number`, no `double`: las variables numéricas pueden llegar como `Integer`, `Long` o `Double` según cómo se crearon.

## AuditoriaDelegate

`com.activiti.extension.bean.AuditoriaDelegate` · [código](./src/main/java/com/activiti/extension/bean/AuditoriaDelegate.java)

**Qué hace:** con el `HistoryService` inyectado, cuenta las instancias anteriores de la misma definición y las guarda en `instanciasPrevias`.

```java
@Component("auditoriaDelegate")
public class AuditoriaDelegate implements JavaDelegate {

    @Autowired
    private HistoryService historyService;

    @Override
    public void execute(DelegateExecution execution) {
        long previas = historyService.createHistoricProcessInstanceQuery()
                .processDefinitionId(execution.getProcessDefinitionId())
                .count();
        execution.setVariable("instanciasPrevias", previas);
    }
}
```

**En el modeler:** Service Task → *Delegate expression* = `${auditoriaDelegate}` (el motor llama a `execute`).

**A tener en cuenta**
- Combina lo mejor de los dos anteriores: estructura de `JavaDelegate` + inyección de Spring.
- **Comprobado:** la instancia actual **no** aparece en la consulta (todavía no se ha guardado en BD en esta transacción). La primera instancia cuenta 0 y la segunda 1.
- Usar un servicio desde Java no pasa por las listas blancas de expresiones; en una expresión, `${historyService...}` sí necesita `beans-whitelist.conf` y `call-whitelist.conf` (ver [Service Task](../ServiceTask/serviceTask.md#lo-comprobado-en-aps-244)).

## InicioExecutionListener

`com.training.aps.listener.InicioExecutionListener` · [código](./src/main/java/com/training/aps/listener/InicioExecutionListener.java)

**Qué hace:** acumula en la variable `trazaListener` el evento y la actividad de cada notificación, para ver el orden en que el motor los dispara.

```java
public class InicioExecutionListener implements ExecutionListener {
    @Override
    public void notify(DelegateExecution execution) {
        String previo = (String) execution.getVariable("trazaListener");
        // En el start/end del PROCESO no hay actividad actual: getCurrentActivityId() devuelve null
        String actividad = execution.getCurrentActivityId() == null ? "proceso" : execution.getCurrentActivityId();
        String paso = execution.getEventName() + ":" + actividad;
        execution.setVariable("trazaListener", previo == null ? paso : previo + " > " + paso);
    }
}
```

**En el BPMN** está enganchado al `start` del proceso y al `start`/`end` del service task *calcular*. Resultado comprobado: `start:proceso > start:calcular > end:calcular`.

**A tener en cuenta**
- En el evento del **proceso**, `getCurrentActivityId()` es `null`.
- ⚠ En el evento `end` del **proceso** no crees variables nuevas: en PostgreSQL da HTTP 500 `violates foreign key constraint "act_fk_var_exe"`, porque la ejecución se borra en la misma transacción. Actualizar una variable que ya existe sí funciona.

## PrioridadTaskListener

`com.training.aps.listener.PrioridadTaskListener` · [código](./src/main/java/com/training/aps/listener/PrioridadTaskListener.java)

**Qué hace:** al crearse la tarea pone prioridad y vencimiento según la categoría del cliente, y deja una variable **local** de la tarea.

```java
public class PrioridadTaskListener implements TaskListener {
    private static final long DIA = 24L * 60 * 60 * 1000;

    @Override
    public void notify(DelegateTask task) {
        boolean oro = "ORO".equals(task.getVariable("categoria"));
        task.setPriority(oro ? 100 : 50);
        task.setDueDate(new Date(System.currentTimeMillis() + (oro ? 1 : 3) * DIA));
        task.setVariableLocal("reglaAplicada", oro ? "urgente" : "normal");
    }
}
```

**En el modeler:** User Task → *Task listeners* → evento `create`, *Class* = `com.training.aps.listener.PrioridadTaskListener`.

**A tener en cuenta**
- `task.getVariable` busca en la tarea y luego en el proceso; `setVariableLocal` deja la variable sólo en la tarea (se consulta con `GET runtime/tasks/{id}/variables?scope=local`).
- Eventos disponibles: `create`, `assignment`, `complete`, `delete`.

## MensajeriaBean

`com.activiti.extension.bean.MensajeriaBean` · [código](./src/main/java/com/activiti/extension/bean/MensajeriaBean.java)

**Qué hace:** entrega el mensaje `pagoRecibido` al pedido con cierto business key, inicia un proceso por mensaje y difunde la señal `alertaGlobal`.

```java
public boolean notificarPago(String pedidoId, Number importe) {
    ProcessInstance pi = runtimeService.createProcessInstanceQuery()
            .processInstanceBusinessKey(pedidoId)
            .singleResult();
    if (pi == null) return false;
    Execution ex = runtimeService.createExecutionQuery()
            .processInstanceId(pi.getId())
            .messageEventSubscriptionName("pagoRecibido")
            .singleResult();
    if (ex == null) return false;
    runtimeService.messageEventReceived("pagoRecibido", ex.getId(), Map.of("importe", importe));
    return true;
}

public String iniciarPorMensaje(String mensaje, String tenantId) {
    return runtimeService.startProcessInstanceByMessageAndTenantId(mensaje, Map.of("origen", "java"), tenantId).getId();
}

public void alertar(String tenantId) {
    runtimeService.signalEventReceivedWithTenantId("alertaGlobal", tenantId);
}
```

**En el modeler:** Service Task → *Expression* = `${mensajeriaBean.notificarPago(pedidoId, importe)}` con *Result variable* `entregado`; `${mensajeriaBean.iniciarPorMensaje('nuevaSolicitudJava', execution.tenantId)}` (proceso `iniciadorJava`: arranca `solicitudJava`, que empieza con ese mensaje); y `${mensajeriaBean.alertar(execution.tenantId)}`.

**A tener en cuenta**
- ⚠ **Comprobado:** `createExecutionQuery().processInstanceBusinessKey(x).messageEventSubscriptionName(y)` **no devuelve nada**. El business key está en la ejecución raíz y la suscripción en una ejecución hija, así que hay que buscar en dos pasos, como arriba.
- En APS los procesos viven en un tenant (`tenant_1`): usa `signalEventReceivedWithTenantId`; la señal alcanza a todas las instancias del tenant (eventos de límite, de captura y de inicio de señal).

## CapacitacionApiEndpoint

`com.activiti.extension.api.CapacitacionApiEndpoint` · [código](./src/main/java/com/activiti/extension/api/CapacitacionApiEndpoint.java)

**Qué hace:** endpoint propio de la API pública que devuelve el usuario que llama y cuántas instancias en curso y terminadas tiene un proceso.

```java
@RestController
@RequestMapping("/enterprise/capacitacion")
public class CapacitacionApiEndpoint {

    @Autowired
    private HistoryService historyService;

    @GetMapping("/resumen/{key}")
    public Map<String, Object> resumen(@PathVariable("key") String key) {
        User u = SecurityUtils.getCurrentUserObject();
        long abiertas = historyService.createHistoricProcessInstanceQuery().processDefinitionKey(key).unfinished().count();
        long cerradas = historyService.createHistoricProcessInstanceQuery().processDefinitionKey(key).finished().count();
        return Map.of("usuario", u.getEmail(), "proceso", key, "enCurso", abiertas, "terminadas", cerradas);
    }
}
```

```bash
curl -u "$APS_USER:$APS_PASS" "$APS_BASE/api/enterprise/capacitacion/resumen/javaDemo"
# {"enCurso":0,"usuario":"admin@app.activiti.com","terminadas":2,"proceso":"javaDemo"}
```

**A tener en cuenta**
- Paquete `com.activiti.extension.api` → se publica bajo `/activiti-app/api/` con Basic auth, igual que la API pública. El paquete `com.activiti.extension.rest` corresponde a la API interna de la UI (cookies), según la [documentación](../CustomEndpointReST/customEndPointRest.md).
- La seguridad no filtra datos: este endpoint cuenta instancias de **todos** los usuarios. Si sólo debe verlo un administrador, compruébalo en el código.
