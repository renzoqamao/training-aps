# herramientas

`aps.py` es el cliente que usan todos los `probar.py` / `recorrido.py` de la capacitación. Sólo usa la librería estándar de Python 3: no hay que instalar nada.

## Configuración (variables de entorno)

| Variable | Obligatoria | Por defecto |
|---|---|---|
| `APS_USER` | sí | — |
| `APS_PASS` | sí | — |
| `APS_BASE` | no | `http://localhost:8080/activiti-app` |
| `APS_TENANT` | no | `tenant_1` |

## Cómo lo importan los ejemplos

No es un paquete instalado: cada script añade esta carpeta a la ruta de Python antes de importarlo.

```python
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'herramientas'))   # desde <Sección>/ejemplos/
from aps import call, deploy, undeploy, start, tasks, complete, hist_vars, check, done, T
```

## Funciones

| Función | Para qué |
|---|---|
| `call(método, ruta, body=None, files=None, ok=(200, 201, 204), user=None)` | Petición HTTP con Basic auth a `APS_BASE/api/<ruta>`. Devuelve `(status, json)`. Si el status no está en `ok`, lanza `AssertionError`; con `ok=None` no valida. `files={'file': (nombre, bytes)}` envía multipart. `user=(email, clave)` llama como otro usuario. |
| `deploy(ruta_bpmn)` / `undeploy(deploymentId)` | Despliega / borra (cascade) un `.bpmn20.xml` con la API del motor. |
| `publish_app(ruta_bpmn, nombre, share_with=())` / `unpublish_app(nombre)` | Importa el BPMN como modelo, crea una app, la publica (necesario para la API pública) y la comparte con los usuarios de `share_with` / lo deshace todo. |
| `start(clave, variables=None, **extra)` | Inicia por clave con la API del motor (`extra`: p. ej. `businessKey`). |
| `tasks(processInstanceId)` / `complete(taskId, variables=None)` | Tareas activas de una instancia / completar una tarea. |
| `hist_vars(processInstanceId)` | Variables históricas como `dict` (sirve con la instancia terminada). |
| `ended(processInstanceId)` | `True` si la instancia terminó. |
| `check(condición, mensaje)` / `done()` | Imprime `OK` / `FALLO`; `done()` resume y sale con código 1 si algo falló. |
| `T`, `TENANT` | `"tenantId=tenant_1"` para las URLs de la API del motor / el tenant. |
