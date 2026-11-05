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

# Ejemplos ejecutables

Varias secciones incluyen una carpeta `ejemplos/` con procesos BPMN y un script `probar.py` que los despliega, los recorre, **comprueba el resultado** (líneas `OK` / `FALLO`) y limpia lo que creó. Todos se probaron en APS 24.4.0.

| Sección | Ejemplo | Qué comprueba |
|---|---|---|
| API ReST | [`API-ReST/ejemplos/recorrido.py`](./API-ReST/ejemplos/recorrido.py) | pública vs motor, `tenantId`, publicar una app por API, ciclo completo, paginación, bug de tareas históricas con variables, capacidades |
| Listeners | [`Listeners/ejemplos/`](./Listeners/ejemplos/) | execution/task listeners con script y expresiones |
| Service Task | [`ServiceTask/ejemplos/`](./ServiceTask/ejemplos/) | expresiones con beans y listas blancas |
| Script Task | [`CustomScriptTask/ejemplos/`](./CustomScriptTask/ejemplos/) | groovy y javascript, `resultVariable` |
| Mensajes y señales | [`MessageAndSignals/ejemplos/`](./MessageAndSignals/ejemplos/) | mensaje a una ejecución, señal de difusión, inicio por mensaje/señal |
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