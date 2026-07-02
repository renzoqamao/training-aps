# Configurar proyecto maven para APS

## Método 1

### Prerrequisito

 * OpenJDK 17
 * Apache Maven 3.8.8
 * Ambiente de Alfresco Process Service 
 * Acceso a los repositorios Nexus de Alfresco (credenciales proporcionadas por Alfresco)
 * Configure el archivo settings.xml de sus servidores Maven con las credenciales para estos repositorios:
 
 ``` 
    <server>
	  <id>activiti-enterprise-releases</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
	<server>
	  <id>enterprise-releases</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
	<server>
	  <id>internal-thirdparty</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
  ```

> **Alternativa — usar un `settings.xml` propio con `--settings`:** En lugar de modificar el `settings.xml` global de Maven (`~/.m2/settings.xml` o `$MAVEN_HOME/conf/settings.xml`), puede mantener un archivo independiente (por ejemplo en `/tmp/settings.xml`) y pasárselo a Maven en cada ejecución con el flag `--settings` (abreviado `-s`). Esto es útil en entornos CI/CD o contenedores, donde no conviene tocar la configuración global.
>
> Cree el archivo `/tmp/settings.xml` con la estructura completa:
>
> ```xml
> <settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
>     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
>     xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">
>     <servers>
>         <server>
>             <id>activiti-enterprise-releases</id>
>             <username>yourAlfrescoUsername</username>
>             <password>yourAlfrescoPassword</password>
>         </server>
>         <server>
>             <id>enterprise-releases</id>
>             <username>yourAlfrescoUsername</username>
>             <password>yourAlfrescoPassword</password>
>         </server>
>         <server>
>             <id>internal-thirdparty</id>
>             <username>yourAlfrescoUsername</username>
>             <password>yourAlfrescoPassword</password>
>         </server>
>     </servers>
> </settings>
> ```
>
> Luego compile indicando ese archivo en los comandos del Método 1:
>
> ```bash
> mvn clean package --settings /tmp/settings.xml
> ```
>
> El mismo flag aplica a cualquier objetivo de Maven, por ejemplo al instalar el JAR de extensiones o al construir el WAR overlay:
>
> ```bash
> mvn clean install --settings /tmp/settings.xml
> ```


1. Creamos una carpeta llamada ```demos```.
2. En el terminal ingresamos al directorio con el comando *cd*.
3. Creamos el proyecto maven con el siguiente comando:
    ```
        mvn archetype:generate  "-DarchetypeArtifactId=maven-archetype-quickstart"
    ```
    - El creador de Maven le hará una serie de preguntas. Elija las opciones siguientes:
   - Group ID: ```org.alfresco```
   - Artifact ID: ```demo-aps```
   - Version: _press ENTER_
   - Package ID: _press ENTER_
   - ```Y```
        * Esto creará una carpeta con un archivo POM y una estructura de carpetas Java.

4. En JDE, seleccione **Archivo > Abrir** y navegue hasta el archivo POM.xml creado en el paso anterior. Una vez seleccionado, presione el botón **Abrir como proyecto** en la siguiente ventana emergente.
5. Elimine el archivo **App.Test** ubicado en: _src > test > java > org.alfresco_.
6. Abra el archivo POM seleccionándolo en el panel de jerarquía izquierdo.
8. Borramos todas las dependencias. El pom.xml debería verse así: 
    ```xml
        <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
        <modelVersion>4.0.0</modelVersion>
        <groupId>org.alfresco</groupId>
        <artifactId>demo-aps</artifactId>
        <packaging>jar</packaging>
        <version>1.0-SNAPSHOT</version>
        <name>demo-aps</name>
        <url>http://maven.apache.org</url>
        <dependencies>
        </dependencies>
        </project>
    ```

9. Especifique las propiedades que deben definirse para este proyecto.

```xml
    <properties>
		<maven.compiler.source>17</maven.compiler.source>
		<maven.compiler.target>17</maven.compiler.target>
		<suite.version>24.2.0</suite.version>
		<spring-boot.version>3.2.3</spring-boot.version>
	</properties>
```

10. Agregue repositorios desde los cuales su proyecto necesita descargar los artefactos necesarios.

```xml
    <repositories>
		<repository>
			<id>activiti-enterprise-releases</id>
			<name>Alfresco EE releases</name>
			<url>https://artifacts.alfresco.com/nexus/repository/activiti-enterprise-releases</url>
			<snapshots>
				<enabled>false</enabled> <!-- Deshabilita los snapshots -->
			</snapshots>
		</repository>
	</repositories>
```

11. Declare todas las dependencias que su proyecto necesita para obtener bibliotecas externas. Para APS 25 no es necesario las exclusiones.

```xml
    <dependencies>
    <!-- Contiene los servicios y la lógica real de BPM Suite. -->
    <dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-logic</artifactId>
			<version>${suite.version}</version>
			<scope>provided</scope>
			<exclusions>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<!-- Contiene los puntos finales REST que utilizan la UI y la API pública. -->
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-rest</artifactId>
			<version>${suite.version}</version>
			<scope>provided</scope>
			<exclusions>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
	<!--  Contiene todas las dependencias de Process Services. 
	También es un módulo Maven conveniente (el tipo de empaquetado es pom ) 
	para el desarrollo. -->		
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-dependencies</artifactId>
			<version>${suite.version}</version>
			<scope>provided</scope>
			<type>pom</type>
			<exclusions>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<!--Contiene clases de configuración. -->
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app</artifactId>
			<version>${suite.version}</version>
			<scope>test</scope>
			<classifier>classes</classifier>
			<exclusions>
				<exclusion>
					<groupId>com.activiti</groupId>
					<artifactId>aspose-transformation</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<!--: Contiene la raíz pom. No lo use para desarrollo. 
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-root</artifactId>
			<version>${suite.version}</version>
			<type>pom</type>
		</dependency>-->
		<!-- Contiene los objetos de dominio , anotados con anotaciones JPA para persistencia y 
		varios repositorios Spring para ejecutar las operaciones reales de la base de datos. 
		También tiene los pojos de Java de las representaciones JSON que se utilizan, 
		por ejemplo, como respuestas de los puntos finales REST.-->
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-model</artifactId>
			<version>${suite.version}</version>
			<type>pom</type>
			<exclusions>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<dependency>
			<groupId>com.activiti</groupId>
			<artifactId>activiti-app-data</artifactId>
			<version>${suite.version}</version>
			<type>pom</type>
			<exclusions>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-core</artifactId>
				</exclusion>
				<exclusion>
					<groupId>org.apache.commons</groupId>
					<artifactId>commons-email2-jakarta</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<dependency>
				<groupId>org.springframework.boot</groupId>
				<artifactId>spring-boot-dependencies</artifactId>
				<version>${spring-boot.version}</version>
				<type>pom</type>
				<scope>import</scope>
		</dependency>
  </dependencies>
```
12. Especifique los complementos utilizados en la sección de compilación que Maven necesita para compilar el proyecto.

Para Estandár: 
```xml
    <build>
		<plugins>
			<plugin>
				<groupId>org.apache.maven.plugins</groupId>
				<artifactId>maven-shade-plugin</artifactId>
				<version>3.4.0</version>
				<executions>
					<execution>
						<phase>package</phase>
						<goals>
							<goal>shade</goal>
						</goals>
					</execution>
				</executions>
			</plugin>
			<plugin>
				<groupId>org.apache.maven.plugins</groupId>
				<artifactId>maven-compiler-plugin</artifactId>
				<version>3.13.0</version>
				<configuration>
					<parameters>true</parameters>
				</configuration>
			</plugin>
		</plugins>
	</build>
```


```bash
mvn clean package
```

13. Especifique los complementos utilizados en la sección de compilación que Maven necesita para compilar el proyecto.

Pruebas:

```xml
<build>
		 <finalName>demo</finalName> <!-- Nombre del JAR principal -->
		<plugins>
			<plugin>
				<groupId>org.apache.maven.plugins</groupId>
				<artifactId>maven-assembly-plugin</artifactId>
				<version>3.3.0</version>
				<configuration>
					<descriptorRefs>
						<descriptorRef>jar-with-dependencies</descriptorRef>
					</descriptorRefs>
					 <!-- Nombre personalizado para el JAR -->
                <finalName>demo-${project.version}</finalName>
                <appendAssemblyId>false</appendAssemblyId> <!-- Elimina el sufijo "jar-with-dependencies" -->
				</configuration>
				<executions>
					<execution>
						<id>make-assembly</id>
						<phase>package</phase>
						<goals>
							<goal>single</goal>
						</goals>
					</execution>
				</executions>
			</plugin>
		</plugins>
	</build>
```

```bash
mvn clean package
mvn clean compile assembly:single
```

### Construir el WAR de activiti-app (WAR Overlay)

Los pasos anteriores generan únicamente el **JAR de extensiones** (tu código personalizado: beans, listeners, service tasks, endpoints REST, etc.). Para desplegar en Tomcat necesitamos el WAR completo de la aplicación (`activiti-app.war`) con nuestras extensiones incluidas.

La técnica utilizada es el **WAR Overlay**: Maven descarga el artefacto base `com.activiti:activiti-app` (empaquetado como `war`) desde el Nexus de Alfresco y **superpone** encima nuestro JAR de extensiones, produciendo un `activiti-app.war` personalizado. Con este método no modificamos el WAR original de Alfresco, solo lo extendemos.

> Ejemplo de referencia: [alfresco-process-services-project-sdk](https://github.com/OpenPj/alfresco-process-services-project-sdk), módulo `activiti-app-overlay-war`.

1. Dentro de la carpeta `demos` creamos un segundo proyecto Maven (por ejemplo `activiti-app-overlay-war`) que dependerá del JAR de extensiones `demo-aps` construido en los pasos anteriores. Su empaquetado (`packaging`) debe ser `war`.

2. Configuramos el `pom.xml` del proyecto overlay. Reutilizamos las mismas `<properties>` y `<repositories>` del proyecto de extensiones (para poder resolver `${suite.version}` y descargar desde el Nexus de Alfresco):

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>org.alfresco</groupId>
    <artifactId>activiti-app-overlay-war</artifactId>
    <packaging>war</packaging>
    <version>1.0-SNAPSHOT</version>
    <name>activiti-app-overlay-war</name>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <suite.version>24.2.0</suite.version>
    </properties>

    <repositories>
        <repository>
            <id>activiti-enterprise-releases</id>
            <name>Alfresco EE releases</name>
            <url>https://artifacts.alfresco.com/nexus/repository/activiti-enterprise-releases</url>
            <snapshots>
                <enabled>false</enabled>
            </snapshots>
        </repository>
    </repositories>

    <dependencies>
        <!-- JAR de extensiones construido previamente (Método 1). -->
        <dependency>
            <groupId>org.alfresco</groupId>
            <artifactId>demo-aps</artifactId>
            <version>1.0-SNAPSHOT</version>
            <type>jar</type>
        </dependency>
        <!-- WAR base de Alfresco Process Services descargado desde Nexus.
             Sobre este WAR se realiza el overlay. -->
        <dependency>
            <groupId>com.activiti</groupId>
            <artifactId>activiti-app</artifactId>
            <version>${suite.version}</version>
            <type>war</type>
            <scope>runtime</scope>
        </dependency>
    </dependencies>

    <build>
        <!-- El WAR final se llamará activiti-app.war (sin sufijo de versión). -->
        <finalName>activiti-app</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-war-plugin</artifactId>
                <version>3.3.2</version>
                <configuration>
                    <!-- APS no incluye web.xml propio en el overlay. -->
                    <failOnMissingWebXml>false</failOnMissingWebXml>
                    <!-- Evita copiar clases del WAR base ya presentes. -->
                    <packagingExcludes>com.activiti/</packagingExcludes>
                    <workDirectory>./target/activiti-app</workDirectory>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

**Puntos clave del overlay:**

| Elemento | Propósito |
|----------|-----------|
| `<packaging>war</packaging>` | Indica a Maven que el artefacto final es un WAR y activa el `maven-war-plugin`. |
| Dependencia `com.activiti:activiti-app` con `<type>war</type>` | Es el WAR base que Maven descarga de Nexus y usa como base del overlay. |
| Dependencia `demo-aps` (jar) | Tu JAR de extensiones; queda embebido en `WEB-INF/lib` del WAR final. |
| `<finalName>activiti-app</finalName>` | Fuerza a que el nombre del artefacto sea `activiti-app.war`. |
| `<scope>runtime</scope>` en el WAR base | El WAR base solo se necesita para el overlay/empaquetado, no para compilar. |

3. Como el proyecto overlay depende del JAR `demo-aps`, primero debemos instalarlo en el repositorio local de Maven. Desde el proyecto de extensiones (`demo-aps`):

```bash
mvn clean install
```

4. Generamos el WAR con las extensiones. Desde el proyecto overlay (`activiti-app-overlay-war`):

```bash
mvn clean package
```

El artefacto resultante se encuentra en:

```
activiti-app-overlay-war/target/activiti-app.war
```

5. Desplegamos el WAR reemplazando el `activiti-app` existente en Tomcat de APS. Detenemos Tomcat, sustituimos la carpeta/WAR desplegado y volvemos a iniciarlo:

```
/opt/alfresco/alfresco-process-services/tomcat/webapps/activiti-app.war
```

> **Nota:** El `${suite.version}` del overlay debe coincidir con la versión de APS del ambiente destino. El WAR base `com.activiti:activiti-app` se descarga desde el Nexus de Alfresco, por lo que se requieren las credenciales configuradas en `settings.xml` (ver Prerrequisitos).


## Método 2

### Prerrequisito

 * OpenJDK 17
 * Apache Maven 3.9.9
 * Docker (opcional)
 * Coloque activiti.lic y transform.lic válidos (o Aspose.Total.Java.lic) en la carpeta /license para ejecutar pruebas unitarias/de integración y para crear contenedores.
 * Acceso a los repositorios Nexus de Alfresco (credenciales proporcionadas por Alfresco)
 * Configure el archivo settings.xml de sus servidores Maven con las credenciales para estos repositorios:
 
 ``` 
    <server>
	  <id>activiti-enterprise-releases</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
	<server>
	  <id>enterprise-releases</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
	<server>
	  <id>internal-thirdparty</id>
	  <username>yourAlfrescoUsername</username>
	  <password>yourAlfrescoPassword</password>
	</server>
  ```

1. Creamos una carpeta llamada ```demos```.
2. En el terminal ingresamos al directorio con el comando *cd*.
3. Clonamos el proyecto publico sdk
	```powershell
	git clone https://github.com/OpenPj/alfresco-process-services-project-sdk.git
	cd alfresco-process-services-project-sdk
	git branch -a
	git checkout tags/v3.0.6
	```

4. Configuramos las credenciales de repositorios privados en el archivo settings.xml del maven instalado que se encuentra instalado en la siguiente ruta:
	```powershell
	cd C:\Program Files\Maven\apache-maven-3.8.8\conf
	```

5. Agregamos los siguientes servidores en la etiqueta ``<servers>``.
	```xml
	<server>
		<id>activiti-enterprise-releases</id>
		<username>tuUsuario</username>
		<password>tuContraseña</password>
		</server>
		<server>
		<id>enterprise-releases</id>
		<username>tuUsuario</username>
		<password>tuContraseña</password>
		</server>
		<server>
		<id>internal-thirdparty</id>
		<username>tuUsuario</username>
		<password>tuContraseña</password>
		</server>
	```

6. Colocas las licencias necesitas en /license con el nombre ``activiti.lic``

7. La versión de APS se toma automáticamente de pom.xml, solo necesita configurar la versión de APS habilitando el perfil activo de una versión específica ``mvn clean install -Paps24.2.0``. Los scripts de ejecución admiten los siguientes comandos: 


* Para solo la applicación Activiti App: `./run.sh (.bat) {build_start|build_start_it_supported|start|stop|purge|tail|reload_aps|build_test|test}`
* Para las aplicaciones Activiti App y Activiti Admin: `./run.sh (.bat) {build_start_admin|build_start_it_supported_admin|start_admin|stop_admin|purge_admin|tail_admin|reload_aps_admin|build_test_admin|test_admin}`


**nota** : En algunos casos cuando tarda en construirse y no levanta todo el docker compose completo cuando se levanta con  ``activiti-admin``. iniciar el docker compose.

8. Ingresamos con:

	```
		http://localhost:8080/activiti-app
	```

## Activar los logs

/opt/alfresco/alfresco-process-services/tomcat/webapps/activiti-app/WEB-INF/classes/log4j2.properties

```properties
logger.audit.name=com.activiti.extension.bean.CustomAudit
logger.audit.level=debug

logger.auditutils.name=com.activiti.extension.utils.AuditUtils
logger.auditutils.level=debug


logger.identityLink.name=org.activiti.engine.impl.persistence.entity.IdentityLinkEntityImpl
logger.identityLink.level=debug

logger.dbengine.name=org.activiti.engine.impl.db
logger.dbengine.level=debug

```