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
> **Nota**: el bean debe estar en el paquete com.activiti.extension.rest para poder encontrarlo.

Cree un archivo jar que contenga esta clase y agréguelo a la ruta de clases.

Se agregará una clase como esta en el paquete com.activiti.extension.rest a los endpoint ReST de la aplicación (por ejemplo, para usar en la interfaz de usuario), que **utilizan el enfoque de cookies para determinar el usuario**. La URL se asignará a /app. Por lo tanto, si inicia sesión en la interfaz de usuario de BPM Suite, puede ir a http://localhost:9090/activiti-app/app/rest/my-rest-endpoint y ver el resultado del endpoint ReST personalizado:

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
curl -u admin@app.activiti.com:password http://localhost:9090/activiti-app/api/enterprise/my-api-endpoint

{"fullName":" Administrator","taskCount":8}

```

>**Nota**: Debido a la carga de clases, actualmente no es posible colocar archivos jar con estos ReST endpoint personalizados en la ruta de clases global o común (por ejemplo, tomcat/lib para Tomcat). Deben colocarse en la ruta de clases de la aplicación web (por ejemplo, WEB-INF/lib).


# Anulaciones de seguridad para servicio ReST personalizado

Puede cambiar la configuración de seguridad predeterminada de los endpoints de la API REST implementando la interfaz ``com.activiti.api.security.AlfrescoApiSecurityOverride``. De manera predeterminada, los endpoints de la API REST utilizan el método de autenticación básica.

De manera similar, puede anular la configuración de seguridad predeterminada basada en cookies+token con los endpoints de REST regulares (aquellos que utiliza la IU) implementando la interfaz ``com.activiti.api.security.AlfrescoWebAppSecurityOverride``.

>**Nota**: La aplicación web y la API utilizan la misma seguridad HTTP de Spring para la autenticación. Para distinguir las configuraciones de seguridad, debe especificar la ruta a la que se aplica la configuración. Estas utilizan /app y /api de manera predeterminada. Por ejemplo, la configuración de la API debe comenzar con lo siguiente:

httpSecurity.antMatcher("/api/**")

## Ejemplo de anulación API ReST

Creamos el siguiente componente que implementa ``AlfrescoApiSecurityOverride`` para permitir permitir la autenticación con JWT.

### Prerrequisitos

Añadir al pom.xml

    ```xml
    <dependencies>
        <dependency>
            <groupId>jakarta.servlet</groupId>
            <artifactId>jakarta.servlet-api</artifactId>
            <version>5.0.0</version>
            <scope>provided</scope>
        <dependency>

         <!-- Dependencia para java-jwt -->
    <dependency>
        <groupId>com.auth0</groupId>
        <artifactId>java-jwt</artifactId>
        <version>4.4.0</version>
    </dependency>
    </dependencies>
  
    ```

### desarrollo

1. Creación de la anulación de seguridad
    ```java
    package com.activiti.extension.conf;

    import org.springframework.security.config.annotation.web.builders.HttpSecurity;
    import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
    import com.activiti.api.security.AlfrescoApiSecurityOverride;
    import org.springframework.stereotype.Component;

    @Component
    public class JwtApiSecurityConfig implements AlfrescoApiSecurityOverride {

        private final JwtAuthenticationFilter jwtAuthenticationFilter;

        public JwtApiSecurityConfig(JwtAuthenticationFilter jwtAuthenticationFilter) {
            this.jwtAuthenticationFilter = jwtAuthenticationFilter;
        }

        @Override
        public void configure(HttpSecurity http) throws Exception {
            http
            .securityMatcher("/api/**")
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        }
    }
    ```

2. Crear el filtro de autenticación JWT (JwtAuthenticationFilter)

    ```java
    package com.activiti.extension.conf;

    import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
    import org.springframework.security.core.context.SecurityContextHolder;
    import org.springframework.security.core.userdetails.UserDetails;
    import org.springframework.security.core.userdetails.UserDetailsService;
    import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
    import org.springframework.stereotype.Component;
    import org.springframework.web.filter.OncePerRequestFilter;

    import jakarta.servlet.FilterChain;
    import jakarta.servlet.ServletException;
    import jakarta.servlet.http.HttpServletRequest;
    import jakarta.servlet.http.HttpServletResponse;
    import java.io.IOException;

    @Component
    public class JwtAuthenticationFilter extends OncePerRequestFilter {

        private final JwtUtil jwtUtil;
        private final UserDetailsService userDetailsService;

        public JwtAuthenticationFilter(JwtUtil jwtUtil, UserDetailsService userDetailsService) {
            this.jwtUtil = jwtUtil;
            this.userDetailsService = userDetailsService;
        }

        @Override
        protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
                throws ServletException, IOException {
            String authHeader = request.getHeader("Authorization");
            String token = null;
            String username = null;

            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                token = authHeader.substring(7);
                username = jwtUtil.validateToken(token);
            }

            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);
                if (userDetails != null) {
                    UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                            userDetails, null, userDetails.getAuthorities());
                    authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                }
            }

            filterChain.doFilter(request, response);
        }
    }
    ```
3. Crear el proveedor de tokens JWT (JwtUtil)

    ```java
    package com.activiti.extension.conf;

    import com.auth0.jwt.JWT;
    import com.auth0.jwt.algorithms.Algorithm;
    import com.auth0.jwt.exceptions.JWTVerificationException;
    import com.auth0.jwt.interfaces.DecodedJWT;
    import com.auth0.jwt.interfaces.JWTVerifier;
    import org.springframework.beans.factory.annotation.Value;
    import org.springframework.stereotype.Component;

    import java.util.Date;

    @Component
    public class JwtUtil {

        @Value("${security.jwt.token.secret-key:defaultSecretKey}")
        private String secretKey;

        @Value("${security.jwt.token.expire-length:3600000}") // 1 hora en milisegundos
        private long validityInMilliseconds;

        public String generateToken(String username) {
            Date now = new Date();
            Date expiration = new Date(now.getTime() + validityInMilliseconds);

            return JWT.create()
                    .withSubject(username)
                    .withIssuedAt(now)
                    .withExpiresAt(expiration)
                    .sign(Algorithm.HMAC256(secretKey));
        }

        public String validateToken(String token) {
            try {
                JWTVerifier verifier = JWT.require(Algorithm.HMAC256(secretKey)).build();
                DecodedJWT decodedJWT = verifier.verify(token);
                return decodedJWT.getSubject();
            } catch (JWTVerificationException e) {
                return null;
            }
        }
    }
    ```


4. Crear un controlador REST para manejar la autenticación y proporcionar el token JWT:

    ```java
    package com.activiti.extension.api;

    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.http.ResponseEntity;
    import org.springframework.security.authentication.AuthenticationManager;
    import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
    import org.springframework.security.core.Authentication;
    import org.springframework.security.core.AuthenticationException;
    import org.springframework.web.bind.annotation.*;

    import com.activiti.extension.conf.JwtUtil;

    @RestController
    @RequestMapping("/enterprise/auth")
    public class JwtAuthController {
        @Autowired
        private AuthenticationManager authenticationManager;
        @Autowired
        private JwtUtil jwtUtil;

        @PostMapping("/login")
        public String login(@RequestParam String username, @RequestParam String password) {
            try {
                Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(username, password)
                );
                return jwtUtil.generateToken(username);
            } catch (AuthenticationException e) {
                throw new RuntimeException("Credenciales inválidas");
            }
        }

        /**
        * Endpoint protegido que solo puede ser accedido con un token JWT válido.
        */
        @GetMapping("/protected/data")
        public ResponseEntity<?> getProtectedData() {
            return ResponseEntity.ok().body("{\"message\": \"Acceso permitido con token válido\"}");
        }
    }
    ```


## Ejemplo de anulación de la aplicación Web

```java
package com.activiti.extension.bean;
import com.activiti.api.security.AlfrescoWebAppSecurityOverride;
import org.springframework.stereotype.Component;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;

@Component
public class WebAppSecurityConfig implements AlfrescoWebAppSecurityOverride {
    @Override
    public void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity
            .antMatcher("/app/**")                            // Configura solo las URL que comienzan con /app/
            .authorizeRequests()
            .antMatchers("/app/login", "/app/public/**")
                .permitAll()                                  // Permite sin autenticación la página de login y recursos públicos
            .anyRequest().authenticated()                     // Requiere autenticación para cualquier otra URL /app/**
            .and()
            .formLogin()
                .loginPage("/app/login")                      // Página de inicio de sesión personalizada
                .defaultSuccessUrl("/app/home")               // URL por defecto tras login exitoso
                .permitAll()                                  // El login (y sus recursos) son accesibles para todos
            .and()
            .logout()
                .logoutUrl("/app/logout")
                .logoutSuccessUrl("/app/login?logout")
                .permitAll();
            // (CSRF está habilitado por defecto; no se deshabilita aquí para las rutas /app/**)
    }
}

```

Consultamos el siguiente A traves del postman, navegador etc.
```cmd
curl -X POST http://localhost:9090/activiti-app/api/enterprise/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin@app.activiti.com", "password": "admin"}'

```

## Ejemplo de extensión de la seguridad de API ReST

Crearemos un endpoint ReST que no necesita enviar autenticación.

### prerequisitos

Añadir al pom.xml

    ```xml
    <dependencies>
        <dependency>
            <groupId>jakarta.servlet</groupId>
            <artifactId>jakarta.servlet-api</artifactId>
            <version>5.0.0</version>
            <scope>provided</scope>
        <dependency>
    </dependencies>
  
    ```
### desarrollo

1. Creación del controller. 
    ```java
    package com.activiti.extension.api;

    import org.springframework.http.ResponseEntity;
    import org.springframework.security.core.context.SecurityContextHolder;
    import org.springframework.web.bind.annotation.GetMapping;
    import org.springframework.web.bind.annotation.PostMapping;
    import org.springframework.web.bind.annotation.RequestMapping;
    import org.springframework.web.bind.annotation.RestController;
    import org.springframework.security.core.Authentication;

    @RestController
    @RequestMapping("/enterprise/public")
    public class PublicController {

        @GetMapping("/secure-data")
        public ResponseEntity<String> secureData() {
            return ResponseEntity.ok("Datos seguros accesibles por admin");
        }
    }
    ```

2. Creación de un Request Mutable
    ```java
    package com.activiti.extension.conf;

    import jakarta.servlet.http.HttpServletRequest;
    import jakarta.servlet.http.HttpServletRequestWrapper;
    import java.util.*;

    public class MutableHttpServletRequest extends HttpServletRequestWrapper {
        // Mapa que almacenará los encabezados personalizados
        private final Map<String, String> customHeaders;

        public MutableHttpServletRequest(HttpServletRequest request) {
            super(request);
            this.customHeaders = new HashMap<>();
        }

        // Método para agregar o reemplazar un encabezado
        public void putHeader(String name, String value) {
            this.customHeaders.put(name, value);
        }

        @Override
        public String getHeader(String name) {
            // Primero, verifica en los encabezados personalizados
            String headerValue = customHeaders.get(name);
            if (headerValue != null) {
                return headerValue;
            }
            // Si no se encuentra, devuelve el encabezado original
            return super.getHeader(name);
        }

        @Override
        public Enumeration<String> getHeaderNames() {
            // Crea una lista de los nombres de los encabezados personalizados
            Set<String> set = new HashSet<>(customHeaders.keySet());
            // Agrega los nombres de los encabezados originales
            Enumeration<String> e = super.getHeaderNames();
            while (e.hasMoreElements()) {
                String n = e.nextElement();
                set.add(n);
            }
            // Devuelve una enumeración de todos los encabezados
            return Collections.enumeration(set);
        }

        @Override
        public Enumeration<String> getHeaders(String name) {
            // Si el encabezado está en los personalizados, devuelve su valor
            if (customHeaders.containsKey(name)) {
                return Collections.enumeration(Collections.singleton(customHeaders.get(name)));
            }
            // De lo contrario, devuelve los encabezados originales
            return super.getHeaders(name);
        }
    }
    ```

3. Creación del filtro
    ```java
    package com.activiti.extension.conf;

    import jakarta.servlet.FilterChain;
    import jakarta.servlet.ServletException;
    import jakarta.servlet.http.HttpServletRequest;
    import jakarta.servlet.http.HttpServletResponse;
    import org.springframework.beans.factory.annotation.Value;
    import org.springframework.stereotype.Component;
    import org.springframework.web.filter.OncePerRequestFilter;

    import java.io.IOException;
    import java.util.Base64;

    @Component
    public class AdminAuthenticationFilter extends OncePerRequestFilter {
        @Value("${admin.username}")
        private String username;
        @Value("${admin.password}")
        private String password;

        @Override
        protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain) throws IOException, ServletException {

            logger.info("URI :" + request.getRequestURI());

            MutableHttpServletRequest mutableRequest = new MutableHttpServletRequest(request);

            if (request.getRequestURI().contains("/public/")) {
                // Autenticar como usuario invitado
                logger.info("URI Public :" + request.getRequestURI());
                // Envuelve la solicitud original
                String credenciales = username + ":" + password;
                logger.info("credenciales : " + credenciales);
                String codificado = "Basic " + Base64.getEncoder().encodeToString(credenciales.getBytes());
                // Agrega el encabezado personalizado
                mutableRequest.putHeader("Authorization", codificado);
                logger.info("Encabezado 'Authorization' agregado a la solicitud : " + codificado);
            }
            chain.doFilter(mutableRequest, response);
        }
    }
    ```

4. Creación de Extensión de la seguridad del API ReST
    ```java
    package com.activiti.extension.conf;

    import com.activiti.api.security.AlfrescoApiSecurityExtender;
    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.context.annotation.Configuration;
    import org.springframework.security.config.annotation.web.builders.HttpSecurity;
    import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

    @Configuration
    public class PublicAdminSecurityExtender implements AlfrescoApiSecurityExtender {

        private final AdminAuthenticationFilter adminAuthenticationFilter;

        @Autowired
        public PublicAdminSecurityExtender(AdminAuthenticationFilter adminAuthenticationFilter) {
            this.adminAuthenticationFilter = adminAuthenticationFilter;
        }

        @Override
        public void configure(HttpSecurity httpSecurity) throws Exception {
            httpSecurity.addFilterBefore(adminAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        }
    }
    ```
5. Agregar las siguientes propiedades a activiti-app.properties
    ```properties
    admin.username=admin@app.activiti.com
    admin.password=admin
    ```

Consultamos el siguiente A traves del postman, navegador etc.
```cmd
http://localhost:9090/activiti-app/api/enterprise/public/secure-data
```