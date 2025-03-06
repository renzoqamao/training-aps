# Campos de formulario personalizados

Se pueden agregar tipos de campos de formulario personalizados a través de plantillas de formulario personalizadas . Una plantilla de formulario se basa en la plantilla de formulario predeterminada y se pueden eliminar, reordenar, modificar (cambiar el nombre, el icono, etc.) o tener nuevos tipos de campos de formulario.

Las plantillas de formulario se definen en la sección Plantillas del Diseñador de aplicaciones. Un nuevo tipo de campo de formulario consta de lo siguiente:

- Una plantilla HTML que se representa al arrastrar y soltar desde la paleta en el **lienzo del formulario** es el generador de formularios.
- Una plantilla HTML que se representa cuando el formulario se muestra en **tiempo de ejecución**.
Un controlador AngularJS personalizado opcional en caso de que sea necesario **aplicar lógica** personalizada al campo de formulario.
- Una lista opcional de **scripts de terceros** que se necesitan cuando se trabaja con el campo de formulario en tiempo de ejecución.


# Ejemplos 

Para los siguientes ejemplos:

1. Crear una plantilla

![crear una plantilla](./images/createStencil.png)

2. Datos de la plantilla

![información plantilla](./images/infoStencil.png)

3. Editor de plantillas

![edición de  plantilla](./images/editorStencil.png)

4. Añadir nuevo elemento

![añadir nuevo elemento](./images/addNewElement.png)

## Ejemplo 1

Para realizar el ejemplo hay que navegar a: 

Plantillas > Crear Plantilla (Editor de formularios) > Editor de Plantillas > Añadir nuevo elemento


Este ejemplo contiene una lista de campos numéricos con un botón en la parte inferior para agregar una nueva línea de elementos, mientras se genera un gráfico circular al a derecha.

Este elemento se llamará **Gráfico**

![elementName](./images/elementName.png)

Se utilizaré la biblioteca Epoch, descarga los siguiente archivos desde su sitio de github:

- [d3.min.js](https://raw.githubusercontent.com/mbostock/d3/v3.5.6/d3.min.js)
- [epoch.min.js](https://raw.githubusercontent.com/fastly/epoch/0.6.0/epoch.min.js)

>**Nota**: ya que la biblioteca epoch depende de d3, entonces d3 debe estar primero en la tabla y epoch en segundo lugar.

![importLibScripts](./images/importLibScripts.png)

en **Plantilla de editor de formulario**

```html
<img src="https://img.freepik.com/free-vector/3d-pie-chart-3_78370-628.jpg?t=st=1738548774~exp=1738552374~hmac=0a263e85898ff599780f88de6e2003358a8efdf81a10a65658eea46a030469f2&w=740"></img>
```


en **Plantilla de tiempo de ejecución de formulario**

```html
<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/epoch/0.6.0/epoch.min.css">

<div ng-controller="MyController" style="float:left;margin: 35px 20px 0 0;">
    <div ng-repeat="item in items">
          <input type="text" ng-model="item.label" style="width:200px; margin: 0 10px 10px 0;" ng-change="refreshChart()">
          <input type="number" ng-model="item.value" style="width: 80px; margin-bottom: 10px;" ng-change="refreshChart()">
    </div>

    <div>
        <button class="btn btn-default btn-sm" ng-click="addItem()" ng-disabled="isDisabled">
           Add item
        </button>
    </div>
</div>

<div class="epoch category10" ng-class="'activiti-chart-' + field.id" style="display:inline-block;width: 200px; height: 200px;"></div>
<div class="clearfix"></div>

```


Definir el controlador para este campo de formulario. El controlador es un controlador **AngularJs** que realiza principalmente tres funciones:

- Mantener un modelo de los artículos de línea
- Implementar una devolución de llamada para el botón en el que se puede hacer clic
- Almacene el valor del campo de formulario en el formato adecuado de Process Services

![ControllerDefinition](./images/controllerDefinition.png)

```Javascript
angular.module('activitiApp')
    .controller('MyController', ['$rootScope', '$scope', function ($rootScope, $scope) {

        console.log('MyController instantiated');

        // Items are empty on initialisation
        $scope.items = [];

        // The variable to store the piechart data (non angular)
        var pieChart;

        // Epoch can't use the Angular model, so we need to clean it
        // (remove hashkey etc, specific to Angular)
        var cleanItems = function(items) {
            var cleanedItems = [];
            items.forEach(function(item) {
               cleanedItems.push( { label: item.label, value: item.value} );
            });

            return cleanedItems;
        };

        // Callback for the button
        $scope.addItem = function() {

            // Update the model
            $scope.items.push({ label: 'label ' + ($scope.items.length + 1), value: 0 });

            // Update the values for the pie chart
            // Note: Epoch is not an angular lib so doesn't use the model directly
            if (pieChart === undefined) {

                pieChart = jQuery('.activiti-chart-' + $scope.field.id).epoch({
                    type: 'pie',
                    data: cleanItems($scope.items)
                });
                console.log('PieChart created');

            } else {

                $scope.refreshChart();

            }

        };


        // Callback when model value changes
        $scope.refreshChart = function() {
            pieChart.update(cleanItems($scope.items));
            console.log('PieChart updated');
        };


        // Register this controller to listen to the form extensions methods
        $scope.registerCustomFieldListener(this);

        // Deregister on form destroy
        $scope.$on("$destroy", function handleDestroyEvent() {
            console.log("destroy event");
            $scope.removeCustomFieldListener(this);
        });

        // Setting the value before completing the task so it's properly stored
        this.formBeforeComplete = function(form, outcome, scope) {
            console.log('Before form complete');
            $scope.field.value = JSON.stringify(cleanItems($scope.items));
        };

        // Needed when the completed form is rendered
        this.formRendered = function(form, scope) {
            console.log(form);
            form.fields.forEach(function(field) {
                if (field.type === 'readonly'
                      && $scope.field.id == field.id
                      && field.value
                      && field.value.length > 0) {

                    $scope.items = JSON.parse(field.value);
                    $scope.isDisabled = true;

                    pieChart = jQuery('.activiti-chart-' + $scope.field.id).epoch({
                        type: 'pie',
                        data: cleanItems($scope.items)
                    });

                }
            });
        };

}]);

```

Los campos de Propiedad y tipo de valor de campo es para agregar un nuevo par de clave:valor a customFieldsValueInfo.FieldName (ex customFieldsValueInfo.grafico )

![property](./images/Property.png)

En el form renderizado 

![object](./images/formObject.png)


``$scope.field.value`` es igual a Field value type. 


## Ejemplo 2

Campo Mes presentado como un menú desplegable donde el usuario final puede seleccionar un mes. Campo estatico y no implica datos dinámicos.

Plantillas > Crear Plantilla (Editor de formularios) > Editor de Plantillas > Añadir nuevo elemento

1. Creamos el campo como lo muestran las siguientes imagenes, esto Obliga a que el campo tenga el id **selectedMonth**.

![fieldMonth](./images/example2/fieldMonth.png)

```html
<div ng-controller="monthController" style="float:left;margin: 0 20px 0 0;">
    <select name="singleMonthSelect" ng-model="data.selectedMonth">
        <option value="jan">Enero</option>
        <option value="feb">Febrero</option>
        <option value="mar">Marzo</option>
        <option value="apr">Abril</option>
        <option value="may">Mayo</option>
        <option value="jun">Junio</option>
        <option value="jul">Julio</option>
        <option value="aug">Agosto</option>
        <option value="set">Septiembre</option>
        <option value="oct">Octubre</option>
        <option value="nov">Noviembre</option>
        <option value="dec">Diciembre</option>
    </select>
</div>
```

```html
<i> El menú desplegable del mes va aquí </i>
```

```javascript
angular
.module('activitiApp')
//El siguiente código adjunta este controlador al marcado HTML que acabamos de crear 
.controller('monthController',
    ['$rootScope', '$scope', 
    // indica la implementación del controlador
    function($rootScope, $scope){
        $scope.data={ selectedMonth : null,};
        
        ALFRESCO.formExtensions.formBeforeComplete =
            function(form, outcome, scope){
                console.log('Before form complete');
                $scope.field.value = $scope.data.selectedMonth
            };
    }]
);
```

Probamos creando una aplicación con la plantilla de formulario creada.

>**Nota** : el campo creado tiene que tener el id ``selectedMonth``.

## Ejemplo 3

Menú desplegable con una lista de datos de un servicio externo. El servicio externo es el api de pokemon:


```url
https://pokeapi.co/api/v2/pokemon?limit=10&offset=0
```

```json
{
  "count": 1304,
  "next": "https://pokeapi.co/api/v2/pokemon?offset=10&limit=10",
  "previous": null,
  "results": [
    {
      "name": "bulbasaur",
      "url": "https://pokeapi.co/api/v2/pokemon/1/"
    },
    {
      "name": "ivysaur",
      "url": "https://pokeapi.co/api/v2/pokemon/2/"
    },
    {
      "name": "venusaur",
      "url": "https://pokeapi.co/api/v2/pokemon/3/"
    },
    {
      "name": "charmander",
      "url": "https://pokeapi.co/api/v2/pokemon/4/"
    },
    {
      "name": "charmeleon",
      "url": "https://pokeapi.co/api/v2/pokemon/5/"
    },
    {
      "name": "charizard",
      "url": "https://pokeapi.co/api/v2/pokemon/6/"
    },
    {
      "name": "squirtle",
      "url": "https://pokeapi.co/api/v2/pokemon/7/"
    },
    {
      "name": "wartortle",
      "url": "https://pokeapi.co/api/v2/pokemon/8/"
    },
    {
      "name": "blastoise",
      "url": "https://pokeapi.co/api/v2/pokemon/9/"
    },
    {
      "name": "caterpie",
      "url": "https://pokeapi.co/api/v2/pokemon/10/"
    }
  ]
}
```
Formulario en tiempo de ejecución

```html
<div ng-controller="pokeController" style="float:left;margin: 0 20px 0 0;">
    <select ng-model="data.selectedPokemon"
        ng-options="item.code as item.name for item in data.pokemones">
        <option value="">--Select Pokemon--</option>
    </select>
    
</div>
```

Controlador del formulario

```javascript
angular.module('activitiApp')
.controller('pokeController', 
    ['$rootScope', '$scope', '$http',  
    function ($rootScope, $scope, $http) {       
        $scope.data = {
            selectedPokemon: null,           
            pokemones: null  };            
        // Fetch all the states from an external REST service       
        // that responds with JSON       
        $http.get('https://pokeapi.co/api/v2/pokemon?limit=10&offset=0').
            then(
                function(data, status, headers, config) {               
                var tempResponseArray = data.data.results;               
                $scope.data.pokemones = [];                   
                    for (var i = 0; i < tempResponseArray.length; i++) {                   
                        var pokemon = { name: tempResponseArray[i].name, code: i};                   
                        $scope.data.pokemones.push(pokemon);                   
                    }               
                },
                function(data, status, headers, config) {                   
                            alert('Error: '+ status);                   
                            tempResponseArray = [];           
                }
            );                 
            
            // Setting the value before completing the task so it's properly stored       
            ALFRESCO.formExtensions.formBeforeComplete = function(form, outcome, scope){               
                $scope.field.value = $scope.data.selectedPokemon;           
            };       
        }
    ]
);
```

![pokemon](./images/example3/pokemon.png)


>**Nota** : el campo creado tiene que tener el id ``selectedPokemon``.
## Ejemplo 4

Implementación de un campo de formulario de imagen con hipervínculo. En el cual este campo necesita de parametros adicionales para configurar el campo que se incluye en el formulario.

Plantilla de tiempo de ejecución de formulario

```html
<a href="{{field.params.customProperties.hyperlinkUrl}}" target="_blank">
    <img src="{{field.params.customProperties.imageUrl}}"/>
</a>
```

Plantilla de editor de formulario

```html
<i>La imagen con hipervinculo se mostrará aqui</i>
```

Tenemos dos propiedades: ``hyperlinkUrl`` y ``imageUrl``


El siguiente paso es definir los dos parámetros de configuración. Haga clic en el enlace Editar en la parte inferior de la pantalla de creación de campos:

![ficha y propiedades](./images/example4/ficha_properties.png)


En la siguiente ventana, hacemos click en ``Añadir nueva propiedad``


![ventana de propiedades](./images/example4/windowsProperty.png)



Para ``Para hyperlinkUrl``:


![hyperlink url properties](./images/example4/hyperlinkProperty.png)


Para ``Para imageUrl``:


![Image url properties](./images/example4/imageUrlProperty.png)

