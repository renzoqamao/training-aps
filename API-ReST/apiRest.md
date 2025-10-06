# Process Services ReST API

La API ReST expone las operaciones genéricas de Process Engine. También incluye un conjunto dedicado de puntos finales de API ReST para funciones específicas de Process Services.

> **Nota**: También existe una API ReST interna que la interfaz de usuario de JavaScript utiliza como puntos finales de ReST. NO utilice esta API, ya que las URL de la API ReST pueden modificar el producto para utilizar funciones no compatibles. Además, la API ReST interna utiliza un mecanismo de autenticación diferente adaptado al uso del navegador web.

## CORS 
Las soluciones que utilizan las API REST de Process Services pueden estar en un dominio o puerto diferente. Esto se conoce como uso compartido de recursos de origen cruzado (CORS).De manera predeterminada, CORS no puede proporcionar un alto nivel de seguridad. Esto se puede aliviar mediante el uso de servidores proxy web que consoliden diferentes dominios y puertos o habilitando CORS en la configuración de Process Services.

Para habilitar el uso compartido de recursos de origen cruzado (CORS) en los servicios del proceso, configure la propiedad ``cors.enabled`` como true (verdadera) en el archivo ``activiti-app.properties``.


> **Nota**: Esta función solo es compatible con el servidor de aplicaciones tomcat.

### Configuración de CORS

Cuando CORS esta habilitado, las solicitudes CORS se pueden realizar a todos los endpoints de /activiti-app/api. Además, se ponen a disposición algunas propiedades adicionales que se pueden configurar para ajustar aún más CORS. Esto hará que CORS esté disponible solo para ciertos origenes o para restringir los métodos HTTP válidos que se pueden usar y los encabezados que se pueden enviar con solicitudes habiltiadas para CORS.

```properties
cors.enabled=false
cors.allowed.origin.patterns=*
cors.allowed.methods=GET,POST,HEAD,OPTIONS,PUT,DELETE
cors.allowed.headers=Authorization,Content-Type,Cache-Control,X-Requested-With,accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers,X-CSRF-Token
cors.exposed.headers=Access-Control-Allow-Origin,Access-Control-Allow-Credentials
cors.support.credentials=true
cors.preflight.maxage=10
```

| Propiedad                     | Descripción|
|-------------------------------|------------|
| cors.allowed.origins          | Especifica una lista de orígenes para los que se permiten solicitudes de origen cruzado. Un valor especificado puede ser un dominio específico, p. ej., https://domain32.com, o el valor especial definido por CORS * para todos los orígenes. Para las solicitudes previas al vuelo y reales coincidentes, el encabezado de respuesta Access-Control-Allow-Origin puede ser el valor del dominio coincidente o *. <br>  **Nota**: La especificación CORS no permite * cuando allowCredentials está configurado como verdadero y se debe utilizar cors.allowed.origin.patterns en su lugar|
| cors.allowed.origin.patterns  | La alternativa a cors.allowed.origins admite los patrones de orígenes más flexibles y * se puede utilizar en cualquier parte del nombre de host además de en las listas de puertos. Por ejemplo: https://*.domain32.com dominios que terminan en domain32.com, https://*.domain32.com:[8080, 8081] dominios que terminan en domain32.com en el puerto 8080 o 8081, y https://*.domain32.com:[\*]- dominios que terminan en domain32.com en cualquier puerto, incluido el puerto predeterminado. A diferencia de cors.allowed.origins, que solo admite * y no se puede utilizar con allowCredentials, cuando se coincide con un cors.allowed.origin.patterns, el encabezado de respuesta Access-Control-Allow-Origin se establece en el origen coincidente y no *, incluido el patrón. cors.allowed.origin.patterns se puede utilizar junto con setAllowCredentials(java.lang.Boolean) establecido en verdadero.    |
| cors.allowed.methods          | Configura qué solicitudes HTTP están permitidas. GET, POST, HEAD, OPTIONS, PUT, DELETE   |
| cors.allowed.headers          | Especifica los encabezados que se pueden configurar de forma manual o programática en los encabezados de solicitud, además de los que configura el agente de usuario (por ejemplo, Connection). Los valores predeterminados son: Authorization, Content-Type, Cache-Control, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers. X-CSRF-Token    |
| cors.exposed.headers          | Permite incluir en la lista blanca los encabezados a los que el cliente puede acceder desde el servidor. El valor predeterminado expone los siguientes encabezados: Access-Control-Allow-Origin, Access-Control-Allow-Credentials    |
| cors.support.credentials      | Determina si se permiten las cookies HTTP y las credenciales basadas en autenticación HTTP. El valor predeterminado es verdadero.    |
| cors.preflight.maxage         | Las solicitudes de verificación previa utilizan el método OPTIONS para verificar primero la disponibilidad del recurso y luego solicitarlo. Esta propiedad determina el tiempo máximo (en minutos) para almacenar en caché una solicitud de verificación previa. El valor predeterminado es 10.   |

## Uso del explorador de ReST API

El explorador de API REST se basa en la iniciativa OpenAPI (Swagger) y proporciona una interfaz para la API REST. Puede explorar los puntos finales de API disponibles y las operaciones de prueba disponibles dentro de un grupo de API en particular.

Acceda al explorador de API REST en este enlace: ``http://localhost:8080/activiti-app/api-explorer.html``.

También hay un explorador de API REST público. ``https://activiti.alfresco.com/activiti-app/api-explorer.html#/ ``.


## Process Services ReST API

La API REST expone datos y operaciones específicos de Process Services.

A diferencia de la API REST de Process Engine, la API REST de Process Services puede ser invocada por cualquier usuario. Las siguientes secciones describen los puntos finales de la API REST compatibles.


### información del server

Para recuperar información sobre la versión de Process Services, utilice el siguiente comando:

```
GET api/enterprise/app-version
```

Response:

```
{
   "edition": "Alfresco Activiti Enterprise BPM Suite",
   "majorVersion": "1",
   "revisionVersion": "0",
   "minorVersion": "2",
   "type": "bpmSuite",
}
```

### Perfil

Esta operación devuelve información de la cuenta del usuario actual. Es útil para obtener el nombre, el correo electrónico, los grupos de los que forma parte el usuario, la foto del usuario, etc.

```
GET api/enterprise/profile
```

Response:

```
{
     "tenantId": 1,
     "firstName": "John",
     "password": null,
     "type": "enterprise",
     "company": null,
     "externalId": null,
     "capabilities": null,
     "tenantPictureId": null,
     "created": "2015-01-08T13:22:36.198+0000",
     "pictureId": null,
     "latestSyncTimeStamp": null,
     "tenantName": "test",
     "lastName": "Doe",
     "id": 1000,
     "lastUpdate": "2015-01-08T13:34:22.273+0000",
     "email": "johndoe@alfresco.com",
     "status": "active",
     "fullname": "John Doe",
     "groups": [
          {
               "capabilities": null,
               "name": "analytics-users",
               "tenantId": 1,
               "users": null,
               "id": 1,
               "groups": null,
               "externalId": null,
               "status": "active",
               "lastSyncTimeStamp": null,
               "type": 0,
               "parentGroupId": null
          },
          {
               "capabilities": null,
               "name": "Engineering",
               "tenantId": 1,
               "users": null,
               "id": 2000,
               "groups": null,
               "externalId": null,
               "status": "active",
               "lastSyncTimeStamp": null,
               "type": 1,
               "parentGroupId": null
          },
          {
               "capabilities": null,
               "name": "Marketing",
               "tenantId": 1,
               "users": null,
               "id": 2001,
               "groups": null,
               "externalId": null,
               "status": "active",
               "lastSyncTimeStamp": null,
               "type": 1,
               "parentGroupId": null
          }
     ]
}
```

Para actualizar la información del usuario (nombre, apellido o correo electrónico):

```
POST api/enterprise/profile
```

```
{
    "firstName" : "John",
    "lastName" : "Doe",
    "email" : "john@alfresco.com",
    "company" : "Alfresco"
}
```

Para obtener la imagen del usuario, utilice la siguiente llamada REST:

```
GET api/enterprise/profile-picture
```

Para cambiar la contraseña: 
```
POST api/enterprise/profile-password
```

```
{
    "oldPassword" : "12345",
    "newPassword" : "6789"
}
```


### Runtime Apps

Cuando un usuario inicia sesión en Process Services, se muestra la página de inicio que contiene todas las aplicaciones que el usuario puede ver y usar.

La solicitud de API REST correspondiente para obtener esta información es:


```
GET api/enterprise/runtime-app-definitions
```

```
{
     "size": 3,
     "total": 3,
     "data": [
          {
               "deploymentId": "26",
               "name": "HR processes",
               "icon": "glyphicon-cloud",
               "description": null,
               "theme": "theme-6",
               "modelId": 4,
               "id": 1
          },
          {
               "deploymentId": "2501",
               "name": "Sales onboarding",
               "icon": "glyphicon-asterisk",
               "description": "",
               "theme": "theme-1",
               "modelId": 1002,
               "id": 1000
          },
          {
               "deploymentId": "5001",
               "name": "Engineering app",
               "icon": "glyphicon-asterisk",
               "description": "",
               "theme": "theme-1",
               "modelId": 2001,
               "id": 2000
          }
     ],
     "start": 0
}
```
Las propiedades id y modelId de las aplicaciones son importantes aquí, ya que se utilizan en varias operaciones que se describen a continuación.

### App Definition List

Cuando un usuario inicia sesión en Process Services, se muestra la página de inicio que contiene todas las aplicaciones que el usuario puede ver y usar.

La solicitud de API REST correspondiente para obtener esta información es:

```
GET api/enterprise/runtime-app-definitions
```

```
{
     "size": 3,
     "total": 3,
     "data": [
          {
               "deploymentId": "26",
               "name": "HR processes",
               "icon": "glyphicon-cloud",
               "description": null,
               "theme": "theme-6",
               "modelId": 4,
               "id": 1
          },
          {
               "deploymentId": "2501",
               "name": "Sales onboarding",
               "icon": "glyphicon-asterisk",
               "description": "",
               "theme": "theme-1",
               "modelId": 1002,
               "id": 1000
          },
          {
               "deploymentId": "5001",
               "name": "Engineering app",
               "icon": "glyphicon-asterisk",
               "description": "",
               "theme": "theme-1",
               "modelId": 2001,
               "id": 2000
          }
     ],
     "start": 0
}
```

Las propiedades id y modelId de las aplicaciones son importantes aquí, ya que se utilizan en varias operaciones que se describen a continuación.


### Process Definitions

Obtenga una lista de definiciones de procesos (visibles dentro del inquilino del usuario):

```
GET api/enterprise/process-definitions
```

```
{
     "size": 5,
     "total": 5,
     "data": [
          {
            "id": "demoprocess:1:7504",
            "name": "Demo process",
            "description": null,
            "key": "demoprocess",
            "category": "http://www.activiti.org/test",
            "version": 1,
            "deploymentId": "7501",
            "tenantId": "tenant_1",
            "hasStartForm": true
          },
          ...
     ],
     "start": 0
}
```
Los siguientes parámetros están disponibles:

* latest: Un valor booleano que indica que solo se deben devolver las últimas versiones de las definiciones de proceso.
* appDefinitionId: Devuelve las definiciones de proceso que pertenecen a una aplicación determinada.

Para obtener los iniciadores candidatos asociados a una definición de proceso:
```
GET api/enterprise/process-definitions/{processDefinitionId}/identitylinks/{family}/{identityId}
```
Donde:

* processDefinitionId: El ID de la definición de proceso para obtener los vínculos de identidad.
* family: Indica grupos o usuarios, según el tipo de vínculo de identidad.
identityId: El ID de la identidad.

Para agregar un iniciador candidato a una definición de proceso:

```
POST api/enterprise/process-definitions/{processDefinitionId}/identitylinks
```
Cuerpo de la solicitud (usuario):

```
{
"user" : "1"
}
```
Cuerpo de la solicitud (grupo):
```
{
"group" : "1001"
}
```

Para eliminar un iniciador candidato de una definición de proceso:

```
DELETE api/enterprise/process-definitions/{processDefinitionId}/identitylinks/{family}/{identityId}
```

### Start Form

Cuando la definición de proceso tiene un formulario de inicio (hasStartForm es verdadero como en la llamada anterior), el formulario de inicio se puede recuperar de la siguiente manera:

```
GET api/enterprise/process-definitions/{process-definition-id}/start-form
```
Ejemplo de respuesta:

```
{
  "processDefinitionId": "p1:2:2504",
  "processDefinitionName": "p1",
  "processDefinitionKey": "p1",
  "fields": [
    {
      "fieldType": "ContainerRepresentation",
      "id": "container1",
      "name": null,
      "type": "container",
      "value": null,
      "required": false,
      "readOnly": false,
      "overrideId": false,
      "placeholder": null,
      "optionType": null,
      "hasEmptyValue": null,
      "options": null,
      "restUrl": null,
      "restIdProperty": null,
      "restLabelProperty": null,
      "layout": null,
      "sizeX": 0,
      "sizeY": 0,
      "row": 0,
      "col": 0,
      "visibilityCondition": null,
      "fields": {
        "1": [
          {
            "fieldType": "FormFieldRepresentation",
            "id": "label1",
            "name": "Label1",
            "type": "text",
            "value": null,
            "required": false,
            "readOnly": false,
            "overrideId": false,
            "placeholder": null,
            "optionType": null,
            "hasEmptyValue": null,
            "options": null,
            "restUrl": null,
            "restIdProperty": null,
            "restLabelProperty": null,
            "layout": {
              "row": 0,
              "column": 0,
              "colspan": 1
            },
            "sizeX": 1,
            "sizeY": 1,
            "row": 0,
            "col": 0,
            "visibilityCondition": null
          }
        ],
        "2": [ ]
      }
    },
    {
      "fieldType": "DynamicTableRepresentation",
      "id": "label21",
      "name": "Label 21",
      "type": "dynamic-table",
      "value": null,
      "required": false,
      "readOnly": false,
      "overrideId": false,
      "placeholder": null,
      "optionType": null,
      "hasEmptyValue": null,
      "options": null,
      "restUrl": null,
      "restIdProperty": null,
      "restLabelProperty": null,
      "layout": {
        "row": 10,
        "column": 0,
        "colspan": 2
      },
      "sizeX": 2,
      "sizeY": 2,
      "row": 10,
      "col": 0,
      "visibilityCondition": null,
      "columnDefinitions": [
        {
          "id": "p2",
          "name": "c2",
          "type": "String",
          "value": null,
          "optionType": null,
          "options": null,
          "restUrl": null,
          "restIdProperty": null,
          "restLabelProperty": null,
          "required": true,
          "editable": true,
          "sortable": true,
          "visible": true
        }
      ]
    }
  ],
  "outcomes": [ ]
}
```

### Start Process Instance

Para iniciar instancias de proceso, utilice:
```
POST api/enterprise/process-instances
```
Con un cuerpo json que contenga las siguientes propiedades:

* processDefinitionId: El identificador de definición de proceso. No lo utilice con processDefinitionKey.
* processDefinitionKey: La clave de definición de proceso. No la utilice con processDefinitionId.
* name: El nombre que se le dará a la instancia de proceso creada.
* values: Un objeto JSON con el Id del campo de formulario y los valores del campo de formulario. El Id del campo de formulario se recupera de la llamada de inicio del formulario (ver arriba).
* outcome: Si el formulario de inicio tiene resultados, este es uno de esos valores.
* variables: Contiene una matriz JSON de variables. Los valores y los resultados no se pueden utilizar con variables.

La respuesta contendrá los detalles de la instancia de proceso, incluido el ID.

Una vez iniciado, el formulario completo (si está definido) se puede obtener utilizando:
```
GET /enterprise/process-instances/{processInstanceId}/start-form
```

### Process instance List

Para obtener la lista de instancias de proceso:
```
POST api/enterprise/process-instances/query
```
con un cuerpo json que contenga los parámetros de consulta. Los siguientes parámetros son posibles:

* processDefinitionId
* appDefinitionId
* state (los valores posibles son running, finished y all)
* sort (los valores posibles son created-desc, created-asc, ended-desc, ended-asc)
* start (para paginación, predeterminado 0)
* size (para paginación, predeterminado 25)

Ejemplo de respuesta:
```
{
"size": 6,
"total": 6,
"start": 0,
"data":[
{"id": "2511", "name": "Test step - January 8th 2015", "businessKey": null, "processDefinitionId": "teststep:3:29"...},
...
]
}
```

Para obtener una instancia de proceso:
```
GET api/enterprise/process-instances/{processInstanceId}
```
Para obtener el diagrama de una instancia de proceso:
```
GET api/enterprise/process-instances/{processInstanceId}/diagram
```
Para eliminar una instancia de proceso:
```
DELETE api/enterprise/process-instances/{processInstanceId}
```
Para suspender una instancia de proceso:
```
PUT api/enterprise/process-instances/{processInstanceId}/suspend
```
Para activar una instancia de proceso:
```
PUT api/enterprise/process-instances/{processInstanceId}/activate
```
Donde, processinstanceId es el Id de la instancia de proceso.

### Get Process Instance Details

```
GET api/enterprise/process-instances/{processInstanceId}
```

### Delete a Process 

```
DELETE api/enterprise/process-instances/{processInstanceId}
```

### Process Instance variables

Una instancia de proceso puede tener varias variables.

Para obtener las variables de la instancia de proceso:
```
GET api/enterprise/process-instances/{processInstanceId}/variables
```
Donde, processInstanceId es el Id de la instancia de proceso.

Para crear variables de instancia de proceso:
```
PUT api/enterprise/process-instances/{processInstanceId}/variables
```
Para actualizar variables existentes en una instancia de proceso:
```
PUT api/enterprise/process-instances/{processInstanceId}/variables
```
Ejemplo de respuesta:
```
{
"name": "myVariable",
"type": "string",
"value": "myValue"
}
```
Donde:

* name: nombre de la variable
* type: tipo de variable, como una cadena
* value: valor de la variable

Para actualizar una sola variable en una instancia de proceso:
```
PUT api/enterprise/process-instances/{processInstanceId}/variables/{variableName}
```
Para obtener una sola variable en una instancia de proceso:
```
GET api/enterprise/process-instances/{processInstanceId}/variables/{variableName}
```
Para obtener todas las variables de instancia de proceso:
```
GET api/enterprise/process-instances/{processInstanceId}/variables
```
Para obtener una variable de instancia de proceso específica:
```
GET api/enterprise/process-instances/{processInstanceId}/variables/{variableName}
```
Para eliminar una variable de instancia de proceso específica:
```
DELETE api/enterprise/process-instances/{processInstanceId}/variables/{variableName}
```

### Task List

Para devolver una lista de tareas, utilice:

```
POST api/enterprise/tasks/query
```
que incluye un cuerpo JSON que contiene los parámetros de consulta.

Los siguientes parámetros están disponibles:

* appDefinitionId
* processInstanceId
* processDefinitionId
* text (el nombre de la tarea se filtrará con esto, utilizando la semántica similar: %text%)
* assignment
    * assignee : donde el usuario actual es el asignado
    * candidate: donde el usuario actual es un candidato a la tarea
    * group_x: donde la tarea está asignada a un grupo del cual el usuario actual es miembro. Los grupos se pueden obtener a través del punto final REST del perfil
    * sin valor: donde está involucrado el usuario actual
* state (completado o activo)
* includeProcessVariables (establecido en verdadero para incluir variables de proceso en la respuesta)
* includeTaskLocalVariables (establecido en verdadero para incluir variables de tarea en la respuesta)
* sort (los valores posibles son created-desc, created-asc, due-desc, due-asc)
* start (para paginación, predeterminado 0)
* size (para paginación, predeterminado 25)

Ejemplo de respuesta:

```
{
    "size": 6,
    "total": 6,
    "start": 0,
    "data":[
            {
                "id": "2524",
                "name": "Task",
                "description": null,
                "category": null,
                "assignee":{"id": 1, "firstName": null, "lastName": "Administrator", "email": "admin@app.activiti.com"},
                "created": "2015-01-08T10:58:37.193+0000",
                "dueDate": null,
                "endDate": null,
                "duration": null,
                "priority": 50,
                "processInstanceId": "2511",
                "processDefinitionId": "teststep:3:29",
                "processDefinitionName": "Test step",
                "processDefinitionDescription": null,
                "processDefinitionKey": "teststep",
                "processDefinitionCategory": "http://www.activiti.org/test",
                "processDefinitionVersion": 3,
                "processDefinitionDeploymentId": "26",
                "formKey": "5"
            }
            ...
    ]
}
```
## Task Details

```
GET api/enterprise/tasks/{taskId}
```
La respuesta es similar a la respuesta de la lista.


## Task Form
```
GET api/enterprise/task-forms/{taskId}
```
La respuesta es similar a la respuesta del formulario de inicio.

Para recuperar los valores de los campos de formulario que se completan a través de un back-end REST:
```
GET api/enterprise/task-forms/{taskId}/form-values/{field}
```
Que devuelve una lista de valores de campos de formulario

Para completar un formulario de tarea:
```
POST api/enterprise/task-forms/{taskId}
```
con un cuerpo json que contiene:

* values: Un objeto json con el ID del campo de formulario - valores del campo de formulario. El Id del campo de formulario se recupera de la llamada al formulario de inicio (ver arriba).
* outcome: Recupera los valores de resultado si se definen en el formulario de inicio.
Para guardar un formulario de tarea:
```
POST api/enterprise/task-forms/{taskid}/save-form
```
Ejemplo de respuesta:
```
{

"values": {"formtextfield": "snicker doodle"},
"numberfield": "6",
"radiobutton": "red"

}
```
Donde el cuerpo json contiene:

* values: un objeto json con el ID del campo de formulario - valores del campo de formulario. 

El ID del campo de formulario se recupera de la llamada Start Form (ver arriba).
Para recuperar una lista de variables asociadas con un formulario de tarea:

```
GET api/enterprise/task-forms/{taskid}/variables
```

Ejemplo de respuesta:

```
[
{
"id": "initiator",
"type": "string",
"value": "3205"
},
{
"id": "FormField2",
"type": "string",
"value": "TestVariable2"
},
{
"id": "FormField1",
"type": "string",
"value": "TestVariable1"
}
]
```