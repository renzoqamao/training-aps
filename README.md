# Capacitación en APS

## Prerrequisitos

- [Java Development Kit (JDK) - Version 17](https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html)
- [Maven - Version 3.8.8](https://maven.apache.org/download.cgi)
- [Docker - Latest stable version](https://docs.docker.com/desktop/setup/install/windows-install/) 
- Un ambiente de Alfresco Process Service


# Temas

1. [Personalización del formulario de tareas](./CustomFormTask/customFormTask.md)

2. [Personalización de campos de formulario personalizados](./CustomFormFields/customFormFields.md)

3. [Recursos web personalizados](./CustomWebResources/customWebResources.md)

4. [Plantillas de documentos](./DocumentTemplates/documentTemplates.md)

5. [API ReST](./API-ReST/apiRest.md)

6. [Configuración de proyecto Maven para desarrollo](./ConfigurationMavenProject/mavenProject.md)

7. [Endpoints ReST personalizados y anulaciones de seguridad de endpoints ReST](./CustomEndpointReST/customEndPointRest.md)

8. [Desarrollo de listeners](./Listeners/listeners.md)

9. [Desarrollo de Service Task](./ServiceTask/serviceTask.md)

10. [Script Task personalizados](./CustomScriptTask/customScriptTask.md) 

11. [Modelo de datos personalizados](./CustomDataModels/customDataModels.md)

12. [Reportes personalizados](./CustomReports/customReports.md)

13. [Mensajes y señales](./MessageAndSignals/messageAndSignals.md)

14. [Ejemplos Java (delegates, listeners, beans, endpoint REST)](./EjemplosJava/README.md)

15. [Conceptos del motor: definiciones, versiones, instancias y ejecuciones](./ConceptosMotor/conceptosMotor.md)

16. [Propiedades de actividad: multiinstancia, asíncrona, exclusiva, compensación y user task](./PropiedadesActividad/propiedadesActividad.md)

# Ejemplos ejecutables

Varias secciones incluyen una carpeta `ejemplos/` con procesos BPMN y un script `probar.py` que los despliega, los recorre, **comprueba el resultado** (líneas `OK` / `FALLO`) y limpia lo que creó. Todos se probaron en APS 24.4.0.

| Sección | Ejemplo | Qué comprueba |
|---|---|---|
| API ReST | [`API-ReST/ejemplos/recorrido.py`](./API-ReST/ejemplos/recorrido.py) | pública vs motor, `tenantId`, publicar una app por API, ciclo completo, paginación, bug de tareas históricas con variables, capacidades |
| Listeners | [`Listeners/ejemplos/`](./Listeners/ejemplos/) | execution/task listeners con script y expresiones |
| Service Task | [`ServiceTask/ejemplos/`](./ServiceTask/ejemplos/) | expresiones con beans y listas blancas |
| Script Task | [`CustomScriptTask/ejemplos/`](./CustomScriptTask/ejemplos/) | groovy y javascript, `resultVariable` |
| Mensajes y señales | [`MessageAndSignals/ejemplos/`](./MessageAndSignals/ejemplos/) | mensaje a una ejecución, señal de difusión, inicio por mensaje/señal |
| Conceptos del motor | [`ConceptosMotor/ejemplos/`](./ConceptosMotor/ejemplos/) | definiciones por despliegue, versiones, iniciar por clave o id, suspender, ejecuciones |
| Propiedades de actividad | [`PropiedadesActividad/ejemplos/`](./PropiedadesActividad/ejemplos/) | multiinstancia (colección, cardinalidad, condición de terminación), asíncrona, dead letter y su reintento, Exclusiva en el editor, compensación, prioridad/categoría/vencimiento, iniciador puede completar y reasignación desactivada |
| Java | [`EjemplosJava/`](./EjemplosJava/README.md) | las 7 clases Java desplegadas en un jar |

**Requisitos:** Python 3 (sin librerías extra; el cliente es [`herramientas/aps.py`](./herramientas/aps.py)) y un APS 24.4.0 de pruebas. **No los ejecutes contra un servidor compartido**: crean y borran despliegues.

```bash
export APS_USER=admin@app.activiti.com
export APS_PASS=<clave>
export APS_BASE=http://<servidor>:<puerto>/activiti-app   # por defecto http://localhost:8080/activiti-app
# opcional: APS_TENANT (por defecto tenant_1)
cd Listeners/ejemplos && python probar.py
```

Los BPMN de `ejemplos/` no traen la parte gráfica (BPMNDI): están pensados para desplegarse por API.

## Cómo poner en funcionamiento un `.bpmn20.xml`

Hay tres formas. Las tres se probaron en APS 24.4.0.

| Forma | Queda desplegado | Se inicia desde la UI / API pública | Permiso necesario |
|---|---|---|---|
| A. `probar.py` | no (lo borra al terminar) | no | *tenant-admin* o *tenant-admin-api* |
| B. API del motor (curl) | sí | **no**: sólo con la API del motor | *tenant-admin* o *tenant-admin-api* |
| C. App Designer (importar + app + publicar) | sí | **sí** | acceso al App Designer |

### A. Automático con `probar.py`

Despliega, ejecuta las comprobaciones y borra el despliegue (ver [Ejemplos ejecutables](#ejemplos-ejecutables)). Es la forma más rápida de ver que funciona.

### B. Desplegar con la API del motor (curl)

```bash
export APS_USER=admin@app.activiti.com APS_PASS=<clave> APS_BASE=http://<servidor>:<puerto>/activiti-app
B=$APS_BASE/api

# 1. Desplegar (tenantId en la URL es obligatorio)
curl -u "$APS_USER:$APS_PASS" -F "file=@Listeners/ejemplos/listenersDemo.bpmn20.xml" \
     "$B/repository/deployments?tenantId=tenant_1"
# -> {"id":"40782","name":"listenersDemo.bpmn20.xml","tenantId":"tenant_1",...}

# 2. Iniciar por clave (el id del <process>), con variables si las necesita
curl -u "$APS_USER:$APS_PASS" -H "Content-Type: application/json" \
     -d '{"processDefinitionKey":"listenersDemo","tenantId":"tenant_1","variables":[{"name":"decision","value":"aprobado"}]}' \
     "$B/runtime/process-instances?tenantId=tenant_1"

# 3. Ver sus tareas / completar una
curl -u "$APS_USER:$APS_PASS" "$B/runtime/tasks?tenantId=tenant_1&processInstanceId=<id>"
curl -u "$APS_USER:$APS_PASS" -H "Content-Type: application/json" -d '{"action":"complete"}' "$B/runtime/tasks/<taskId>"

# 4. Quitarlo (cascade=true borra también instancias e historial)
curl -u "$APS_USER:$APS_PASS" "$B/repository/deployments?tenantId=tenant_1&name=listenersDemo.bpmn20.xml"
curl -u "$APS_USER:$APS_PASS" -X DELETE "$B/repository/deployments/<deploymentId>?cascade=true"
```

> Un proceso desplegado así **no aparece en ninguna app** y la API pública no lo puede iniciar (`POST /api/enterprise/process-instances` → 403). Sirve para pruebas y para procesos que se lanzan desde sistemas externos con la API del motor.

En Windows usa Git Bash, o en PowerShell `curl.exe` en lugar de `curl`.

### C. Importar en el App Designer y publicar en una app

Es lo que se hace en un entorno real. Los usuarios inician el proceso desde la app.

1. **App Designer → Procesos → Importar proceso** y elige el `.bpmn20.xml`. Los ejemplos no traen la parte gráfica (BPMNDI); APS coloca los elementos automáticamente al importar. **Comprobado:** se conservan los listeners, scripts y expresiones.
2. **App Designer → Apps → Crear app**, ábrela, en **Editar modelos incluidos** añade el proceso importado y guarda.
3. **Publicar** la app. Aparece en la página de inicio; el proceso se inicia desde **Iniciar proceso**.

Lo mismo por API (comprobado, lo hace `publish_app()` de [`herramientas/aps.py`](./herramientas/aps.py) y se explica en [API ReST](./API-ReST/apiRest.md#reglas-que-conviene-saber)):

```
POST /api/enterprise/process-models/import       multipart file=<bpmn>               -> modelo de proceso
POST /api/enterprise/models                       {"name":"Mi App","modelType":3}      -> modelo de app
PUT  /api/enterprise/app-definitions/{appId}      {"appDefinition":{"name":"Mi App","definition":{"models":[{"id":<proceso>}],
                                                   "theme":"theme-1","icon":"glyphicon-asterisk"}},"publish":true}
```

> ⚠ **Un archivo con varios `<process>`** (comprobado con [`ConceptosMotor/ejemplos/probarDosProcesos.py`](./ConceptosMotor/ejemplos/probarDosProcesos.py), detalle en [Conceptos del motor](./ConceptosMotor/conceptosMotor.md#un-archivo-con-varios-process)):
> - **Forma B** (API del motor): despliega **todos**, una definición por `<process>`, en un solo despliegue.
> - **Forma C** (App Designer): el modelo importado conserva **sólo el primero**, y la app publica sólo ese. Los demás se pierden sin aviso.
> - En los dos casos, los **event listeners** de un proceso se aplican también a los otros del mismo archivo.
>
> Para el App Designer, usa **un proceso por archivo**.

> ⚠ **Otras dos cosas que cambia o exige la forma C (comprobado):**
> - Al importar, los event listeners con **¿Reiniciar evento?** pierden el `entityType`. Los de clase y expresión delegada lo conservan.
> - Para publicar la app, cada tarea de usuario necesita asignado, usuarios candidatos o grupos candidatos. Si falta, la publicación devuelve `User task has no assignment set` y no despliega nada. Por API llega con **HTTP 200** y `"error": true` (mensaje en `errorDescription`): hay que revisar el cuerpo, no sólo el status.

### Requisitos de cada ejemplo

| Archivo | Procesos (clave) | Requisitos antes de iniciarlo |
|---|---|---|
| [`API-ReST/ejemplos/procesoApi.bpmn20.xml`](./API-ReST/ejemplos/procesoApi.bpmn20.xml) | `procesoApi` | ninguno |
| [`Listeners/ejemplos/listenersDemo.bpmn20.xml`](./Listeners/ejemplos/listenersDemo.bpmn20.xml) | `listenersDemo` | variable `decision` al completar la tarea; con `el.whitelisting.enabled=true`, añadir `DelegateExecution.*` y `DelegateTask.*` a `call-whitelist.conf` ([detalle](./Listeners/listeners.md#lo-comprobado)) |
| [`CustomScriptTask/ejemplos/scriptTaskDemo.bpmn20.xml`](./CustomScriptTask/ejemplos/scriptTaskDemo.bpmn20.xml) | `scriptTaskDemo` | variables `message` (texto) y `usegroovy` (booleano) al iniciar; groovy y javascript en `whitelisted-scripts.conf` |
| [`ServiceTask/ejemplos/serviceTaskWhitelist.bpmn20.xml`](./ServiceTask/ejemplos/serviceTaskWhitelist.bpmn20.xml) | `serviceTaskPermitido`, `serviceTaskBloqueado`, `serviceTaskExpresion` (3 procesos) | `monto` para `serviceTaskExpresion`; listas blancas según [Service Task](./ServiceTask/serviceTask.md#lo-comprobado-en-aps-244) |
| [`MessageAndSignals/ejemplos/mensajesSenales.bpmn20.xml`](./MessageAndSignals/ejemplos/mensajesSenales.bpmn20.xml) | `pedidoDemo`, `atenderAlertaDemo`, `solicitudDemo` (3 procesos) | `atenderAlertaDemo` y `solicitudDemo` no se inician a mano: arrancan con la señal / el mensaje ([cómo enviarlos](./MessageAndSignals/messageAndSignals.md#mensaje-vs-señal)) |
| [`MessageAndSignals/ejemplos/solicitudCredito.bpmn20.xml`](./MessageAndSignals/ejemplos/solicitudCredito.bpmn20.xml) | `solicitudCredito` | variables `monto` y `plazo` al iniciar; se cancela con el mensaje `retiroSolicitud` y recalcula con la señal `cambioTasa` |
| [`MessageAndSignals/ejemplos/anuncioCambioTasa.bpmn20.xml`](./MessageAndSignals/ejemplos/anuncioCambioTasa.bpmn20.xml) | `anuncioCambioTasa` | ninguno: al iniciarlo lanza la señal `cambioTasa` |
| [`ConceptosMotor/ejemplos/ejecuciones.bpmn20.xml`](./ConceptosMotor/ejemplos/ejecuciones.bpmn20.xml) | `ejSecuencial`, `ejParalelo`, `ejLimite` (3 procesos) | ninguno |
| [`ConceptosMotor/ejemplos/dosProcesos.bpmn20.xml`](./ConceptosMotor/ejemplos/dosProcesos.bpmn20.xml) | `dosA`, `dosB` (2 procesos) | ninguno. Por el App Designer sólo entra `dosA` |
| [`Listeners/ejemplos/eventListenersDemo.bpmn20.xml`](./Listeners/ejemplos/eventListenersDemo.bpmn20.xml) | `eventListenersDemo` | ninguno |
| [`Listeners/ejemplos/eventListenersError.bpmn20.xml`](./Listeners/ejemplos/eventListenersError.bpmn20.xml) | `eventListenersError` | ninguno: al iniciarlo, el error cancela la tarea y termina |
| [`EjemplosJava/procesos/javaDemo.bpmn20.xml`](./EjemplosJava/procesos/javaDemo.bpmn20.xml) | `javaDemo`, `pedidoJava`, `pagadorJava`, `alertadorJava` (4 procesos) | **antes** desplegar `training-aps-ejemplos.jar` y reiniciar ([cómo](./EjemplosJava/README.md#compilar-y-desplegar)); `monto` al iniciar `javaDemo`; `pedidoId` e `importe` en `pagadorJava`; con `el.whitelisting.enabled=true`, añadir `DelegateExecution.*` a `call-whitelist.conf` para `alertadorJava` ([detalle](./EjemplosJava/README.md#compilar-y-desplegar)) |

# Referencias

- [documentación de APS](https://support.hyland.com/r/Alfresco/Alfresco-Process-Services/24.4/Alfresco-Process-Services/Develop)
- [Material de entrenamiento de APS](https://github.com/muraai/aps-training-materials?tab=readme-ov-file)
- [campos de formulario personalizados](https://connect.hyland.com/t5/alfresco-blog/developer-series-custom-form-fields/ba-p/134665)
- [Personalización en tabla dinamica](https://connect.hyland.com/t5/alfresco-forum/dropdown-in-dynamic-table/m-p/14623)
- [Ejemplos de desarollo](https://github.com/cijujoseph/activiti-examples/tree/master)
- [AngularJS](https://docs.angularjs.org/api)
- [cliente de aps rest api](https://github.com/gravitonian/aps-rest-api-java-client)
- [ReST call](https://connect.hyland.com/t5/alfresco-blog/rest-call-task-101/ba-p/132329)
- [get form fields values in a form in aps](https://howtobrothers.com/2018/01/07/how-to-get-form-fields-values-in-a-form-in-alfresco-process-services/)
- [aps sdk](https://github.com/OpenPj/alfresco-process-services-project-sdk/tree/master)
- [business data integration made easy with data models](https://connect.hyland.com/t5/alfresco-blog/business-data-integration-made-easy-with-data-models/ba-p/135150)
- [Desarrollo eficiente de plantillas para Alfresco Process Services](https://connect.hyland.com/t5/alfresco-archive/efficient-stencil-development-for-alfresco-process-services/td-p/152123)