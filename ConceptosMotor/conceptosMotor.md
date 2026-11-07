# Conceptos del motor: definiciones, instancias y ejecuciones

Tres palabras que aparecen en toda la API y en los errores del motor. Todo lo de esta página se comprobó en APS 24.4.0 con [`ejemplos/probar.py`](./ejemplos/probar.py) y [`ejemplos/ejecuciones.bpmn20.xml`](./ejemplos/ejecuciones.bpmn20.xml).

## Plano y casas construidas

- **Definición de proceso** = el **plano**. Es el `<process>` del BPMN una vez desplegado en el motor: qué tareas tiene, en qué orden, con qué listeners.
- **Instancia de proceso** = cada **casa construida** con ese plano. Es un caso concreto: el pedido P-001, la solicitud SOL-2.
- **Ejecución** = cada **puntero** que indica por dónde va una instancia.

Con un plano se construyen todas las casas que se quiera: una definición puede tener cualquier número de instancias a la vez.

## De dónde salen: modelo → despliegue → definición → instancia

```
 App Designer            publicar app /             motor
 (editable)              POST deployments
┌──────────┐            ┌───────────────┐        ┌──────────────────────────┐        ┌───────────┐
│  Modelo  │ ─────────▶ │  Despliegue   │ ─────▶ │ Definición de proceso    │ ─────▶ │ Instancia │ ×N
│ (dibujo) │            │ (paquete de   │        │ una por cada <process>   │ start  │ (un caso) │
└──────────┘            │  archivos)    │        │ key + version, INMUTABLE │        └───────────┘
                        └───────────────┘        └──────────────────────────┘
```

**Comprobado:** un despliegue de `ejecuciones.bpmn20.xml` (3 `<process>`) creó 3 definiciones: `ejLimite:1:…`, `ejParalelo:1:…`, `ejSecuencial:1:…`.

Los `id` de los elementos (tareas, flujos, eventos) deben ser **únicos en todo el archivo**, no sólo dentro de cada `<process>`: con ids repetidos el despliegue da 500.

## El id de una definición: `clave:versión:id`

`ejSecuencial:2:43358`:

| Parte | Qué es |
|---|---|
| `ejSecuencial` | **clave** = el `id` del `<process>`. Estable, la eliges tú. |
| `2` | **versión**. La asigna el motor: sube cada vez que despliegas un archivo con esa misma clave. |
| `43358` | id interno de la base de datos. |

## Las definiciones no se modifican: se versionan

Una definición desplegada **no se puede editar**. Si cambias el BPMN y lo despliegas otra vez, nace la **versión 2** y la 1 sigue existiendo.

| Paso (comprobado) | Resultado |
|---|---|
| Despliego v1 e inicio la instancia **A** | A usa `ejSecuencial:1` |
| Despliego el mismo archivo otra vez | nace `ejSecuencial:2` |
| Inicio **B** por clave (`processDefinitionKey`) | B usa la **v2**: por clave siempre se usa la **última** versión |
| Inicio **C** por id (`processDefinitionId` de la v1) | C usa la **v1**: por id eliges una versión concreta |
| `GET /api/repository/process-definitions?tenantId=tenant_1&key=ejSecuencial&latest=true` | sólo la v2 |

- **Las instancias en curso no migran:** A sigue en la v1, con el diagrama viejo, hasta terminar. El cambio afecta a las instancias **nuevas**.
- En APS, **republicar una app** es un despliegue nuevo, así que crea una nueva versión de sus procesos con el mismo efecto.
- Los **eventos de inicio de mensaje y de señal** apuntan a la **última** versión: al redesplegar, la suscripción pasa a la v2 (ver [Mensajes y señales](../MessageAndSignals/messageAndSignals.md#por-qué-no-se-pueden-desplegar-dos-procesos-con-el-mismo-mensaje-de-inicio)).

### Iniciar por clave o por id

```
POST /api/runtime/process-instances?tenantId=tenant_1
{"processDefinitionKey":"ejSecuencial","tenantId":"tenant_1"}     ← última versión; tenantId también en el body

POST /api/runtime/process-instances?tenantId=tenant_1
{"processDefinitionId":"ejSecuencial:1:43286"}                    ← versión concreta; SIN tenantId en el body
```

**Comprobado:** por id **con** `tenantId` en el body → HTTP 400. El id ya identifica una definición concreta; el `tenantId` del body sólo se usa al iniciar por **clave** o por **mensaje**.

## Suspender una definición

Retira una versión sin borrarla, por ejemplo mientras se cierran sus casos abiertos:

```
PUT /api/repository/process-definitions/{id}   {"action":"suspend"}     ← "activate" la reabre
```

**Comprobado:** con la v1 suspendida, iniciar una instancia de la v1 → HTTP 500; la instancia A (v1) que ya existía siguió existiendo; tras `activate` se pudo iniciar de nuevo.

## Ejecuciones: una raíz y una hija por cada camino activo

Una instancia **siempre** tiene al menos dos ejecuciones, aunque no tenga nada en paralelo:

| Proceso (comprobado) | Ejecuciones |
|---|---|
| inicio → Tarea A → fin | **2**: raíz + hija en Tarea A |
| compuerta paralela → Tarea A y Tarea B | **3**: raíz + hija en A + hija en B |
| Tarea A con evento de límite no interrumpidor | **3**: raíz + hija en A + hija en el evento de límite |

- La **raíz** es la instancia de proceso: no está en ninguna actividad (`activityId` vacío), guarda el *business key* y las variables de proceso.
- Cada **hija** es un camino activo: una tarea, cada rama paralela, cada evento de límite que espera.

```
GET /api/runtime/executions?tenantId=tenant_1&processInstanceId=<id>
```

**Por qué importa:**

- Un mensaje se entrega a **la hija** que está parada en el evento de mensaje (`messageEventSubscriptionName=...`), no a la instancia.
- El *business key* está en la raíz y la suscripción al mensaje en una hija: filtrar por los dos a la vez en una sola consulta **no devuelve nada**. Hay que buscar primero la instancia y luego su ejecución (ver [`MensajeriaBean`](../EjemplosJava/README.md#mensajeriabean)).
- Las variables que se pasan al entregar un mensaje quedan en la **raíz** (nivel de proceso), aunque se entreguen a la hija.

## Un archivo con varios `<process>`

BPMN 2.0 permite varios `<process>` dentro de un `<definitions>`, y el motor de APS los acepta. Lo que pasa depende de cómo se despliegue (comprobado en APS 24.4 con [`ejemplos/dosProcesos.bpmn20.xml`](./ejemplos/dosProcesos.bpmn20.xml) y [`ejemplos/probarDosProcesos.py`](./ejemplos/probarDosProcesos.py)):

| | API del motor (`POST /api/repository/deployments`) | App Designer (importar + app + publicar) |
|---|---|---|
| Definiciones creadas | **Todas**: `dosA` y `dosB`, en **un** despliegue | **Sólo la primera** (`dosA`). El modelo importado ya no tiene `dosB`, sin aviso |
| Se inicia desde la interfaz de APS | No (sólo con la API del motor) | Sí |
| Event listeners del `<process>` | Se aplican a **todos** los procesos del archivo | Sólo hay un proceso |

**Los event listeners son del archivo, no del proceso.** El motor los registra en el modelo BPMN del archivo. En el ejemplo, `dosB` no tiene listeners, pero el `TASK_CREATED` de `dosA` se ejecuta también al crearse la tarea de `dosB`. Lo comprueba la variable `listenerDeA`. Con un listener que lanza un error, eso rompe el inicio del otro proceso ([caso real](../Listeners/listeners.md#cómo-configurar-un-event-listener-en-el-modelador-detectores-de-eventos)). Los execution y task listeners sí son de cada elemento: no se comparten.

Cuándo usar varios procesos en un archivo:
- **Sí:** ejemplos y pruebas que se despliegan con la API del motor, o procesos que siempre van juntos (p. ej. un padre y el hijo de su `callActivity`) y no tienen event listeners.
- **No:** procesos que se modelan y publican en el App Designer. Usa **un proceso por archivo**.

## Ejecutar el ejemplo

```bash
cd ConceptosMotor/ejemplos
APS_USER=admin@app.activiti.com APS_PASS=<clave> python probar.py
```

```
1. Un despliegue crea una definición por cada <process>
  OK    definiciones -> ['ejLimite:1:43288', 'ejParalelo:1:43287', 'ejSecuencial:1:43286']
2. Ejecuciones: siempre una raíz + una hija por cada camino activo
  OK    ejSecuencial: 2 ejecuciones [('hija', 'sTareaA'), ('raíz', '-')]
  OK    ejParalelo: 3 ejecuciones [('hija', 'pTareaA'), ('hija', 'pTareaB'), ('raíz', '-')]
  OK    ejLimite: 3 ejecuciones [('hija', 'lAviso'), ('hija', 'lTareaA'), ('raíz', '-')]
3. Versiones: redesplegar crea la v2; las instancias existentes no migran
  OK    A (iniciada antes) sigue en ejSecuencial:1:43286
  OK    B (por clave, después) usa ejSecuencial:2:43358
  OK    latest=true sólo devuelve la v2
4. Iniciar por id elige una versión concreta (sin tenantId en el body)
  OK    C por id de v1 -> ejSecuencial:1:43286
  OK    por id + tenantId en el body -> HTTP 400
5. Suspender una definición impide iniciarla; las instancias existentes siguen
  OK    iniciar la v1 suspendida -> HTTP 500
  OK    la instancia A (v1) sigue existiendo
  OK    reactivada: se puede iniciar otra vez
Todo OK
```
