# Listeners

Un listener es una operación que escucha eventos activados por el motor de proceso y ejecuta código Java externo o evalúa una expresión cuando ocurre un evento específico. Un listener de cualquier tipo es una pieza de lógica que se puede utilizar con fines técnicos. Los listener se adjuntan a varios puntos del proceso BPMN que coinciden con eventos específicos.

Los listener están configurados para escuchar un evento o eventos específicos, como el ``inicio de un proceso`` o la ``finalización de una tarea``, y luego ejecutar alguna operación que el evento ha desencadenado.

Alfresco Activiti ofrece varios tipos diferentes de oyentes que pueden implementarse para lograr sus objetivos. Estos distintos tipos de listeners le permiten escuchar eventos específicos y utilizar lenguajes de programación de eventos para su lógica. D


## Execution Listeners

Los "execution listeners" permiten ejecutar código cuando ocurren eventos durante la ejecución de un proceso. Estos eventos pueden originarse a partir de tareas, transiciones e incluso del propio proceso. Un desarrollador que escriba sus listeners utilizando código Java debe implementar la interfaz de "execution listener" y luego su clase Java puede ser configurada como un "execution listener" dentro del Diseñador de Procesos BPMN.

Dentro del diseñador de procesos, puedes seleccionar el evento específico al que tu listener debe escuchar, los cuales son eventos de inicio, fin o toma.

El evento de inicio se dispara solo al iniciar un proceso o tarea, y el evento de fin se dispara al completar los mismos. Sin embargo, el evento de toma es único, ya que solo se refiere a transiciones; por lo tanto, la tarea o el proceso solo emiten eventos de inicio y fin, mientras que las transiciones solo emiten eventos de toma.

Los eventos que se pueden capturar son:

- Inicio y final de una instancia de proceso.

- Tomando una transición(en las flechas).

- Inicio y fin de una actividad.

- Inicio y final de un gateway.

- Inicio y fin de intermediate events.

- Finalizar un evento de inicio o iniciar un evento de finalización.

![execution listeners](./img/executionListenersOp.png)


### Demostración Java class

El executionListener va a estar definido en el evento de partida.

```java
package pe.com.domain.delegate;

import org.activiti.engine.delegate.ExecutionListener;
import org.activiti.bpmn.model.FlowElement;
import org.activiti.engine.delegate.DelegateExecution;
import org.activiti.engine.delegate.Expression;

public class JavaExecutionListener implements ExecutionListener{
    private Expression param1;
    @Override
    public void notify(DelegateExecution delegateExecution){    

        final String currentActivityId = delegateExecution.getCurrentActivityId();
        String activityName = null;
        FlowElement FlowElement = delegateExecution.getCurrentFlowElement();
        activityName = FlowElement.getName();
        System.out.println("Starting the '" + activityName + "' -> " + currentActivityId + ", activity. param1: " + param1.getValue(delegateExecution) );
    }
}
```

![execution listener with java class](./img/executionListenerJavaClass2.png)


### Demostración Spring class

El executionListener va a estar definido en el evento final.

```java
package com.activiti.extension.bean;

import org.activiti.engine.delegate.ExecutionListener;
import org.activiti.bpmn.model.FlowElement;
import org.activiti.engine.delegate.DelegateExecution;
import org.springframework.stereotype.Component;

@Component("myExecutionListener")
public class SpringExecutionListener implements ExecutionListener{
    @Override
    public void notify(DelegateExecution delegateExecution){
        final String currentActivityId = delegateExecution.getCurrentActivityId();
        String activityName = null;
        FlowElement FlowElement = delegateExecution.getCurrentFlowElement();
        activityName = FlowElement.getName();
        System.out.println("Ending the '" + activityName + "' -> " + currentActivityId + ", activity." );
    }

    public void writeMessage(DelegateExecution delegateExecution, String message){
        final String currentActivityId = delegateExecution.getCurrentActivityId();
        String activityName = null;
        FlowElement FlowElement = delegateExecution.getCurrentFlowElement();
        activityName = FlowElement.getName();
        System.out.println(activityName +" with id : " + currentActivityId + " says, '" + message + "'");
    }
}
```
![execution listener with Spring class](./img/executionListenerSpringClass.png)



En el flujo de secuencia se define el evento ``take`` o ``Adquirir`` y utilizamos writeMessage que es un metodo definido en un Spring bean. 

![execution listener with take Event](./img/executionListenerTakeEvent.png)

```
${myExecutionListener.writeMessage(execution," Transition ")}
```
[proceso implementado](./processes/ExecutionListeners.bpmn20.xml)

## Task Listeners

Los "task listeners" presentan algunas diferencias: solo pueden aplicarse a una tarea de usuario. Al programar en Java, deben implementar la interfaz de "task listener". Puedes considerar los "task listeners" como una especie de listener especializado que atiende a un conjunto específico de eventos.

Los "task listeners" pueden escuchar cuatro tipos de eventos:

create (crear) :  Ocurre cuando la tarea ha sido creada y todas las propiedades de la tarea están establecidas.
assignment (asignación) : Ocurre cuando la tarea se asigna a un usuario, pero antes del evento create.
complete (completar) :   Ocurre cuando la tarea se completa y justo antes de ser eliminada.
delete (eliminar) : Ocurre justo antes de que la tarea vaya a ser eliminada.

![Task listeners](./img/taskListenersOp.png)

### Demostración

```java
package com.activiti.extension.bean;

import org.activiti.engine.delegate.DelegateTask;
import org.activiti.engine.delegate.TaskListener;
import org.springframework.stereotype.Component;

@Component("myTaskListener")
public class SpringTaskListener implements TaskListener{
    @Override
    public void notify(DelegateTask delegateTask){
        final String assignee = delegateTask.getAssignee();
        final String name = delegateTask.getName();
        System.out.println( name + "has been assigned to ID '"+ assignee + '\'');
    }

    public void writeEvent(DelegateTask delegateTask){
        System.out.println( delegateTask.getName()+ " event '" + delegateTask.getEventName() + '\'');
    }
}
```

![task Listener Assignment](./img/taskListenerAssignment.png)

![task Listener otros eventos](./img/taskListenerOtherEvents.png)

[proceso implementado](./processes/taskListeners.bpmn20.xml)

## Otros Listeners

Si bien la mayoría de los problemas pueden resolverse utilizando "execution listeners" o "task listeners", Alfresco Activiti admite otros tipos de listeners que cubren casos de uso más específicos.

Por ejemplo, existen los "script listeners", los listeners de inicio de sesión y cierre de sesión ("log-in y log-out listeners"), así como los listeners de eventos del motor de procesos ("process engine event listeners").

### Listeners de scripts (Script Listeners)

Alfresco Activiti admite el uso de "script listeners" tanto para "execution listeners" como para "task listeners". Esto se logra utilizando la clase "script execution listener" y la clase "script task listener"

Estas clases requieren un campo de "script" y un campo de "language", que contienen el código del script y el tipo de lenguaje, respectivamente. Opcionalmente, se puede especificar un nombre de variable de retorno que contendrá el valor devuelto por el script.

#### Script Task Listener

![Execution listeners with ScriptTaskListener](./img/taskListenerWithScriptTaskListener.png)

``
org.activiti.engine.impl.bpmn.listener.ScriptTaskListener
``

```javascript
print("Script Task Listener Event: " + task.eventName);
```

Ejecución de Script

![Script en task listener](./img/ScriptTaskListener.png)
``
org.activiti.engine.impl.bpmn.listener.ScriptTaskListener
``

```javascript
print("Script Task Listener Event: " + task.eventName);
```

[proceso implementado](./processes/ScriptTaskListener.bpmn20.xml)

#### Script Execution Listener

![Script execution listener](./img/ScriptExecutionListener.png)

``
org.activiti.engine.impl.bpmn.listener.ScriptExecutionListener
``

```javascript
print("Script Execution Listener Event: " + execution.eventName );
```





### Listeners de inicio y cierre de sesión (Log-in y Log-out Listeners)

Estos listeners especializados permiten recibir una notificación cuando un usuario inicia o cierra sesión en Alfresco Activiti. La implementación del método correspondiente recibirá un objeto de usuario que representa al usuario que ha iniciado o cerrado sesión. 


### **Interfaz de usuario vs Programación**

revisaremos los diferentes enfoques que puedes tomar para implementar listeners en Alfresco Activiti. Como ya sabes, existen muchos tipos diferentes de listeners disponibles para construir y extender tu proceso BPMN. Sin embargo, solo hay dos paradigmas distintos para crearlos: programando en Java o utilizando la interfaz de usuario de Alfresco Activiti. 

Los listeners pueden agregarse a las entidades BPMN desde el editor visual de Alfresco Activiti. Simplemente selecciona la propiedad **execution listeners** o **task listeners** de cualquier entidad BPMN para abrir un cuadro de diálogo donde puedes configurarlo.

Ahí puedes agregar uno o más listeners que escucharán ciertos eventos que ocurren durante el ciclo de vida de la entidad.

Cuando se activa el evento, el listener ejecutará una acción personalizada, la cual también puedes definir en este diálogo. El código de tu acción personalizada puede escribirse como una **expresión** o a través de un **script listener**.

### **Beneficios del enfoque basado en la UI**
- Ideal para operaciones pequeñas que requieren de una a tres líneas de código.
- No es necesario desplegar código ni reiniciar el servidor.
- Permite una implementación rápida.

### **Desventajas del enfoque basado en la UI**
- Las tareas más grandes son difíciles de crear y mantener.
- Es complicado depurar problemas a medida que aumenta la complejidad.
- No permite realizar pruebas unitarias.

---

### **Programación en Java**
También puedes escribir el código de tu listener personalizado dentro de una clase y empaquetarlo en un **archivo JAR**, que será cargado por Alfresco Activiti en el arranque. Aunque los listeners pueden crearse programando en Java, sigue siendo necesario usar la interfaz de usuario de Alfresco Activiti para adjuntar el listener Java a una entidad BPMN. Sin embargo, el código personalizado se escribe como una **clase Java** dentro de un **IDE**, en lugar de hacerlo directamente en la interfaz de usuario de Alfresco Activiti. 

Los únicos pasos que debes realizar en la UI son:
1. Especificar el evento al que el listener debe responder.
2. Indicar el nombre completo de la clase Java que contiene el listener.

### **Beneficios del enfoque basado en Java**
- Es intuitivo para desarrolladores de Java.
- Facilita la gestión de acciones y operaciones más complejas.
- Permite realizar **pruebas unitarias** y depuración del código.

### **Desventajas del enfoque basado en Java**
- Para tareas simples, hay un exceso de código repetitivo (boilerplate).
- Los cambios en el código requieren **redeployment** y reinicio del servidor.
- Tiene una **curva de aprendizaje alta** para desarrolladores que no están familiarizados con Java.


## Event Listeners

El proceso en general tiene listeners de eventos especificos:

![event listener](./img/ProcessEventListener.png)

![java event listener](./img/JavaEventListenersDefine.png)
```java

package pe.com.domain.delegate;

import org.activiti.engine.delegate.event.ActivitiEvent;
import org.activiti.engine.delegate.event.ActivitiEventListener;

public class JavaEventListener implements ActivitiEventListener{
    @Override
    public void onEvent(ActivitiEvent activitiEvent){
        System.out.println("Spring Process Event: " + activitiEvent.getType());
    }
    @Override
    public boolean isFailOnException(){
        return false;
    }
}
```

![spring event listener](./img/SpringEventListenersDefine.png)

```java

package com.activiti.extension.bean;

import org.activiti.engine.delegate.event.ActivitiEvent;
import org.activiti.engine.delegate.event.ActivitiEventListener;
import org.springframework.stereotype.Component;

@Component("myEventListener")
public class SpringEventListener implements ActivitiEventListener{
    @Override
    public void onEvent(ActivitiEvent activitiEvent){
        System.out.println("Spring Process Event: " + activitiEvent.getType());
    }
    @Override
    public boolean isFailOnException(){
        return false;
    }
}
```
Estos listeners te permiten ejecutar lógica personalizada en respuesta a eventos generados por el motor de procesos durante la ejecución de flujos de trabajo.
Ya que es un spring bean este se carga automaticamente y se ejecutará para todos los procesos ya que siempre retorna true del metodo isEnabled.

```java

package com.activiti.extension.bean;

import com.activiti.service.runtime.events.RuntimeEventListener;
import org.activiti.engine.delegate.event.ActivitiEvent;
import org.springframework.stereotype.Component;

@Component
public class MyRuntimeListener implements RuntimeEventListener{
    @Override
    public boolean isEnabled(){
        return true;
    }
    @Override
    public void onEvent(ActivitiEvent activitiEvent){
        System.out.println("Runtime Event: " + activitiEvent.getType());
    }
    @Override
    public boolean isFailOnException(){
        return false;
    }
}
```

En Alfresco Process Services 24.x (y en Activiti), el método isFailOnException() en un listener de eventos (RuntimeEventListener) indica si una excepción lanzada dentro del listener debe hacer que la ejecución del proceso falle.
* Si isFailOnException() retorna true, cualquier excepción no controlada en el listener provocará que la ejecución del proceso falle y se detenga.
* Si retorna false, las excepciones lanzadas en el listener serán ignoradas y el proceso continuará normalmente.

Esto te permite decidir si los errores en la lógica del listener deben afectar el flujo del proceso o no. Por lo general, se deja en false para evitar que errores en la auditoría, logging u otras tareas secundarias interrumpan el proceso principal.

> **Nota**:
- Clase:  implementación Java que define la lógica personalizada que se ejecutará en un punto específico del proceso.
- Expresión Delegada : Una Expresión Delegada es una forma de definir la lógica de ejecución utilizando expresiones que se resuelven en tiempo de ejecución. Estas expresiones suelen utilizar el lenguaje de expresiones de Java Unified Expression Language (UEL) y permiten una mayor flexibilidad al referenciar beans de Spring o métodos específicos sin necesidad de codificar una clase completa.
- Expresión: Una Expresión en APS es una construcción que se evalúa en tiempo de ejecución y puede devolver un valor. Las expresiones se utilizan en diversas partes del proceso, como en condiciones de flujo, asignaciones de tareas o para definir valores de variables. Al igual que las expresiones delegadas, suelen basarse en UEL y pueden acceder a variables del proceso, beans de Spring y otros componentes del contexto de ejecución.
- Tipo de entidad: filtra por la **entidad** que trae el evento (tarea, ejecución, trabajo, comentario…), no por el tipo de actividad del BPMN. Ver [Tipo de entidad](#tipo-de-entidad) más abajo.

### Cómo configurar un event listener en el modelador ("Detectores de eventos")

En el App Designer, con el lienzo vacío seleccionado (propiedades del **proceso**), abre **Detectores de eventos**. Cada fila es un listener con estos campos:

| Campo | Qué es | XML que genera |
|---|---|---|
| **Eventos** | Uno o varios tipos de evento del motor (tabla siguiente). Si lo dejas vacío, escucha **todos**. | `events="TASK_CREATED,TASK_COMPLETED"` |
| **¿Reiniciar evento?** | Si lo marcas, el listener **no ejecuta código**: convierte el evento en un evento BPMN (señal, señal global, mensaje o error). Clase y expresión delegada dejan de aplicar. Ver [¿Reiniciar evento?](#reiniciar-evento). | `throwEvent="signal" signalName="…"` |
| **Clase** | Clase Java que implementa `ActivitiEventListener`. El motor la instancia una vez, con `new`, así que **no es un bean de Spring** (no recibe `@Autowired`). | `class="pe.com.domain.delegate.JavaEventListener"` |
| **Expresión delegada** | Expresión que devuelve un bean que implementa `ActivitiEventListener`, p. ej. `${myEventListener}`. Úsala cuando necesitas servicios de Spring. En APS el bean debe estar en `com.activiti.extension.bean` para que se vea con `beans.whitelisting` activo. | `delegateExpression="${myEventListener}"` |
| **Tipo de entidad** | Filtro opcional por la entidad del evento. Ver [Tipo de entidad](#tipo-de-entidad). | `entityType="task"` |

Se llena **una sola** de las opciones: clase, expresión delegada o reiniciar evento.

```xml
<process id="miProceso">
  <extensionElements>
    <activiti:eventListener events="TASK_ASSIGNED" delegateExpression="${myEventListener}"/>
    <activiti:eventListener events="ENTITY_CREATED" entityType="comment" class="pe.com.domain.delegate.JavaEventListener"/>
    <activiti:eventListener events="TASK_COMPLETED" entityType="task" throwEvent="signal" signalName="tareaTerminada"/>
  </extensionElements>
  …
</process>
```

**Alcance (comprobado):**
- Un listener definido en el proceso solo recibe eventos de las instancias de **esa definición**.
- Se registra en el **modelo BPMN del archivo**: si un `.bpmn20.xml` tiene dos `<process>`, los listeners de uno **también se aplican al otro**. Con dos procesos en el mismo archivo, el `TASK_CREATED → error` de uno rompió el inicio del otro (`No catching boundary event found for error with errorCode 'SIN_TAREAS'`). Usa un archivo por proceso.
- Por el App Designer solo entra el primer `<process>` del archivo ([detalle](../ConceptosMotor/conceptosMotor.md#un-archivo-con-varios-process)).
- ⚠ **Al importar en el App Designer, los listeners con *¿Reiniciar evento?* pierden el *Tipo de entidad*.** Comprobado: `entityType="task"` desaparece del XML del modelo; con clase o expresión delegada se conserva. Después de importar, vuelve a escribirlo en el diálogo. Con eventos `TASK_*` no cambia nada, porque solo traen tareas. Con `ENTITY_*`, el listener pasa a dispararse para **cualquier** entidad.
- Para escuchar **todos** los procesos sin tocar los BPMN, usa un bean `RuntimeEventListener` (arriba) o un listener global del motor.

#### Eventos posibles

Lista de `ActivitiEventType` del motor de APS 24.4 (`activiti-engine 8.1.2`). La columna **¿Entidad?** dice si el evento trae una entidad: solo esos pasan el filtro **Tipo de entidad**.

| Evento | Cuándo ocurre | ¿Entidad? (qué trae) |
|---|---|---|
| `ENTITY_CREATED` | Se crea una entidad: tarea, ejecución, vínculo de identidad (candidato, involucrado), comentario, adjunto, trabajo | Sí, la creada |
| `ENTITY_INITIALIZED` | La entidad ya se creó y tiene sus datos hijos (p. ej. la tarea con sus candidatos) | Sí |
| `ENTITY_UPDATED` | Se modifica una entidad (p. ej. prioridad o vencimiento de la tarea) | Sí |
| `ENTITY_DELETED` | Se borra una entidad (p. ej. se quita un candidato) | Sí |
| `ENTITY_SUSPENDED` / `ENTITY_ACTIVATED` | Se suspende / activa la definición, una instancia o sus tareas y trabajos | Sí |
| `TIMER_SCHEDULED` | Se programa un temporizador | Sí, el trabajo (`job`) |
| `TIMER_FIRED` | Se dispara un temporizador | Sí, `job` |
| `JOB_CANCELED` | Se cancela un trabajo (p. ej. el temporizador de borde de una tarea que se completó) | Sí, `job` |
| `JOB_EXECUTION_SUCCESS` / `JOB_EXECUTION_FAILURE` | Un trabajo asíncrono o temporizador terminó bien / falló (el fallo trae la excepción) | Sí, `job` |
| `JOB_RETRIES_DECREMENTED` | El motor baja los reintentos de un trabajo que falló | Sí, `job` |
| `ACTIVITY_STARTED` / `ACTIVITY_COMPLETED` | Empieza / termina cualquier actividad: tarea, gateway, evento, subproceso | No (trae `activityId`, `activityName`, `activityType`) |
| `ACTIVITY_CANCELLED` | Se interrumpe una actividad (evento de borde, error, cancelación de la instancia) | No |
| `ACTIVITY_SIGNALED` | Una actividad recibe una señal | No |
| `ACTIVITY_MESSAGE_WAITING` / `ACTIVITY_MESSAGE_RECEIVED` / `ACTIVITY_MESSAGE_SENT` | Una actividad queda esperando un mensaje, lo recibe, o se envía uno | No |
| `ACTIVITY_ERROR_RECEIVED` | Un evento de borde o subproceso de evento captura un error BPMN | No |
| `ACTIVITY_COMPENSATE` | Se compensa una actividad | No |
| `SEQUENCEFLOW_TAKEN` | Se toma un flujo (flecha) | No |
| `UNCAUGHT_BPMN_ERROR` | Se lanza un error BPMN que nadie captura | No |
| `VARIABLE_CREATED` / `VARIABLE_UPDATED` / `VARIABLE_DELETED` | Se crea, cambia o borra una variable (de proceso, ejecución o local de tarea) | No (trae nombre, valor y tipo) |
| `TASK_CREATED` | Se crea una tarea de usuario (ya con su asignado y candidatos) | Sí, `task` |
| `TASK_ASSIGNED` | Cambia el asignado: reclamar, asignar, reasignar, liberar | Sí, `task` |
| `TASK_COMPLETED` | Se completa una tarea | Sí, `task` |
| `PROCESS_STARTED` | Se inicia una instancia (también la de un `callActivity`) | Sí, la ejecución |
| `PROCESS_COMPLETED` / `PROCESS_COMPLETED_WITH_ERROR_END_EVENT` | La instancia termina normal / por un evento de fin de error | Sí, la ejecución |
| `PROCESS_CANCELLED` | Se borra o cancela la instancia (trae la causa) | No |
| `HISTORIC_ACTIVITY_INSTANCE_CREATED` / `_ENDED`, `HISTORIC_PROCESS_INSTANCE_CREATED` / `_ENDED` | Se crea / cierra el registro histórico | Sí, pero histórica: ningún **Tipo de entidad** la acepta |
| `CUSTOM` | Lo lanza código propio con `runtimeService.dispatchEvent(...)` | Depende |
| `ENGINE_CREATED` / `ENGINE_CLOSED` | Arranca / se apaga el motor | No llegan a un listener de proceso: solo a uno global |
| `MEMBERSHIP_CREATED` / `MEMBERSHIP_DELETED` / `MEMBERSHIPS_DELETED` | Altas y bajas de miembros en grupos del motor | No llegan en APS: usa su propio módulo de identidad |

#### Tipo de entidad

Valores aceptados (cualquier otro da `Unsupported entity-type for an ActivitiEventListener` al desplegar):

| Valor | Entidad | Para qué |
|---|---|---|
| `task` | Tarea de usuario | Separar los `ENTITY_*` de tareas de los de otras entidades |
| `execution` / `process-instance` | Ejecución. En este motor toda ejecución es también `ProcessInstance`, así que los dos valores filtran lo mismo (incluye ejecuciones hijas) | `ENTITY_SUSPENDED`, `PROCESS_STARTED` |
| `identity-link` | Candidato, involucrado, asignado o propietario | Ver cuándo se agregan o quitan candidatos (`ENTITY_CREATED` / `ENTITY_DELETED`) |
| `job` | Trabajo asíncrono o temporizador | `ENTITY_CREATED` de trabajos, `JOB_*` |
| `comment` | Comentario **del motor** (los de la interfaz de APS van en su propia tabla y no generan evento) | |
| `attachment` | Adjunto del motor | |
| `process-definition` | Definición de proceso | `ENTITY_SUSPENDED` de la definición |

⚠ **El filtro descarta todo evento que no trae entidad.** Si eliges `ACTIVITY_STARTED` (o cualquier `ACTIVITY_*`, `VARIABLE_*`, `SEQUENCEFLOW_TAKEN` o `PROCESS_CANCELLED`) y además pones un tipo de entidad, el listener **nunca se ejecuta**, sin error. Comprobado en el ejemplo `eventListenersDemo` (listener 2). Con esos eventos, deja el tipo de entidad vacío.

#### ¿Reiniciar evento?

Al marcarlo, el evento del motor se **relanza como evento BPMN** y no se ejecuta código. Eliges el tipo y escribes el nombre de la señal o mensaje, o el código del error:

| Tipo | XML | Qué hace | Si no hay quién lo reciba |
|---|---|---|---|
| Señal | `throwEvent="signal" signalName="x"` | Dispara la señal `x` **solo en la misma instancia** (eventos que esperan `x`) | No pasa nada. Si el evento no es de una instancia (p. ej. un evento del motor), falla |
| Señal global | `throwEvent="globalSignal" signalName="x"` | Dispara la señal `x` en **todas** las instancias del tenant que la esperan | No pasa nada |
| Mensaje | `throwEvent="message" messageName="x"` | Entrega el mensaje `x` a la misma instancia, si lo está esperando | No pasa nada; falla si el evento no es de una instancia |
| Error | `throwEvent="error" errorCode="x"` | Lanza el error BPMN `x` **desde la ejecución del evento**: lo captura un evento de borde de error o un subproceso de evento | **La operación falla** (`No catching boundary event found for error with errorCode 'x'`) y se deshace |

- Estos listeners **siempre** tienen `isFailOnException = true`: si algo falla, falla la operación que generó el evento.
- El **Nombre** debe ser el `name` de la señal o mensaje (no su `id`). El error se busca por su `errorCode`.
- Combínalo con **Tipo de entidad** para limitarlo, p. ej. `TASK_COMPLETED` + `task`.
- Casos típicos: avisar a una rama en espera cuando se completa cualquier tarea (señal), o cortar un subproceso cuando pasa algo (error).

## Ejemplos probados en APS 24.4

> **Cómo desplegar estos BPMN a mano** (curl o App Designer) y qué necesita cada uno: [README → Cómo poner en funcionamiento un `.bpmn20.xml`](../README.md#cómo-poner-en-funcionamiento-un-bpmn20xml).

[`ejemplos/listenersDemo.bpmn20.xml`](./ejemplos/listenersDemo.bpmn20.xml) usa listeners **sin código Java** y [`ejemplos/probar.py`](./ejemplos/probar.py) comprueba que cada uno se ejecutó:

| Listener | Tipo | Resultado comprobado |
|---|---|---|
| proceso `start` | `ScriptExecutionListener` (groovy) | variable `inicio = "groovy: start"` |
| flujo `take` | expresión `${execution.setVariable('flujoTomado', true)}` | `flujoTomado = true` |
| tarea `create` | `ScriptTaskListener` (javascript) | prioridad 80 + variable **local** `creadaPor` |
| tarea `complete` | expresión `${execution.setVariable('decisionFinal', decision)}` | copia la decisión al proceso |
| proceso `end` | expresión | actualiza `fin` |

Las versiones Java (`ExecutionListener`, `TaskListener`) están en [`EjemplosJava`](../EjemplosJava/README.md#inicioexecutionlistener).

### Lo comprobado

- ⚠ **No crees variables nuevas en el listener `end` del proceso.** En PostgreSQL da HTTP 500 al completar la última tarea: `violates foreign key constraint "act_fk_var_exe" on table "act_ru_variable"` (la ejecución se borra en la misma transacción). Crea la variable antes (p. ej. en `start`) y en `end` sólo actualízala.
- En los listeners del **proceso**, `execution.getCurrentActivityId()` es `null`.
- Con `el.whitelisting.enabled=true` (valor por defecto del producto) las expresiones `${execution.setVariable(...)}` fallan con `Unknown method used in expression` hasta añadir a `call-whitelist.conf`:
  ```properties
  org.activiti.engine.delegate.DelegateExecution.*
  org.activiti.engine.delegate.DelegateTask.*
  ```
  Los listeners de **script** (groovy/javascript) no pasan por esa lista: dependen de `whitelisted-scripts.conf`.

```bash
cd Listeners/ejemplos && APS_USER=... APS_PASS=... python probar.py
```

### Event listeners: reiniciar evento y tipo de entidad

[`ejemplos/eventListenersDemo.bpmn20.xml`](./ejemplos/eventListenersDemo.bpmn20.xml) y [`ejemplos/eventListenersError.bpmn20.xml`](./ejemplos/eventListenersError.bpmn20.xml) (archivos separados, ver *Alcance*). Los comprueba [`ejemplos/probarEventListeners.py`](./ejemplos/probarEventListeners.py):

| Listener | Configuración | Resultado comprobado |
|---|---|---|
| 1 | `TASK_COMPLETED` + `task`, reiniciar como **señal** `tareaTerminada` | Al completar *Trabajar*, la rama paralela que esperaba la señal sigue y la instancia termina |
| 2 | `ACTIVITY_STARTED` + `task`, reiniciar como señal `nuncaLlega` | **No se dispara nunca**: `ACTIVITY_STARTED` no trae entidad |
| 3 | `TASK_CREATED` + `task`, reiniciar como **error** `SIN_TAREAS` | Al crearse *Revisar*, el error lo captura el borde del subproceso: la tarea se cancela y la instancia termina |

```bash
cd Listeners/ejemplos && APS_USER=... APS_PASS=... python probarEventListeners.py
```
