# Modelos de datos personalizados

Las mejores prácticas de gestión de procesos empresariales (BPM) suelen sugerir que la solución BPM no sea el sistema de registro. En particular, los datos empresariales necesarios para la solución empresarial digital deben existir en otros almacenes de datos fuera del almacén de persistencia que utiliza el propio motor BPM.

Los datos empresariales que se utilizan o crean durante la ejecución de un proceso empresarial deben existir y mantenerse en uno o más almacenes de datos externos (por ejemplo, RDBMS, NoSQL, etc.). Por lo tanto, para simplificar y acelerar el desarrollo de soluciones empresariales digitales a escala empresarial, Alfresco Process Services (edición empresarial de Alfresco de Activiti Community Edition (código abierto)) proporciona un componente importante y valioso llamado "modelos de datos".

Alfresco process service admite la integración con base de datos externas. Es posible realizar operaciones **CRUD** durante la ejecución de una instancia de proceso. (**Nota**: operación ``Delete`` no esta soportado actualmente).

## Ventajas

Se presentan algunos de los puntos críticos que escuchamos con bastante frecuencia de los modeladores de procesos de negocios, analistas, desarrolladores, etc.

- Los sistemas de mi organización son muy difíciles de integrar en nuestros procesos.
- Las capacidades de modelado de datos en nuestra plataforma BPM existente son altamente técnicas y tienen una curva de aprendizaje pronunciada.
- Como analista/modelador, me encantaría tener algunas características en el producto que me permitan modelar mi modelo de datos SoR (Sistema de Registros) en la plataforma de procesos.
- Nuestra organización cuenta con API REST muy maduras y bien definidas en todos nuestros sistemas de TI. Sin embargo, como analista de negocios y modelador de procesos, mapear las solicitudes y respuestas de las API REST es un trabajo demasiado técnico para mí.
- Contamos con servicios web bien definidos y reutilizables basados ​​en estándares como SOAP, POX, etc. en nuestra organización. Deseamos que nuestro sistema BPM tenga capacidades integradas que nos permitan escribir componentes reutilizables y compatibles con el negocio sobre estos servicios web.
- Hemos estado usando la versión comunitaria de Activiti durante mucho tiempo. Tenemos mucho código Java reutilizable que nos permite integrar nuestros procesos con nuestros sistemas de TI. 
- Para comprender esa integración de sistemas externos, a menudo tenemos que investigar el código fuente Java asociado con el proceso. Al pasar de la comunidad a la empresa, sería realmente bueno si pudiéramos representar visualmente esas estructuras de datos en el modelador BPMN y tener una integración directa de esos componentes con otros componentes del proceso, como formularios, reglas, etc.
- Como persona de negocios, cuando reviso un diagrama BPMN veo muchas tareas de servicio con lógica Java oculta en él. Cada vez que hago esto, tengo que recurrir a un desarrollador para entender los componentes de Java y averiguar los campos de entrada y salida de esos componentes. ¡Esto me parece tedioso!
- Somos una organización con muchas aplicaciones tradicionales de dos niveles (cliente->base de datos) sin API. Necesitamos que nuestros procesos comerciales se comuniquen directamente con las bases de datos de nuestras aplicaciones.
- Utilizamos Alfresco Content Services como nuestro sistema de registros de documentos. ¿Cuáles son las capacidades de integración de APS con Alfresco Content Services?
- El modelo de datos es el componente que puede abordar todas las inquietudes y problemas mencionados anteriormente de una manera elegante, simple y fácil de usar, sin las complejidades de componentes similares que normalmente se encuentran en otros productos de grandes proveedores de BPM.

## Ejemplo de modelo de datos personalizado

> Uso de un modelo de datos personalizado para que un proceso empresarial se comunique con Elasticsearch. En este ejemplo, se utiliza como fuente de datos la instancia de Elasticsearch integrada que viene con Alfresco Process Services (Enterprise Activiti).

### descripción generla de los procesos utilizados

1. Proceso **Create Policy**: proceso de póliza de seguro mediante el cual un usuario crea una póliza. Como parte del proceso, los datos de la póliza se almacenan en una fuente externa a través de DataModel. En este ejemplo, la fuente externa es ElasticSearch.

2. Proceso **Claims Process**: proceso de reclamaciones mediante el cual un usuario realiza una reclamación. En este proceso, el componente DataModel se utiliza para realizar lo siguiente:
    * Obtener detalles de la póliza y mostrarlo a un revisor.
    * Validar los datos ingresados por el usuario contra lo registrado en la póliza utilizando Tablas de decisión y solicitar al usuario que actualice los detalles de la póliza.
    * Cree una entrada de reclamaciones en el sistema de reclamaciones externo. En este ejemplo la fuente externa es ElasticSearch.

### Pasos de configuración

1. Habilitar la compresión HTTP en las respuestas de ElasticSearch, configurar el parametro ``http.compression : true`` en el archivo de configuración elasticsearch.yml.

2. Implemente las siguientes clases para configurar los procesos de modelo de datos personalizado.

    ```xml
     <!-- Dependencia para jackson-core -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-core</artifactId>
        <version>2.12.3</version>
    </dependency>
    <!-- Dependencia para jackson-databind -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.12.3</version>
    </dependency>
    ```
    ```java
    package com.activiti.extension.bean;

    import com.activiti.api.datamodel.AlfrescoCustomDataModelService;
    import com.activiti.model.editor.datamodel.DataModelDefinitionRepresentation;
    import com.activiti.model.editor.datamodel.DataModelEntityRepresentation;
    import com.activiti.runtime.activiti.bean.datamodel.AttributeMappingWrapper;
    import com.activiti.variable.VariableEntityWrapper;
    import com.fasterxml.jackson.core.JsonProcessingException;
    import com.fasterxml.jackson.databind.JsonNode;
    import com.fasterxml.jackson.databind.ObjectMapper;
    import com.fasterxml.jackson.databind.node.ObjectNode;
    import org.apache.commons.lang3.StringUtils;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.beans.factory.annotation.Value;
    import org.springframework.stereotype.Service;

    import java.io.IOException;
    import java.util.HashMap;
    import java.util.List;
    import java.util.Map;

    @Service
    public class CustomDataModelServiceImpl implements AlfrescoCustomDataModelService {

        private static Logger logger = LoggerFactory.getLogger(CustomDataModelServiceImpl.class);
        private static final String POLICY_ENTITY_NAME = "Policy";
        private static final String CLAIM_ENTITY_NAME = "Claim";

        private static final String POLICY_INDEX = "policyindex";
        private static final String CLAIM_INDEX = "claimindex";

        @Value("${elastic-search.rest-client.schema}://${elastic-search.rest-client.address}:${elastic-search.rest-client.port}/")
        private String ELASTIC_BASE;

        @Autowired
        protected ObjectMapper objectMapper;

        @Autowired
        private ElasticHTTPClient elasticHTTPClient;

        @Override
        public ObjectNode getMappedValue(DataModelEntityRepresentation entityDefinition, String fieldName,
                Object fieldValue) {
            
            String esUrl;
            if (StringUtils.equals(entityDefinition.getName(), POLICY_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+ POLICY_INDEX+"/_doc/";
            } else if (StringUtils.equals(entityDefinition.getName(), CLAIM_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+CLAIM_INDEX+"/_doc/";
            } else{
                return null;
            }

            String esResponse = elasticHTTPClient
                    .execute(esUrl + (String) fieldValue, null, "GET");
            JsonNode responseNode;
            try {
                
                responseNode = objectMapper.readTree(esResponse);
                if (responseNode.findValue("found").asText().equals("true")) {
                    ObjectNode policyNode = (ObjectNode) objectMapper
                            .readTree(objectMapper.writeValueAsString(responseNode.get("_source")));
                    return policyNode;
                }
            } catch (JsonProcessingException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            
            return null;
        }

        @Override
        public VariableEntityWrapper getVariableEntity(String keyValue, String variableName, String processDefinitionId,
                DataModelEntityRepresentation entityValue) {
            

            String esUrl;
            if (StringUtils.equals(entityValue.getName(), POLICY_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+ POLICY_INDEX+"/_doc/";
            } else if (StringUtils.equals(entityValue.getName(), CLAIM_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+CLAIM_INDEX+"/_doc/";
            } else{
                return null;
            }
            if (keyValue != null) {
                String esResponse = elasticHTTPClient
                        .execute(esUrl + (String)keyValue, null, "GET");
                JsonNode responseNode;
                try {
                    
                    responseNode = objectMapper.readTree(esResponse);
                    if (responseNode.findValue("found").asText().equals("true")) {
                        ObjectNode policyNode = (ObjectNode) objectMapper
                                .readTree(objectMapper.writeValueAsString(responseNode.get("_source")));
                        VariableEntityWrapper variableEntityWrapper = new VariableEntityWrapper(variableName,
                                processDefinitionId, entityValue);
                        variableEntityWrapper.setEntity(policyNode);
                        variableEntityWrapper.setKey(keyValue);	
                        return variableEntityWrapper;
                    }
                } catch (JsonProcessingException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
            }

            return null;
        }

        @Override
        public String storeEntity(List<AttributeMappingWrapper> attributeDefinitionsAndValues,
                DataModelEntityRepresentation entityDefinition, DataModelDefinitionRepresentation dataModel) {
            logger.info("create policy start");
            String esUrl;
            String idAttribute;
            if (StringUtils.equals(entityDefinition.getName(), POLICY_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+ POLICY_INDEX+"/_doc/";
                idAttribute = "policyId";
            } else if (StringUtils.equals(entityDefinition.getName(), CLAIM_ENTITY_NAME)) {
                esUrl = ELASTIC_BASE+CLAIM_INDEX+"/_doc/";
                idAttribute = "claimId";
            } else{
                return null;
            }
            // Set up a map of all the column names and values
            Map<String, Object> parameters = new HashMap<String, Object>();
            for (AttributeMappingWrapper attributeMappingWrapper : attributeDefinitionsAndValues) {
                System.out.println(attributeMappingWrapper.getAttribute().getName());
                System.out.println(attributeMappingWrapper.getValue());
                parameters.put(attributeMappingWrapper.getAttribute().getName(), attributeMappingWrapper.getValue());
            }
            try {
                String jsonString = new ObjectMapper().writeValueAsString(parameters);
                String response = elasticHTTPClient.execute(
                        esUrl + (String) parameters.get(idAttribute),
                        jsonString, "POST");
                logger.info(response);
                return (String) parameters.get(idAttribute);
            } catch (JsonProcessingException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            return null;
        }
    }
    ```


    ```java
    package com.activiti.extension.bean;

    import java.io.IOException;
    import java.util.Date;

    import org.activiti.engine.ActivitiException;
    import org.apache.http.HttpResponse;
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpGet;
    import org.apache.http.client.methods.HttpPost;
    import org.apache.http.client.methods.HttpPut;
    import org.apache.http.client.methods.HttpRequestBase;
    import org.apache.http.entity.StringEntity;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.impl.conn.PoolingHttpClientConnectionManager;
    import org.apache.http.message.BasicHeader;
    import org.apache.http.protocol.HTTP;
    import org.apache.http.util.EntityUtils;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.core.env.Environment;
    import org.springframework.stereotype.Component;

    // http client bean with connection pool
    @Component("elasticHTTPClient")
    public class ElasticHTTPClient {

        protected static final Logger logger = LoggerFactory.getLogger(ElasticHTTPClient.class);
        private final CloseableHttpClient httpClient;

        public ElasticHTTPClient() {

            PoolingHttpClientConnectionManager cm = new PoolingHttpClientConnectionManager();
            cm.setDefaultMaxPerRoute(200);
            cm.setMaxTotal(200);
            httpClient = HttpClients.custom().setConnectionManager(cm).build();
        }

        public String execute(String restEndpointURI, String requestJson, String method) {

            String jsonString = null;
            CloseableHttpResponse response = null;
            HttpRequestBase httpRequest;
            if(method.equals("POST")){
                httpRequest = new HttpPost(restEndpointURI);
            }
            else if(method.equals("PUT")){
                httpRequest = new HttpPut(restEndpointURI);
            }
            else{
                httpRequest = new HttpGet(restEndpointURI);
            }
            try {
                if(method.equals("POST") || method.equals("PUT")){
                    StringEntity input = new StringEntity(requestJson, "UTF-8");
                    System.out.println("requestJson: " +requestJson);
                    input.setContentType(new BasicHeader(HTTP.CONTENT_TYPE, "application/json"));
                    input.setContentEncoding("UTF-8");
                    if(method.equals("POST")) {
                        ((HttpPost) httpRequest).setEntity(input);
                    }
                    else {
                        ((HttpPut) httpRequest).setEntity(input);
                    }
                }

                Long httpStartTime = new Date().getTime();
                response = (CloseableHttpResponse) executeHttpRequest(httpRequest, method);
                logger.debug("Total HTTP Execution Time: " + ((new Date()).getTime() - httpStartTime));

                try {
                    jsonString = EntityUtils.toString(response.getEntity());
                } catch (Exception e) {
                    logger.error("error while parsing JSON response: " + jsonString, e);
                }

            } finally {
                try {
                    if (response != null) {
                        response.close();
                    }
                } catch (IOException e) {
                    logger.error("Failed to close HTTP response after invoking: "+  method + " "+ restEndpointURI, e);
                }

                if (httpRequest != null) {
                    httpRequest.releaseConnection();
                } else {
                    logger.debug("Could not release connection.");
                }
            }

            return jsonString;
        }

        protected HttpResponse executeHttpRequest(HttpRequestBase httpRequest, String method) {

            CloseableHttpResponse response = null;
            try {
                response = httpClient.execute(httpRequest);
                System.out.println("response: "+ response);
            } catch (IOException e) {
                throw new ActivitiException("error while executing http request: " + method + " "+ httpRequest.getURI(), e);
            }

            if (response.getStatusLine().getStatusCode() >= 400) {
                throw new ActivitiException("error while executing http request " + method + " "+ httpRequest.getURI()
                        + " with status code: " + response.getStatusLine().getStatusCode());
            }
            return response;
        }

    }
    ```


3. Importe la aplicación llamado "InsuranceDemoApp.zip" en su servicio de APS y públiquelo. [Ver Aplicación](InsuranceDemoApp.md)

### Pasos de configuración

1. Inicie el proceso **Create Policy** completando los valores en el formulario de inicio.

2. Inicie el proceso de **Claims Process** utilizando el ``Policy ID`` utilizado en el proceso anterior de **Create Policy**. Al crear un proceso **Claims Process**, ingrese un correo electrónico y un número de contacto del cliente diferentes a los utilizados en el proceso de **Create Policy**. Esto creará una tarea para que el usuario actualice la póliza con la información correcta.

3. Ahora, vaya al formulario de la tarea **Review Claim** para ver ``policyDetails.customerName``, ``policyDetails.contactNumber``, ``policyDetails.customerEmail`` que se obtienen de Elasticsearch a través de Datamodel. Si hay una tarea **Update Policy** junto con **Review Claim**, complete esta tarea antes de completar **Review Claim** actualizando el correo electrónico y el número de contacto con un nuevo valor. Ahora, vaya a la tarea **Review Claim** y vea el valor que actualizó a través de **Update Policy**  que se muestra en los campos ``policyDetails.contactNumber``, ``policyDetails.customerEmail``.

4. Como parte del proceso de reclamaciones, también se está creando una entrada de reclamaciones en Elasticsearch utilizando el modelo de datos.

Para ver los datos directamente en la fuetne de datos externa se puede utilizar las siguientes url:

```
http://localhost:9200/_nodes/settings?pretty información de elasticsearch
http://localhost:9200/policyindex/_doc/policyId ingresado en el formulario "create Policy" del evento de inicio de "Create Policy"
http://localhost:9200/claimindex/_doc/claimId  ingresado en la tarea **Review Claim**
```

## Resumen

- Los modelos de datos le permiten separar la integración de datos del modelado de procesos de negocio. En otras palabras, el modelado de procesos se hace más fácil con los modelos de datos, ya que le permiten ocultar la complejidad de implementación de los modelos de procesos.
- Los modelos de datos se integran con todos los demás componentes de modelado, como formularios, tablas de decisiones, etc. disponibles en APS, lo que reduce el tiempo de comercialización de sus soluciones de procesos de negocio.
- Los modelos de datos le permiten crear objetos/componentes de entidad de dominio reutilizables que, a su vez, pueden reutilizarse de manera uniforme en múltiples procesos.
- El modelo de datos es una alternativa de integración amigable para los negocios disponible en APS.



