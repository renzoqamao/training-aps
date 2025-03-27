# Plantilla de documentos

Utilice la tarea **Generar Documento** para generar un documento PDF o de Microsoft Word basado en una plantilla de documento de Word (.docx). Puede insertar variables de proceso en la plantilla de MS Word que se reemplazarán con valores reales durante la transformación del documento.

Una plantilla de documento puede ser:

- De Tenant : cualquiera puede usar esta plantilla en sus procesos. Útil para plantillas de empresa.

- Del Modelo de proceso : esta plantilla se carga mientras se modela el modelo de proceso y está vinculada al ciclo de vida del modelo de proceso.

Al exportar un modelo de aplicación, las plantillas de documentos del modelo de proceso se incluyen de forma predeterminada y se vuelven a cargar durante la importación. Las plantillas de documentos de Tenant no se exportan, pero se las compara con el nombre de la plantilla de documento, ya que los nombres son únicos para las plantillas de documentos de Tenant.

En la plantilla se puede insertar variables de la siguiente forma:
```
<<[miVariable]>>
```

Dado que el método anterior no realiza comprobaciones de valores nulos , se generará una excepción en tiempo de ejecución si la variable es null . Por lo tanto, utilice el siguiente método para evitar dichos errores:

```
<<[variables.get("miVariable")]>>
```

Si esta variable es null , se insertará un valor predeterminado en su lugar. También puede proporcionar un valor predeterminado:

```
<<[variables.get("miVariable", "miValorPredeterminado")]>>
```


> **Nota**: Los tipos de campos de formulario, como los de menú desplegable, botón de opción y escritura anticipada (typehead), utilizan myVariable_ID para el ID y myVariable_LABEL para el valor de la etiqueta. El ID es el valor real que utilizan las tareas de servicio y se insertan de forma predeterminada. Para mostrar el valor de la etiqueta en el documento generado, utilice myVariable_LABEL.

Al utilizar la tarea Generar documento , asegúrese de utilizar la sintaxis correcta para las variables y expresiones. Escriba las variables entre los caracteres ``<<[..]>>`` `


# Ejemplos

### Bloques condicionales

#### Tipo Texto
```
<<if [textfield==day]>> AM, <<else>> PM \<</if>>
```
#### Tipo Cantidad/Número
```
<<if [annualsalary > $40000]>>, it is generous, <<else>> a standard starting salary \<</if>>
```
#### Tipo Checkbox
```
<<if [senstitiveflag=="true"]>>it is Confidential, <<else>> Not Confidential \<</if>>
```
### tipo de fecha
```
<<[datefield]>>
```
### formato tipo de fecha
```
<<[datefield]:"yyyy.MM.dd">>
```
### Número/cantidad
```
 <<[amountfield]>>
```
### Cadena booleana
```
 <<[Genericcheckbox]>>
```
### Radio button / Typehead / dropdown: 
```
Select <<[Options_LABEL]>> with an ID <<[Options_ID]>>
```

### Bonus

```java
package com.activiti.extension.bean;

import org.activiti.engine.delegate.DelegateExecution;
import org.springframework.stereotype.Component;

import com.activiti.api.docgen.TemplateVariableProcessor;
import com.activiti.domain.runtime.RuntimeDocumentTemplate;

@Component
public class MyTemplateVariableProcessor implements TemplateVariableProcessor {
    
    public Object process(RuntimeDocumentTemplate runtimeDocumentTemplate, DelegateExecution execution, String variableName, Object value) {
            
        if (!"datos".equals(variableName)) return value.toString();
        
        return value.toString() + "___" + "HELLO_WORLD";
        
    }
}
```
> Nota:variables.get("myVariable") Sólo se pasarán a la TemplateVariableProcessorimplementación las variables con el formato de la plantilla .docx.