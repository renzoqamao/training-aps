# ReST Endpoints Personalizados

Es posible agregar ReST endpoints personalizados a BPM Suite, tanto en la API ReST normal (utilizada por la interfaz de usuario HTML/Javascript de BPM Suite) como en la API Pública (utilizando la autenticación básica en lugar de cookies).

La API ReST se crea con Spring MVC, [documentación de Spring MVC](http://docs.spring.io/spring/docs/current/spring-framework-reference/html/mvc.html) para saber como crear nuevo Java Beans para implementar los endpoints personalizados.

Es neceseario añadir la siguiente dependencia al archivo maven:
```xml
    <dependencies>
        <dependency>
            <groupId>com.activiti</groupId>
            <artifactId>activiti-app-rest</artifactId>
            <version>${suite.version}</version>
        </dependency>
    </dependencies>
```
A continuación se muestra un ejemplo muy simple. En este caso, se inyecta el ``TaskService`` de Process Services y se crea una respuesta personalizada. Por supuesto, esta lógica puede ser cualquier cosa.

```java
package com.activiti.extension.rest;

import com.activiti.domain.idm.User;
import com.activiti.security.SecurityUtils;
import org.activiti.engine.TaskService;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/rest/my-rest-endpoint")
public class MyRestEndpoint {

    @Autowired
    private TaskService taskService;

    @RequestMapping(method = RequestMethod.GET, produces = "application/json")
    public MyRestEndpointResponse executeCustonLogic() {

        User currentUser = SecurityUtils.getCurrentUserObject();
        long taskCount = taskService.createTaskQuery().taskAssignee(String.valueOf(currentUser.getId())).count();

        MyRestEndpointResponse myRestEndpointResponse = new MyRestEndpointResponse();
        myRestEndpointResponse.setFullName(currentUser.getFullName());
        myRestEndpointResponse.setTaskCount(taskCount);
        return myRestEndpointResponse;

    }

    private static final class MyRestEndpointResponse {

    	private String fullName = StringUtils.EMPTY;
        private long taskCount = -1;
        
        @SuppressWarnings("unused")
		public String getFullName() {
			return fullName;
		}
		public void setFullName(String fullName) {
			this.fullName = fullName;
		}
		
		@SuppressWarnings("unused")
		public long getTaskCount() {
			return taskCount;
		}
		public void setTaskCount(long taskCount) {
			this.taskCount = taskCount;
		}

    }

}
```
**Nota**: el bean debe estar en el paquete com.activiti.extension.rest para poder encontrarlo.

Cree un archivo jar que contenga esta clase y agréguelo a la ruta de clases.

Se agregará una clase como esta en el paquete com.activiti.extension.rest a los endpoint ReST de la aplicación (por ejemplo, para usar en la interfaz de usuario), que **utilizan el enfoque de cookies para determinar el usuario**. La URL se asignará a /app. Por lo tanto, si inicia sesión en la interfaz de usuario de BPM Suite, puede ir a http://localhost:8080/activiti-app/app/rest/my-rest-endpoint y ver el resultado del endpoint ReST personalizado:

```html
{"fullName":" Administrator","taskCount":8}
```

Para agregar un endpoint REST personalizado a la API ReST pública, protegido por **autenticación básica**, se debe colocar una clase similar en el paquete com.activiti.extension.api.

```java
package com.activiti.extension.api;

import com.activiti.domain.idm.User;
import com.activiti.security.SecurityUtils;
import org.activiti.engine.TaskService;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/enterprise/my-api-endpoint")
public class MyApiEndpoint {

    @Autowired
    private TaskService taskService;

    @RequestMapping(method = RequestMethod.GET, produces = "application/json")
    public MyRestEndpointResponse executeCustonLogic() {

        User currentUser = SecurityUtils.getCurrentUserObject();
        long taskCount = taskService.createTaskQuery().taskAssignee(String.valueOf(currentUser.getId())).count();

        MyRestEndpointResponse myRestEndpointResponse = new MyRestEndpointResponse();
        myRestEndpointResponse.setFullName(currentUser.getFullName());
        myRestEndpointResponse.setTaskCount(taskCount);
        return myRestEndpointResponse;

    }

    private static final class MyRestEndpointResponse {

        private String fullName = StringUtils.EMPTY;
        private long taskCount = -1;
        
        @SuppressWarnings("unused")
		public String getFullName() {
			return fullName;
		}
		public void setFullName(String fullName) {
			this.fullName = fullName;
		}
		
		@SuppressWarnings("unused")
		public long getTaskCount() {
			return taskCount;
		}
		public void setTaskCount(long taskCount) {
			this.taskCount = taskCount;
		}
    }
}
```

Tenga en cuenta que el endpoint debe tener ``/enterprise`` como primer elemento en la URL, ya que esto está configurado en SecurityConfiguration para estar protegido con autenticación básica (más específicamente, ``api/enterprise/*`` lo está).

A la que se puede acceder como a la API normal:

```cmd
curl -u admin@app.activiti.com:password http://localhost:8080/activiti-app/api/enterprise/my-api-endpoint

{"fullName":" Administrator","taskCount":8}

```

**Nota**: Debido a la carga de clases, actualmente no es posible colocar archivos jar con estos ReST endpoint personalizados en la ruta de clases global o común (por ejemplo, tomcat/lib para Tomcat). Deben colocarse en la ruta de clases de la aplicación web (por ejemplo, WEB-INF/lib).


# Anulaciones de seguridad para servicio ReST personalizado

Puede cambiar la configuración de seguridad predeterminada de los endpoints de la API REST implementando la interfaz ``com.activiti.api.security.AlfrescoApiSecurityOverride``. De manera predeterminada, los endpoints de la API REST utilizan el método de autenticación básica.

De manera similar, puede anular la configuración de seguridad predeterminada basada en cookies+token con los endpoints de REST regulares (aquellos que utiliza la IU) implementando la interfaz ``com.activiti.api.security.AlfrescoWebAppSecurityOverride``.

**Nota**: La aplicación web y la API utilizan la misma seguridad HTTP de Spring para la autenticación. Para distinguir las configuraciones de seguridad, debe especificar la ruta a la que se aplica la configuración. Estas utilizan /app y /api de manera predeterminada. Por ejemplo, la configuración de la API debe comenzar con lo siguiente:

httpSecurity.antMatcher("/api/**")

## Ejemplo de creación de enpoint ReST Público

Creamos el siguiente componente que implementa ``AlfrescoApiSecurityOverride`` para permitir el acceso no autenticado a ``/api/enterprise/public/**``.

```java
package com.activiti.extension.bean;

import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.servlet.util.matcher.MvcRequestMatcher;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.handler.HandlerMappingIntrospector;

import com.activiti.api.security.AlfrescoApiSecurityOverride;

@Component
public class PublicEndpointSecurityOverride implements AlfrescoApiSecurityOverride {

    @Override
    public void configure(HttpSecurity http) throws Exception {
         http
            .securityMatcher(new AntPathRequestMatcher("/api/enterprise/public/**")) // Solo aplica a esta ruta
            .authorizeHttpRequests(auth -> auth
                .anyRequest().permitAll() // Permitir acceso sin autenticación solo para esta ruta
            )
            .csrf().disable(); // Opcional: Deshabilitar CSRF para las rutas públicas
        
    }

}
```

Creamos el endpoint público:

```java
package com.activiti.extension.api;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping("/enterprise/public/action")
public class ActionPublic {

    @GetMapping("/status")
    public ResponseEntity<String> getStatus() {
        return ResponseEntity.ok("La aplicación está funcionando correctamente.");
    }
}
```

Consultamos el siguiente A traves del postman, navegador etc.
```cmd
http://localhost:9090/activiti-app/api/enterprise/public/action/status
```
