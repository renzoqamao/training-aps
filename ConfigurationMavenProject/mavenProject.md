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

11. Declare todas las dependencias que su proyecto necesita para obtener bibliotecas externas.

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

13. Probamos ejecutando el siguiente comando para compilar con las dependencias

```bash
mvn clean compile assembly:single
```


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
