# Propiedades de actividad: multiinstancia, asíncrona, exclusiva, compensación y propiedades de user task

Qué hace cada propiedad del panel de una actividad (service task, user task, script task...) en el editor de APS, cuándo conviene usarla y qué escribe en el BPMN. Todo lo marcado como **comprobado** se ejecutó en APS 24.4.0 (motor Activiti 8.1.2) con [`ejemplos/probar.py`](./ejemplos/probar.py) y [`ejemplos/propiedades.bpmn20.xml`](./ejemplos/propiedades.bpmn20.xml). Los nombres de los ejemplos son inventados.

## Resumen

| Propiedad en el editor | Atributo BPMN | Valor por defecto | Para qué sirve |
|---|---|---|---|
| **Asincrónica** | `activiti:async="true"` | desmarcada | Guardar el estado antes de la actividad y ejecutarla en un job de fondo |
| **Exclusiva** | `activiti:exclusive` | editor: **desmarcada**; motor (sin atributo): exclusiva | Que los jobs asíncronos de una misma instancia no corran a la vez |
| **Tipo de multiinstancia** | `<multiInstanceLoopCharacteristics isSequential=…>` | *None* | Repetir la actividad: en paralelo o una tras otra |
| **Cardinalidad** | `<loopCardinality>` | — | Cuántas repeticiones (número o expresión) |
| **Colección** | `activiti:collection` | — | Una repetición por cada elemento de una lista |
| **Variable del elemento** | `activiti:elementVariable` | — | Nombre de la variable con el elemento de cada repetición |
| **Condición de terminación** | `<completionCondition>` | — | Terminar el bucle antes de completar todas las repeticiones |
| **Es para compensación** | `isForCompensation="true"` | desmarcada | Actividad que sólo corre para deshacer otra |
| **Prioridad** (user task) | `activiti:priority` | **0** | Ordenar y filtrar bandejas |
| **Categoría** (user task) | `activiti:category` | vacía | Agrupar y filtrar tareas |
| **Fecha de vencimiento** (user task) | `activiti:dueDate` | vacía | Fecha límite de la tarea |

## Asincrónica

Sin esta marca, el motor ejecuta todo lo que sigue a una acción del usuario (iniciar, completar) **en la misma transacción** y dentro de la misma petición HTTP. Con la marca, guarda el estado justo antes de la actividad, responde, y la actividad se ejecuta después en un *job* de fondo.

**Comprobado:**
- Al iniciar un proceso cuya primera actividad es asíncrona, la respuesta llega con `ended: false`. Segundos después, el job la ejecuta y el proceso termina.
- **Un error síncrono deshace todo:** un service task que falla sin la marca hace que el inicio responda **HTTP 500** y **no queda ninguna instancia**.
- **Un error asíncrono no deshace lo anterior:** la instancia existe y el job se reintenta. El motor lo intenta **3 veces** (`asyncExecutorNumberOfRetries = 3`, unos 10 s entre intentos) y después lo pasa a **dead letter jobs** con `retries = 0` y el mensaje del error. En la prueba tardó unos 28 s.
- Los jobs se ven con la API del motor: `GET /api/management/jobs` (pendientes) y `GET /api/management/deadletter-jobs` (agotados). También se ven en activiti-admin.
- **Reintentar un dead letter job:** primero se corrige la causa (en el ejemplo, una variable) y después `PUT /api/management/deadletter-jobs/{id}` con `{"action": "move"}` (200). El job vuelve a la cola, se ejecuta y el proceso continúa. Con `POST` responde 403.

**Casos de uso:**
- Llamar a un sistema externo lento o inestable (un servicio de archivo, un correo, un registro en otro sistema) sin que el usuario espere ni pierda lo que acaba de completar si el sistema falla.
- Cortar una transacción larga en partes, para que un error al final no deshaga todo el trabajo previo.

**Ojo:** que el proceso no se detenga ante un error no significa que el error desaparezca. Un job en dead letter deja la instancia **detenida en esa actividad** hasta que alguien lo reintente. Si se reintenta sin corregir la causa, vuelve a fallar.

## Exclusiva

Sólo tiene efecto en actividades **asíncronas**. Exclusiva significa que el motor no ejecuta a la vez dos jobs exclusivos de la **misma instancia**. Sin ella, dos ramas paralelas asíncronas pueden ejecutarse al mismo tiempo y una de ellas fallar con `OptimisticLockingException` al guardar.

**Comprobado (diferencia entre editor y motor):**
- En el **editor de APS** el checkbox viene **desmarcado**. Desmarcado se exporta como `activiti:exclusive="false"`, es decir, **no exclusiva**.
- En el **motor**, si el XML no trae el atributo, la actividad **es exclusiva**. Al importar un XML sin el atributo, el editor muestra el checkbox **marcado**.

> **Regla práctica:** si marcas *Asincrónica* en el editor, marca también *Exclusiva*, salvo que necesites paralelismo real entre ramas de la misma instancia y aceptes los reintentos por conflicto.

## Multiinstancia

Repite una actividad. Con **Paralelo** crea todas las repeticiones a la vez; con **Secuencial**, una tras otra.

| Propiedad | Ejemplo |
|---|---|
| Cardinalidad | `3` o `${numeroRevisores}` |
| Colección | `${revisores}`: debe ser una `java.util.Collection` (una lista), no un texto ni un arreglo |
| Variable del elemento | `revisor`, para luego asignar la tarea con `${revisor}` |
| Condición de terminación | `${nrOfCompletedInstances >= 2}` |

Variables que el motor pone a disposición dentro del bucle (**comprobado**): `nrOfInstances`, `nrOfActiveInstances`, `nrOfCompletedInstances` y `loopCounter` (índice de la repetición, empieza en 0).

**Comprobado:**
- **Paralela con colección:** con `revisores = [ana.demo, beto.demo, carla.demo]` se crean 3 tareas a la vez, una asignada a cada uno. Con `nrOfCompletedInstances >= 2`, al completar la segunda se **cancela la tercera** y el proceso sigue.
- **Secuencial con cardinalidad 3:** hay una sola tarea a la vez y `loopCounter` vale 0 y luego 1. Con la condición `${voto == 'NO'}`, completar la segunda con `voto = NO` termina el bucle sin hacer la tercera vuelta.
- La condición se evalúa **cada vez que termina una repetición**.

**Casos de uso:**
- **Revisión por varios:** todos los miembros de una lista revisan el mismo documento en paralelo.
- **Mayoría o quórum:** `${nrOfCompletedInstances / nrOfInstances >= 0.5}`.
- **Basta un rechazo:** `${decision == 'RECHAZADO'}` corta el bucle con el primer rechazo.
- **Aprobación escalonada:** aprobadores en orden (secuencial), cada uno ve el resultado del anterior.
- **Un service task por elemento:** notificar a cada destinatario de una lista.

**Ojo:**
- Si la colección viene como texto `"a,b,c"`, conviértela antes en lista. El ejemplo lo hace con un script task Groovy: `new ArrayList(texto.tokenize(','))`.
- Una variable que fija el usuario al completar una repetición (como `voto`) queda en el proceso y la siguiente repetición la ve. Para separar los resultados de cada repetición, guárdalos como variables locales de la tarea con un task listener.

## Es para compensación

Marca una actividad como **manejador de compensación**: no forma parte del flujo normal y sólo se ejecuta cuando se lanza un evento de compensación, para **deshacer** otra actividad que ya terminó. Se dibuja así:

```
[Reservar] ──▶ … ──▶ (evento intermedio de lanzamiento: compensación)
    ⊙ evento de borde de compensación
    ┊ (asociación)
[Anular reserva]   ← "Es para compensación" marcado
```

**Comprobado:**
- Si el proceso pasa por "Reservar" y **no** lanza la compensación, "Anular reserva" **no se ejecuta**.
- Si llega al evento de lanzamiento, el motor ejecuta "Anular reserva" para la actividad "Reservar" ya completada.
- En el XML, la `association` debe ir **al final** del `<process>`, después de los flujos. Si va en medio, el despliegue falla con un error de esquema (`cvc-complex-type.2.4.a`).

**Casos de uso:**
- Deshacer en otro sistema algo ya hecho (una reserva, un registro, un bloqueo de saldo) cuando el caso se cancela más adelante.
- Una "transacción de negocio" en varios pasos donde no se puede hacer *rollback* técnico, porque cada paso ya se confirmó.

## Propiedades exclusivas del user task

| Propiedad | Comprobado |
|---|---|
| **Prioridad** | Sin la propiedad la tarea queda con **`priority = 0`** (no 50, como en otros motores). Acepta expresiones: `${urgencia * 10}` con `urgencia = 7` dio 70. El motor no la usa para nada más que ordenar y filtrar. |
| **Categoría** | `categoriaDemo` queda en la tarea. La **API del motor** filtra por ella (`GET /api/runtime/tasks?category=…`). La **API pública no**: `POST /api/enterprise/tasks/query` con `category` da **400** (*Unrecognized field "category"*), aunque sí devuelve la categoría en cada tarea, así que se puede filtrar del lado del cliente. |
| **Fecha de vencimiento** | Acepta una fecha, una expresión o una duración ISO 8601: `P2D` dio *ahora + 2 días*. Por sí sola no dispara nada; para escalar o recordar se usa un **temporizador de borde**. La interfaz web la muestra como texto relativo ("en 2 días", "hace 3 días") y **no marca de forma especial las tareas vencidas** (revisado en `workflow/views/tasks.html` y `task-detail.html`). |
| **Asignación** | Asignado, usuarios candidatos o grupos candidatos. En el mismo diálogo hay dos opciones propias de APS (ver abajo). |
| **Correo al asignar / plantilla de correo** | Propias de APS: avisan al asignado con una plantilla. |
| **Formulario** | Referencia al formulario o *form key*. |
| **Listeners de tarea** | `create`, `assignment`, `complete`: ver [Desarrollo de listeners](../Listeners/listeners.md). |

### Opciones de APS en el diálogo de asignación

El editor las escribe como extensiones del user task. Las aplica la capa de APS (API pública e interfaz web), no el motor.

```xml
<userTask id="revisar" activiti:assignee="${asignado}">
  <extensionElements>
    <modeler:initiator-can-complete><![CDATA[true]]></modeler:initiator-can-complete>
    <modeler:deactivate-user-task-reassignment><![CDATA[true]]></modeler:deactivate-user-task-reassignment>
  </extensionElements>
</userTask>
<!-- xmlns:modeler="http://activiti.com/modeler" -->
```

| Opción | Comprobado con la API pública |
|---|---|
| **Permitir que el iniciador complete la tarea** (`initiator-can-complete`) | La tarea informa `initiatorCanCompleteTask: true`. El iniciador del proceso, **sin ser el asignado**, la completa (`PUT /api/enterprise/tasks/{id}/action/complete` → 200). En una tarea sin la opción, el mismo usuario recibe **403**. |
| **Desactivar la reasignación** (`deactivate-user-task-reassignment`) | La tarea informa `deactivateUserTaskReassignment: true`, pero **sólo la interfaz web lo aplica**: limita el selector de asignado a los grupos y usuarios ya involucrados en la tarea (y no deja editarlo si no hay ninguno). La API pública **sí permite reasignar** (`action/assign` → 200). **No sirve como control de seguridad.** |

**Casos de uso:**
- *Iniciador puede completar:* quien abrió una solicitud puede cerrarla o retirarla aunque la tarea esté en manos de otra persona.
- *Desactivar reasignación:* evitar que un usuario de la interfaz pase la tarea a cualquiera. Si se necesita que el servidor lo impida (API incluida), hace falta una extensión que valide la asignación.

## Ejecutar el ejemplo

```bash
export APS_USER=admin@app.activiti.com APS_PASS=<clave> APS_BASE=http://localhost:8080/activiti-app
cd PropiedadesActividad/ejemplos && python probar.py
```

Despliega los 7 procesos con la API del motor y recorre cada uno. Además:
- importa dos modelos pequeños con la API pública para comprobar el checkbox *Exclusiva* del editor;
- publica una app con [`iniciador.bpmn20.xml`](./ejemplos/iniciador.bpmn20.xml) y usa dos usuarios de prueba, `demo.iniciador@demo.test` y `demo.asignado@demo.test`. Los crea la primera vez y después los reutiliza, porque APS no borra usuarios. La clave se toma de `APS_DEMO_PASS` (por defecto `Demo-Clave-2026`).

Al final borra los despliegues, los modelos y la app. La parte 4 espera unos 30 s a que el job agote sus reintentos. Resultado: 31 comprobaciones OK.
