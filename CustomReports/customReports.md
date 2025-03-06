# Reportes Personalizados

Un reporte personalizado es una sección adicional en la aplicación Analytics en cada aplicación publicada, que muestra uno o más informes personalizados. Cada informe se implementa mediante un Spring bean encargado de:

1. Realizar una consulta de búsqueda en Elasticsearch utilizando la API Java del cliente.
2. Convertir los resultados de la búsqueda (hits o agregaciones) en datos para gráficos o tablas y añadirlos a la respuesta.

La interfaz de usuario mostrará automáticamente los widgets adecuados según los datos que proporcione tu spring bean.

## Implementación del Bean

Tu Spring bean será descubierto automáticamente mediante anotaciones, pero debe ubicarse en el paquete ``com.activiti.service.reporting``. Dado que este paquete se utiliza para los informes predeterminados, se recomienda que los informes personalizados utilicen un subpaquete, como ``com.activiti.service.reporting.custom``.


Debes implementar el método ``generate()``, y puedes sobrescribir el método ``getParameterDefinitions()`` si necesitas recopilar parámetros seleccionados por el usuario desde la interfaz para utilizarlos en tu consulta.

## Implementación de generate

El método tiene dos responsabilidades:

- Realizar uno o más consultas en elasticSearch para obtener datos del informe.
- Poblar datos de gráficos o tablas a partir de los resultados de la consulta.


La estructura general de la clase será la siguiente:​

```java
/**
 * Copyright 2005-2015 Alfresco Software, Ltd. All rights reserved.
 * License rights for this program may be obtained from Alfresco Software, Ltd.
 * pursuant to a written agreement and any use of this program without such an
 * agreement is prohibited.
 */
package com.activiti.service.reporting.custom;

import co.elastic.clients.elasticsearch._types.FieldValue;
import co.elastic.clients.elasticsearch._types.SortOptions;
import co.elastic.clients.elasticsearch._types.SortOrder;
import co.elastic.clients.elasticsearch._types.aggregations.Aggregate;
import co.elastic.clients.elasticsearch._types.aggregations.Aggregation;
import co.elastic.clients.elasticsearch._types.aggregations.CalendarInterval;
import co.elastic.clients.elasticsearch._types.aggregations.DateHistogramAggregate;
import co.elastic.clients.elasticsearch._types.aggregations.DateHistogramBucket;
import co.elastic.clients.elasticsearch._types.aggregations.ExtendedStatsAggregate;
import co.elastic.clients.elasticsearch._types.aggregations.FilterAggregate;
import co.elastic.clients.elasticsearch._types.aggregations.StringTermsAggregate;
import co.elastic.clients.elasticsearch._types.aggregations.StringTermsBucket;
import co.elastic.clients.elasticsearch._types.mapping.FieldType;
import co.elastic.clients.elasticsearch._types.query_dsl.DateRangeQuery;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch.core.SearchRequest;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.util.NamedValue;
import co.elastic.clients.util.ObjectBuilder;
import com.activiti.domain.idm.User;
import com.activiti.domain.reporting.MasterDetailTableDataRepresentation;
import com.activiti.domain.reporting.MultiBarChart;
import com.activiti.domain.reporting.Parameter;
import com.activiti.domain.reporting.ParametersDefinition;
import com.activiti.domain.reporting.PieChartDataRepresentation;
import com.activiti.domain.reporting.ReportDataRepresentation;
import com.activiti.domain.reporting.ReportingDataUtil;
import com.activiti.domain.reporting.TableDataRepresentation;
import com.activiti.service.api.ReportingIndexManager;
import com.activiti.service.api.UserCache;
import com.activiti.service.reporting.generators.BaseReportGenerator;
import com.activiti.service.reporting.searchClient.AnalyticsClient;
import com.activiti.util.ISO8601Utils;
import com.aspose.slides.internal.og.la;
import com.aspose.slides.internal.og.un;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import org.activiti.engine.ProcessEngine;
import org.apache.commons.lang3.tuple.Pair;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/*
 * Es una implementación personalizada de un generador de informes en APS 24.4. 
 * Su propósito es generar informes sobre instancias de procesos, incluyendo métricas
 * como la duración de actividades, histogramas de fechas y detalles de las instancias
 * de procesos más lentas.
 * Extiende: BaseReportGenerator → Hereda funcionalidad base para generación de reportes.
 * Component Spring: @Component("report.generator.p.overview.custom") → Indica que esta clase es un bean gestionado por Spring.
 * Interacción con Elasticsearch: Usa AnalyticsClient para consultar datos en Elasticsearch.
 * Generación de reportes:
 *    Histogramas de fechas de tareas.
 *    Gráficos de torta sobre duración de actividades.
 *    Tablas con duración de actividades y detalles de las instancias más lentas.
 */
@Component("report.generator.p.overview.custom")
public class ProcessInstanceOverviewReportGeneratorCustom extends BaseReportGenerator {
   private static final Logger logger = LoggerFactory.getLogger(ProcessInstanceOverviewReportGeneratorCustom.class);
   public static final String ID = "report.generator.p.overview.custom";
   public static final String PARAM_PROCESSDEFINITION_ID = "processDefinitionId";
   public static final String PARAM_DATE_RANGE = "dateRange";
   public static final String PARAM_SLOW_PROCESS_INSTANCE_INTEGER = "slowProcessInstanceInteger";
   private static final String AGGREGATION_CREATE_TIME_FILTER = "createTimeFilter";
   private static final String AGGREGATION_CREATE_TIME_HISTOGRAM = "createTimeHistogram";
   private static final String AGGREGATION_END_TIME_FILTER = "endTimeFilter";
   private static final String AGGREGATION_END_TIME_HISTOGRAM = "endTimeHistogram";
   private static final String AGGREGATION_ACTIVITY_NAME_TERM = "activityNameTerm";
   private static final String AGGREGATION_STATISTICS = "statistics";

   public ProcessInstanceOverviewReportGeneratorCustom() {
   }

   // Retorna el título del reporte
   public String getTitleKey() {
      // return "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.TITLE";
      return "Resumen de instancia de procesos personalizada";
   }

   // Retorna el ID del reporte
   public String getID() {
      return "report.generator.p.overview.custom";
   }

   // Retorna el nombre:
   public String getName() {
      return "Process instances overview custom";
   }

   // Retorna el tipo
   public String getType() {
      return "report custom";
   }

   // Convierte los parámetros en JSON para la UI del reporte.
   public String getParameters(ObjectMapper objectMapper, Map<String, Object> parameterValues) {
      ParametersDefinition definition = new ParametersDefinition();
      definition.getParameters().add(this.createProcessDefinitionParameter(parameterValues.get("processDefinitionId")));
      definition.getParameters().add(this.createDateRangeParameter(parameterValues.get("dateRange")));
      definition.getParameters()
            .add(this.createSlowProcessInstanceNumberParameter(parameterValues.get("slowProcessInstanceInteger")));
      definition.getParameters().add(this.createProcessStatusParameter(parameterValues.get("status")));

      try {
         return objectMapper.writeValueAsString(definition);
      } catch (JsonProcessingException var5) {
         return null;
      }
   }

   // Parámetro para seleccionar una definición de proceso.
   protected Parameter createProcessDefinitionParameter(Object value) {
      return new Parameter("processDefinitionId", (String) null, "Definición de procesos (custom)", "processDefinition",
            value);
   }

   // Parámetro de rango de fechas.
   protected Parameter createDateRangeParameter(Object value) {
      return new Parameter("dateRange", (String) null, "Rango de fechas (custom)", "dateRange", value);
   }

   // Parámetro para definir cuántas instancias lentas mostrar.
   protected Parameter createSlowProcessInstanceNumberParameter(Object value) {
      return new Parameter("slowProcessInstanceInteger", (String) null,
            "¿Cuántas de las instancias del proceso más lentas deben mostrarse? (custom)", "integer",
            value != null ? value : 10);
   }

   // Parámetro para filtrar por estado del proceso.
   protected Parameter createProcessStatusParameter(Object value) {
      return new Parameter("status", (String) null, "Estado del proceso (custom)", "status",
            value != null ? value : null);
   }

   /* Método principal de generación de reportes */

   /*
    * Este es el método principal que genera el reporte. Flujo de ejecución:
    * Obtener parámetros (status, dateRange, etc.).
    * Ejecutar consultas en Elasticsearch para obtener datos sobre:
    * Duración de actividades.
    * Histogramas de fechas.
    * Instancias de procesos más lentas.
    * Generar visualizaciones:
    * Gráfico de torta con la duración de actividades.
    * Tabla con detalles de duración de actividades.
    * Histograma de fechas de tareas.
    * Tabla con detalles de las instancias más lentas.
    */
   public ReportDataRepresentation generate(ProcessEngine processEngine, AnalyticsClient analyticsClient,
         ReportingIndexManager indexManager, User currentUser, UserCache userCache, ObjectMapper objectMapper,
         Map<String, Object> parameterMap) {

      // Crea una nueva instancia de ReportDataRepresentation que almacenará los datos
      // del reporte.
      ReportDataRepresentation reportData = new ReportDataRepresentation();
      String status = (String) parameterMap.get("status");
      // Ejecuta una consulta para obtener la duración de las actividades.
      SearchResponse activityDurationResponse = this.getExecuteActivityDurationQuery(analyticsClient, indexManager,
            currentUser, parameterMap);
      // Genera un gráfico de pastel (pie chart) de la duración de las actividades y
      // lo añade al reporte.
      this.generateActivityDurationPieChart(reportData, activityDurationResponse);
      // Genera una tabla con la duración de las actividades y la añade al reporte.
      this.generateActivityDurationTable(reportData, activityDurationResponse);
      // // Ejecuta una consulta para obtener la duración de las instancias de
      // proceso.
      SearchResponse processInstanceResponse = this.getExecuteProcessInstanceDurationQuery(analyticsClient,
            indexManager, currentUser, parameterMap);
      Date startDate = this.getStartDate(parameterMap); // Obtiene la fecha de inicio del rango de fechas del mapa de
                                                        // parámetros.
      Date endDate = this.getEndDate(parameterMap); // Obtiene la fecha de fin del rango de fechas del mapa de
                                                    // parámetros.
      // Genera un histograma de fechas de tareas y lo añade al reporte.
      this.generateTaskDateHistogram(reportData, processInstanceResponse, startDate, endDate);
      // Obtiene una lista de IDs de las instancias de proceso más lentas.
      List<String> slowestProcessInstanceIds = this.getProcessInstanceIds(processInstanceResponse);
      // Obtiene el número de instancias de proceso lentas que se deben mostrar, a
      // partir del mapa de parámetros.
      Integer nrOfSlowProcessInstancesToDisplay = (Integer) parameterMap.get("slowProcessInstanceInteger");
      // Ejecuta una consulta para obtener las variables de las instancias de proceso
      // más lentas.
      Map<String, List<Pair<String, Object>>> processInstanceVariables = this
            .executeFetchVariableForSlowestProcessInstanceQuery(analyticsClient, indexManager, currentUser,
                  nrOfSlowProcessInstancesToDisplay, slowestProcessInstanceIds, status);
      // Genera una tabla con las instancias de proceso más lentas y la añade al
      // reporte.
      this.generateSlowProcessInstancesTable(reportData, processInstanceResponse, processInstanceVariables);

      // Retorna el objeto ReportDataRepresentation que contiene todo el reporte
      // generado.
      return reportData;

   }

   /* Métodos para consultas a Elasticsearch */
   // Consulta la duración de instancias de procesos.
   protected SearchResponse executeProcessInstanceDurationQuery(AnalyticsClient analyticsClient,
         ReportingIndexManager indexManager, User currentUser, String processDefinitionId, Date startDate, Date endDate,
         Integer fetchSize, String status) {
      CalendarInterval dateInterval = this.determineDateInterval(startDate, endDate);
      SearchResponse searchResponse = null;

      try {
         // Construye una consulta de rango para 'createTime' entre 'startDate' y
         // 'endDate'
         // Esta consulta busca documentos donde el campo 'createTime' esté entre
         // 'startDate' y 'endDate'
         Query rq1 = Query.of((q) -> {
            return q.range((r) -> {
               return r.date((d) -> {
                  return (ObjectBuilder) ((DateRangeQuery.Builder) d.field("createTime")
                        .gte(Long.toString(startDate.getTime()))).lte(Long.toString(endDate.getTime()));
               });
            });
         });
         // Construye una consulta de rango para 'endTime' entre 'startDate' y 'endDate'
         Query rq2 = Query.of((q) -> {
            return q.range((r) -> {
               return r.date((d) -> {
                  return (ObjectBuilder) ((DateRangeQuery.Builder) d.field("endTime")
                        .gte(Long.toString(startDate.getTime()))).lte(Long.toString(endDate.getTime()));
               });
            });
         });
         // Obtiene el índice adecuado para el usuario actual
         String i = indexManager.getIndexForUser(currentUser, "process-instances");

         // Crea la consulta base utilizando los parámetros proporcionados
         Query baseQuery = this.createBaseQuery(processDefinitionId, startDate, endDate, status);

         // Define las opciones de ordenamiento por 'duration' en orden descendente
         SortOptions so = SortOptions.of((s) -> {
            return s.field((f) -> {
               return f.field("duration").order(SortOrder.Desc).unmappedType(FieldType.Long);
            });
         });

         // Define una agregación de histograma de fechas para 'createTime'
         // Agrupa documentos por el campo createTime en intervalos definidos por
         // dateInterval
         Aggregation agg1 = Aggregation.of((ag) -> {
            return ag.filter(this.applyStatusProcessFilter(rq1, status)).aggregations("createTimeHistogram", (agh) -> {
               return agh.dateHistogram((h) -> {
                  return h.field("createTime").calendarInterval(dateInterval);
               });
            });
         });

         // Define una agregación de histograma de fechas para 'endTime'
         // Agrupa documentos por el campo endTime en los mismos intervalos.
         Aggregation agg2 = Aggregation.of((ag) -> {
            return ag.filter(this.applyStatusProcessFilter(rq2, status)).aggregations("endTimeHistogram", (agh) -> {
               return agh.dateHistogram((h) -> {
                  return h.field("endTime").calendarInterval(dateInterval);
               });
            });
         });

         // Construye la solicitud de búsqueda con las consultas, ordenamientos y
         // agregaciones definidas
         SearchRequest searchRequest = (new SearchRequest.Builder()).index(i, new String[0]).query(baseQuery)
               .sort(so, new SortOptions[0]).size(fetchSize != null && fetchSize > 0 ? fetchSize : 1)
               .aggregations("createTimeFilter", agg1).aggregations("endTimeFilter", agg2).build();
         // Ejecuta la búsqueda utilizando el cliente de analítica
         searchResponse = analyticsClient.search(searchRequest);
      } catch (Exception var19) {
         // Registra una advertencia en caso de que la consulta falle
         logger.warn("Could not execute query for process instance durations", var19);
      }

      return searchResponse;
   }

   // Consulta base de las queries
   protected Query createBaseQuery(String processDefinitionId, Date startDate, Date endDate, String status) {
      // Crea una consulta de rango para el campo 'timeStamp' entre 'startDate' y
      // 'endDate'
      Query rq = Query.of((qx) -> {
         return qx.range((r) -> {
            return r.date((d) -> {
               return (ObjectBuilder) ((DateRangeQuery.Builder) d.field("timeStamp")
                     .gte(Long.toString(startDate.getTime()))).lte(Long.toString(endDate.getTime()));
            });
         });
      });
      // Crea una consulta booleana que debe cumplir las siguientes condiciones
      Query q = Query.of((qu) -> {
         return qu.bool((bq) -> {
            // La consulta debe coincidir exactamente con 'processDefinitionId' en el campo
            // 'processDefinitionId.keyword'
            return bq.must((m) -> {
               return m.term((t) -> {
                  return t.field("processDefinitionId.keyword").value(processDefinitionId);
               });
            })
                  // Aplica un filtro adicional basado en el estado del proceso
                  .filter(this.applyStatusProcessFilter(rq, status), new Query[0]);
         });
      });
      // Devuelve la consulta construida
      return q;
   }

   // Consulta la duración de actividades.
   protected SearchResponse executeActivityDurationQuery(AnalyticsClient analyticsClient,
         ReportingIndexManager indexManager, User currentUser, String processDefinitionId, Date startDate, Date endDate,
         String status) {
      SearchResponse searchResponse = null;

      try {
         // Crea una consulta de rango para filtrar por 'timeStamp' entre 'startDate' y
         // 'endDate'.
         Query rq = Query.of((qx) -> {
            return qx.range((r) -> {
               return r.date((d) -> {
                  return (ObjectBuilder) ((DateRangeQuery.Builder) d.field("timeStamp")
                        .gte(Long.toString(startDate.getTime()))).lte(Long.toString(endDate.getTime()));
               });
            });
         });
         // Obtiene el índice adecuado para el usuario actual y el tipo
         // 'process-instance-activities'.
         String i = indexManager.getIndexForUser(currentUser, "process-instance-activities");

         // Crea una consulta booleana que:
         // - Debe coincidir con el 'processDefinitionId'.
         // - Aplica un filtro adicional basado en el estado de la actividad.
         Query q = Query.of((qu) -> {
            return qu.bool((bq) -> {
               return bq.must((m) -> {
                  return m.term((t) -> {
                     return t.field("processDefinitionId.keyword").value(processDefinitionId);
                  });
               }).filter(this.applyStatusProcessFilter(rq, status), new Query[0]);
            });
         });
         // Define una agregación que:
         // - Agrupa por 'activityName.keyword'.
         // - Ordena las actividades por la suma de sus duraciones en orden descendente.
         // - Calcula estadísticas extendidas (como promedio, mínimo, máximo, etc.) de la
         // duración.
         Aggregation agg = Aggregation.of((ag) -> {
            return ag.terms((t) -> {
               return t.field("activityName.keyword").order(NamedValue.of("statistics.sum", SortOrder.Desc),
                     new NamedValue[0]);
            }).aggregations("statistics", (ags) -> {
               return ags.extendedStats((es) -> {
                  return (ObjectBuilder) es.field("duration");
               });
            });
         });
         // Construye la solicitud de búsqueda con:
         // - El índice determinado.
         // - La consulta definida.
         // - La agregación configurada.
         SearchRequest searchRequest = (new SearchRequest.Builder()).index(i, new String[0]).query(q)
               .aggregations("activityNameTerm", agg).build();
         searchResponse = analyticsClient.search(searchRequest); // Ejecuta la consulta utilizando el cliente de
                                                                 // analítica.
      } catch (Exception var14) {
         logger.warn("Could not execute activity duration query", var14); // Registra una advertencia en caso de que la
                                                                          // consulta falle.
      }

      return searchResponse;
   }

   // Obtiene variables de las instancias de proceso más lentas.
   protected Map<String, List<Pair<String, Object>>> executeFetchVariableForSlowestProcessInstanceQuery(
         AnalyticsClient analyticsClient, ReportingIndexManager indexManager, User currentUser, int fetchSize,
         List<String> processInstanceIds, String status) {
      // Inicializa el mapa que almacenará las variables de cada instancia de proceso.
      Map<String, List<Pair<String, Object>>> result = new HashMap();
      SearchResponse searchResponse = null;

      try {
         // Convierte la lista de IDs de instancias de proceso en una lista de
         // FieldValue. Esto es necesario para construir la consulta de términos que
         // buscará estas instancias específicas en Elasticsearch.
         List<FieldValue> fvs = processInstanceIds.stream().map(FieldValue::of).toList();
         // Crea una consulta booleana que:
         // - Debe coincidir con los IDs de las instancias de proceso proporcionadas.
         // - Aplica un filtro adicional basado en el estado de la instancia de proceso.
         Query qu = Query.of((q) -> {
            return q.bool((bq) -> {
               return bq.must((mq) -> {
                  return mq.terms((t) -> {
                     return t.terms((tqf) -> {
                        return tqf.value(fvs);
                     }).field("processInstanceId.keyword");
                  });
               }).minimumShouldMatch(String.valueOf(1)).filter(this.applyStatusProcessFilter(status), new Query[0]);
            });
         });
         // Obtiene el índice adecuado para el usuario actual y el tipo 'variables'.
         String i = indexManager.getIndexForUser(currentUser, "variables");
         // Define las opciones de ordenamiento para la consulta, ordenando por
         // 'name.keyword' en orden ascendente.
         SortOptions so = SortOptions.of((s) -> {
            return s.field((f) -> {
               return f.field("name.keyword").order(SortOrder.Asc).unmappedType(FieldType.Keyword);
            });
         });
         // Construye la solicitud de búsqueda con:
         // - El índice determinado.
         // - La consulta definida.
         // - El tamaño de resultados, calculado como 'fetchSize * 50'.
         // - La opción de ordenamiento configurada.
         SearchRequest searchRequest = (new SearchRequest.Builder()).index(i, new String[0]).query(qu)
               .size(fetchSize * 50).sort(so, new SortOptions[0]).build();
         searchResponse = analyticsClient.search(searchRequest); // Ejecuta la consulta utilizando el cliente de
                                                                 // analítica.
         List<Hit> searchHits = searchResponse.hits().hits(); // Obtiene las coincidencias de la búsqueda.
         Iterator var15 = searchHits.iterator();

         // Itera sobre cada resultado de la búsqueda.
         while (var15.hasNext()) {
            Hit searchHit = (Hit) var15.next();
            Map<String, Object> variableData = (Map) searchHit.source(); // Obtiene los datos de la variable desde la
                                                                         // fuente del resultado.
            String processInstanceId = (String) variableData.get("processInstanceId"); // Obtiene el ID de la instancia
                                                                                       // de proceso asociado a la
                                                                                       // variable.
            if (!result.containsKey(processInstanceId)) { // Si el resultado no contiene ya una entrada para este ID de
                                                          // instancia de proceso, la crea.
               result.put(processInstanceId, new ArrayList());
            }

            Object value = this.getVariableValue(variableData); // Obtiene el valor de la variable utilizando el método
                                                                // 'getVariableValue'.
            if (value != null) { // Si el valor no es nulo, lo añade a la lista de variables de la instancia de
                                 // proceso correspondiente.
               ((List) result.get(processInstanceId)).add(Pair.of((String) variableData.get("name"), value));
            }
         }
      } catch (Exception var20) {
         logger.warn("Could not fetch variables for slowest process instances", var20); // Registra una advertencia en
                                                                                        // caso de que la consulta
                                                                                        // falle.
      }
      // Devuelve el mapa de resultados que contiene las variables de cada instancia
      // de proceso.
      return result;
   }

   // Este método determina el intervalo de calendario adecuado (por ejemplo, día,
   // semana, mes) entre las fechas de inicio y fin proporcionadas.
   protected CalendarInterval determineDateInterval(Date startDate, Date endDate) {
      long dateDifference = endDate.getTime() - startDate.getTime();
      CalendarInterval dateInterval = CalendarInterval.Day;
      if (dateDifference > 2764800000L) {
         if (dateDifference > 38880000000L) {
            dateInterval = CalendarInterval.Year;
         } else {
            dateInterval = CalendarInterval.Month;
         }
      }

      return dateInterval;
   }

   /* Métodos para generar gráficos */

   // Crea un histograma con conteos de instancias de procesos en el tiempo.
   protected void generateTaskDateHistogram(ReportDataRepresentation reportData,
         SearchResponse<FilterAggregate> searchResponse, Date startDate, Date endDate) {
      MultiBarChart histogramBartChart = new MultiBarChart(); // Crea una instancia de MultiBarChart para representar el
                                                              // histograma.
      histogramBartChart.setTitle("Process instance counts"); // Establece el título del histograma.
      histogramBartChart.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.HISTOGRAM-TITLE"); // Clave
                                                                                                              // de
                                                                                                              // título
                                                                                                              // para
                                                                                                              // internacionalización.
      histogramBartChart
            .setDescriptionKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.HISTOGRAM-DESCRIPTION"); // Clave
                                                                                                              // de
                                                                                                              // descripción
                                                                                                              // para
                                                                                                              // internacionalización.
      histogramBartChart.setyAxisType("count"); // Establece el tipo del eje Y como 'count'.
      // Determina el intervalo de fechas adecuado (día, mes, año) según el rango
      // proporcionado.
      CalendarInterval interval = this.determineDateInterval(startDate, endDate);
      histogramBartChart.setxAxisType("date_day"); // Por defecto, el eje X es por día.
      if (CalendarInterval.Month.equals(interval)) {
         histogramBartChart.setxAxisType("date_month"); // Si el intervalo es mensual, ajusta el eje X.
      } else if (CalendarInterval.Year.equals(interval)) {
         histogramBartChart.setxAxisType("date_year"); // Si el intervalo es anual, ajusta el eje X.
      }
      // Añade el histograma al reporte de datos.
      reportData.addReportDataElement(histogramBartChart);
      if (searchResponse != null) { // Verifica si la respuesta de búsqueda no es nula.

         // Obtiene las agregaciones de la respuesta de búsqueda.
         Map<String, Aggregate> aggregations = searchResponse.aggregations();
         FilterAggregate createTimeFilter = ((Aggregate) aggregations.get("createTimeFilter")).filter();
         FilterAggregate endTimeFilter = ((Aggregate) aggregations.get("endTimeFilter")).filter();

         // Verifica que ambas agregaciones de filtro no sean nulas.
         if (createTimeFilter != null && endTimeFilter != null) {
            // Obtiene los histogramas de fechas de creación y finalización.
            DateHistogramAggregate createTimeHistogram = ((Aggregate) createTimeFilter.aggregations()
                  .get("createTimeHistogram")).dateHistogram();
            DateHistogramAggregate endTimeHistogram = ((Aggregate) endTimeFilter.aggregations().get("endTimeHistogram"))
                  .dateHistogram();
            // Lista para almacenar los valores del histograma de fechas de creación.
            List<List<Object>> createTimeValues = new ArrayList();
            if (createTimeHistogram != null) {

               // Itera sobre cada bucket del histograma de fechas de creación.
               Iterator var13 = createTimeHistogram.buckets().array().iterator();

               while (var13.hasNext()) {
                  DateHistogramBucket bucket = (DateHistogramBucket) var13.next();
                  List<Object> objects = new ArrayList();
                  objects.add(Date.from(Instant.ofEpochMilli(bucket.key()))); // Convierte la clave del bucket a fecha.
                  objects.add(bucket.docCount()); // Añade el conteo de documentos.
                  createTimeValues.add(objects);
               }
            }
            // Lista para almacenar los valores del histograma de fechas de finalización.
            List<List<Object>> endTimeValues = new ArrayList();
            if (endTimeHistogram != null) {
               // Itera sobre cada bucket del histograma de fechas de finalización.
               Iterator var18 = endTimeHistogram.buckets().array().iterator();

               while (var18.hasNext()) {
                  DateHistogramBucket bucket = (DateHistogramBucket) var18.next();
                  List<Object> objects = new ArrayList();
                  objects.add(Date.from(Instant.ofEpochMilli(bucket.key()))); // Convierte la clave del bucket a fecha.
                  objects.add(bucket.docCount()); // Añade el conteo de documentos.
                  endTimeValues.add(objects);
               }
            }
            // Normaliza los valores de los histogramas de creación y finalización.
            Pair<List<List<Object>>, List<List<Object>>> normalizedValues = ReportingDataUtil
                  .normalizeHistogramValues(createTimeValues, endTimeValues);
            histogramBartChart.addValue("started", (List) normalizedValues.getLeft()); // Añade los valores normalizados
                                                                                       // de inicio al histograma.
            histogramBartChart.addValue("completed", (List) normalizedValues.getRight()); // Añade los valores
                                                                                          // normalizados de
                                                                                          // finalización al histograma
         }
      }
   }

   /*
    * ​El método getTaskDateHistogramData extrae y organiza datos de histogramas de
    * fechas desde una respuesta de búsqueda de Elasticsearch,
    * devolviendo un mapa que contiene listas de valores correspondientes a las
    * instancias de proceso "started" y "completed".
    */
   protected Map<String, List<List<Object>>> getTaskDateHistogramData(SearchResponse<FilterAggregate> searchResponse) {
      Map<String, List<List<Object>>> reportData = new HashMap();

      // Obtiene las agregaciones de la respuesta de búsqueda.
      Map<String, Aggregate> aggregations = searchResponse.aggregations();
      // Extrae las agregaciones de filtro para tiempos de creación y finalización.
      FilterAggregate createTimeFilter = ((Aggregate) aggregations.get("createTimeFilter")).filter();
      FilterAggregate endTimeFilter = ((Aggregate) aggregations.get("endTimeFilter")).filter();
      // Verifica que ambas agregaciones de filtro no sean nulas.
      if (createTimeFilter != null && endTimeFilter != null) {
         // Obtiene las agregaciones de histograma de fechas para tiempos de creación y
         // finalización.
         DateHistogramAggregate createTimeHistogram = ((Aggregate) createTimeFilter.aggregations()
               .get("createTimeHistogram")).dateHistogram();
         DateHistogramAggregate endTimeHistogram = ((Aggregate) endTimeFilter.aggregations().get("endTimeHistogram"))
               .dateHistogram();
         List<List<Object>> createTimeValues = new ArrayList(); // Lista para almacenar los valores del histograma de
                                                                // tiempos de creación.
         if (createTimeHistogram != null) {
            Iterator var9 = createTimeHistogram.buckets().array().iterator(); // Itera sobre cada bucket del histograma
                                                                              // de tiempos de creación.

            while (var9.hasNext()) {
               DateHistogramBucket bucket = (DateHistogramBucket) var9.next();
               List<Object> objects = new ArrayList();
               objects.add(Date.from(Instant.ofEpochMilli(bucket.key()))); // Convierte la clave del bucket a fecha.
               objects.add(bucket.docCount()); // Añade el conteo de documentos.
               createTimeValues.add(objects);
            }
         }

         List<List<Object>> endTimeValues = new ArrayList(); // Lista para almacenar los valores del histograma de
                                                             // tiempos de finalización.
         if (endTimeHistogram != null) {
            Iterator var13 = endTimeHistogram.buckets().array().iterator(); // Itera sobre cada bucket del histograma de
                                                                            // tiempos de finalización.

            while (var13.hasNext()) {
               DateHistogramBucket bucket = (DateHistogramBucket) var13.next();
               List<Object> objects = new ArrayList();
               objects.add(Date.from(Instant.ofEpochMilli(bucket.key()))); // Convierte la clave del bucket a fecha.
               objects.add(bucket.docCount()); // Añade el conteo de documentos.
               endTimeValues.add(objects);
            }
         }
         // Normaliza los valores de los histogramas de creación y finalización.
         Pair<List<List<Object>>, List<List<Object>>> normalizedValues = ReportingDataUtil
               .normalizeHistogramValues(createTimeValues, endTimeValues);
         // Añade los valores normalizados al mapa de datos del reporte.
         reportData.put("started", (List) normalizedValues.getLeft());
         reportData.put("completed", (List) normalizedValues.getRight());
      }

      return reportData;
   }

   // ​El método getAxisType determina el tipo de eje temporal que se debe utilizar
   // en una representación gráfica, basándose en el intervalo de fechas
   // proporcionado.
   protected String getAxisType(Date startDate, Date endDate) {
      CalendarInterval interval = this.determineDateInterval(startDate, endDate);
      if (CalendarInterval.Month.equals(interval)) {
         return "date_month";
      } else {
         return CalendarInterval.Year.equals(interval) ? "date_year" : "date_day";
      }
   }

   // El método generateActivityDurationPieChart se encarga de crear un gráfico de
   // pastel que representa la duración total de las actividades y lo añade al
   // reporte.
   protected void generateActivityDurationPieChart(ReportDataRepresentation reportData, SearchResponse searchResponse) {
      // Obtiene un mapa con los datos de duración de actividades a partir de la
      // respuesta de búsqueda.
      Map<String, Double> activityDurationData = this.getActivityDurationData(searchResponse);
      // Crea una representación de gráfico de pastel utilizando los datos de duración
      // de actividades.
      PieChartDataRepresentation activityDurationPieChart = this.createActivityDurationPieChart(activityDurationData);
      reportData.addReportDataElement(activityDurationPieChart);
   }

   // Método auxiliar para estructurar los datos del gráfico de torta. ​El método
   // createActivityDurationPieChart construye un gráfico de pastel que representa
   // la duración total de cada actividad.
   protected PieChartDataRepresentation createActivityDurationPieChart(Map<String, Double> activitiDurationData) {
      PieChartDataRepresentation pieChart = new PieChartDataRepresentation(); // Crea una nueva instancia de
                                                                              // PieChartDataRepresentation para el
                                                                              // gráfico de pastel.
      pieChart.setTitle("Process steps total time"); // Establece el título del gráfico.
      pieChart.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-CHART-TITLE"); // Establece
                                                                                                                  // la
                                                                                                                  // clave
                                                                                                                  // del
                                                                                                                  // título
                                                                                                                  // para
                                                                                                                  // internacionalización.
      pieChart.setDescriptionKey(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-CHART-DESCRIPTION"); // Establece la
                                                                                                         // clave de la
                                                                                                         // descripción
                                                                                                         // para
                                                                                                         // internacionalización.
      Iterator var3 = activitiDurationData.keySet().iterator(); // Itera sobre cada entrada en el mapa de datos de
                                                                // duración de actividades.

      while (var3.hasNext()) {
         String activitiDuration = (String) var3.next();
         pieChart.add(activitiDuration, (Number) activitiDurationData.get(activitiDuration)); // Añade cada actividad y
                                                                                              // su duración al gráfico
                                                                                              // de pastel.
      }
      // Devuelve la representación del gráfico de pastel.
      return pieChart;
   }

   // El método getActivityDurationData procesa la respuesta de una búsqueda de
   // Elasticsearch para extraer la duración total de cada actividad y las
   // convierte a horas.
   protected Map<String, Double> getActivityDurationData(SearchResponse<StringTermsAggregate> searchResponse) {
      Map<String, Double> reportData = new HashMap();
      Map<String, Aggregate> aggregations = searchResponse.aggregations(); // Obtiene las agregaciones de la respuesta
                                                                           // de búsqueda
      StringTermsAggregate termsAggregation = ((Aggregate) aggregations.get("activityNameTerm")).sterms(); // Extrae la
                                                                                                           // agregación
                                                                                                           // de
                                                                                                           // términos
                                                                                                           // para los
                                                                                                           // nombres de
                                                                                                           // las
                                                                                                           // actividades.
      if (termsAggregation != null) { // Verifica si la agregación de términos no es nula.
         Iterator var5 = termsAggregation.buckets().array().iterator(); // Itera sobre cada bucket en la agregación de
                                                                        // términos.

         while (var5.hasNext()) {
            StringTermsBucket termsBucket = (StringTermsBucket) var5.next();
            ExtendedStatsAggregate stats = ((Aggregate) termsBucket.aggregations().get("statistics")).extendedStats(); // Obtiene
                                                                                                                       // la
                                                                                                                       // agregación
                                                                                                                       // de
                                                                                                                       // estadísticas
                                                                                                                       // extendidas
                                                                                                                       // para
                                                                                                                       // el
                                                                                                                       // bucket
                                                                                                                       // actual.
            if (stats != null) { // Verifica si la agregación de estadísticas no es nula.
               reportData.put(termsBucket.key().stringValue(), ReportingDataUtil.convertToHours(stats.sum())); // Convierte
                                                                                                               // la
                                                                                                               // suma
                                                                                                               // de la
                                                                                                               // duración
                                                                                                               // a
                                                                                                               // horas
                                                                                                               // y la
                                                                                                               // almacena
                                                                                                               // en el
                                                                                                               // mapa
                                                                                                               // con el
                                                                                                               // nombre
                                                                                                               // de la
                                                                                                               // actividad
                                                                                                               // como
                                                                                                               // clave.
            }
         }
      }
      // Retorna el mapa con los datos del reporte.
      return reportData;
   }

   /* Métodos para generar tablas */

   // ​El método generateActivityDurationTable se encarga de crear una tabla que
   // muestra las estadísticas de duración de las actividades y añadirla al
   // reporte.
   protected void generateActivityDurationTable(ReportDataRepresentation reportData, SearchResponse searchResponse) {
      // Obtiene un mapa con las estadísticas de duración de actividades a partir de
      // la respuesta de búsqueda.
      Map<String, ExtendedStatsAggregate> activityDurationTableData = this.getActivityDurationTableData(searchResponse);
      // Crea una representación de tabla utilizando los datos de duración de
      // actividades.
      TableDataRepresentation generateActivityDurationTable = this
            .createActivityDurationTable(activityDurationTableData);
      // Añade la tabla al reporte.
      reportData.addReportDataElement(generateActivityDurationTable);
   }

   // Genera una tabla con duración de actividades.
   protected TableDataRepresentation generateActivityDurationTable(
         SearchResponse<StringTermsAggregate> searchResponse) {
      // Crea una nueva instancia de TableDataRepresentation para la tabla.
      TableDataRepresentation tableData = new TableDataRepresentation();
      tableData.setTitle("Activity duration details"); // Establece el título de la tabla.
      tableData.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-TITLE"); // Establece
                                                                                                                   // la
                                                                                                                   // clave
                                                                                                                   // del
                                                                                                                   // título
                                                                                                                   // para
                                                                                                                   // su
                                                                                                                   // posible
                                                                                                                   // internacionalización.
      tableData.setDescriptionKey(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-DESCRIPTION"); // Establece la
                                                                                                         // clave de la
                                                                                                         // descripción
                                                                                                         // para su
                                                                                                         // posible
                                                                                                         // internacionalización.

      // Define los nombres de las columnas de la tabla.
      tableData.setColumnNames(Arrays.asList("Activity", "Count", "Sum", "Min duration", "Max duration",
            "Average duration", "Stddev duration"));
      // Define las claves de los nombres de las columnas para internacionalización.
      tableData.setColumnNameKeys(
            Arrays.asList("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-ACTIVITY",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.COUNT",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SUM",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.MIN-DURATION",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.MAX-DURATION",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.AVERAGE",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.STDDEV"));
      // Define el centrado de las columnas (falso para el nombre de la actividad,
      // verdadero para los valores numéricos).
      tableData.setColumnsCentered(Arrays.asList(false, true, true, true, true, true));
      Map<String, Aggregate> aggregations = searchResponse.aggregations(); // Obtiene las agregaciones de la respuesta
                                                                           // de búsqueda.

      StringTermsAggregate termsAggregation = ((Aggregate) aggregations.get("activityNameTerm")).sterms(); // Extrae la
                                                                                                           // agregación
                                                                                                           // de
                                                                                                           // términos
                                                                                                           // para los
                                                                                                           // nombres de
                                                                                                           // las
                                                                                                           // actividades.

      if (termsAggregation != null) { // Verifica si la agregación de términos no es nula.
         Iterator var5 = termsAggregation.buckets().array().iterator(); // Itera sobre cada bucket en la agregación de
                                                                        // términos.

         while (var5.hasNext()) {
            StringTermsBucket termsBucket = (StringTermsBucket) var5.next();
            // Obtiene la agregación de estadísticas extendidas para el bucket actual.
            ExtendedStatsAggregate stats = ((Aggregate) termsBucket.aggregations().get("statistics")).extendedStats();
            if (stats != null) { // Verifica si la agregación de estadísticas no es nula.
               List<TableDataRepresentation.TableDataEntry> row = new ArrayList(); // Crea una lista para almacenar los
                                                                                   // datos de la fila.
               // Agrega los datos de la actividad a la fila.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(termsBucket.key())); // Nombre de la
                                                                                                  // actividad.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(stats.count())); // Número de instancias de
                                                                                              // la actividad
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
                     ReportingDataUtil.convertToHours(stats.sum()))); // Duración total.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
                     ReportingDataUtil.convertToHours(stats.min()))); // Duración mínima.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
                     ReportingDataUtil.convertToHours(stats.max()))); // Duración máxima.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
                     ReportingDataUtil.convertToHours(stats.avg()))); // Duración promedio.
               row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
                     ReportingDataUtil.convertToHours(stats.stdDeviation()))); // Desviación estándar.
               tableData.addRow(row); // Agrega la fila a la tabla.
            }
         }
      }

      return tableData;
   }

   // Método auxiliar para crear la tabla.
   protected TableDataRepresentation createActivityDurationTable(Map<String, ExtendedStatsAggregate> reportData) {
      TableDataRepresentation tableData = new TableDataRepresentation(); // Crea una nueva instancia de
                                                                         // TableDataRepresentation para la tabla.
      tableData.setTitle("Activity durations"); // Establece el título de la tabla.
      tableData.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-TITLE"); // Establece
                                                                                                                   // la
                                                                                                                   // clave
                                                                                                                   // del
                                                                                                                   // título
                                                                                                                   // para
                                                                                                                   // su
                                                                                                                   // posible
                                                                                                                   // internacionalización.
      tableData.setDescriptionKey(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-DESCRIPTION"); // Establece la
                                                                                                         // clave de la
                                                                                                         // descripción
                                                                                                         // para su
                                                                                                         // posible
                                                                                                         // internacionalización.
      tableData.setColumnNames(Arrays.asList("Activity", "Count", "Sum", "Min duration", "Max duration",
            "Average duration", "Stddev duration")); // Define los nombres de las columnas de la tabla.
      // Define las claves de los nombres de las columnas para internacionalización.
      tableData.setColumnNameKeys(
            Arrays.asList("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.ACTIVITY-DURATION-TABLE-ACTIVITY",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.COUNT",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SUM",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.MIN-DURATION",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.MAX-DURATION",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.AVERAGE",
                  "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.STDDEV"));
      // Define el centrado de las columnas (falso para el nombre de la actividad,
      // verdadero para los valores numéricos).
      tableData.setColumnsCentered(Arrays.asList(false, true, true, true, true, true));
      Iterator var3 = reportData.keySet().iterator(); // Itera sobre las claves (nombres de actividades) en el mapa de
                                                      // datos.

      while (var3.hasNext()) {
         String key = (String) var3.next();
         List<TableDataRepresentation.TableDataEntry> row = new ArrayList(); // Crea una lista para almacenar los datos
                                                                             // de la fila.
         ExtendedStatsAggregate stat = (ExtendedStatsAggregate) reportData.get(key); // Obtiene las estadísticas de la
                                                                                     // actividad actual.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(key)); // Nombre de la actividad.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(stat.count())); // Número de instancias de la
                                                                                       // actividad.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(ReportingDataUtil.convertToHours(stat.sum()))); // Duración
                                                                                                                       // total.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(ReportingDataUtil.convertToHours(stat.min()))); // Duración
                                                                                                                       // mínima.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(ReportingDataUtil.convertToHours(stat.max()))); // Duración
                                                                                                                       // máxima.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(ReportingDataUtil.convertToHours(stat.avg()))); // Duración
                                                                                                                       // promedio.
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
               ReportingDataUtil.convertToHours(stat.stdDeviation())));// Desviación estándar.
         // Agrega la fila a la tabla.
         tableData.addRow(row);
      }

      return tableData;
   }

   // ​El método getActivityDurationTableData extrae estadísticas de duración de
   // actividades desde una respuesta de búsqueda de Elasticsearch y las organiza
   // en un mapa para su posterior uso en reportes.
   protected Map<String, ExtendedStatsAggregate> getActivityDurationTableData(
         SearchResponse<StringTermsAggregate> searchResponse) {
      // Crea un mapa para almacenar los datos del reporte, donde la clave es el
      // nombre de la actividad
      // y el valor es un objeto ExtendedStatsAggregate que contiene las estadísticas
      // de la actividad.
      Map<String, ExtendedStatsAggregate> reportData = new HashMap();
      // Obtiene el mapa de agregaciones de la respuesta de búsqueda.
      Map<String, Aggregate> aggregations = searchResponse.aggregations();
      // Extrae la agregación de términos para los nombres de las actividades.
      StringTermsAggregate termsAggregation = ((Aggregate) aggregations.get("activityNameTerm")).sterms();
      if (termsAggregation != null) { // Verifica si la agregación de términos no es nula.
         Iterator var5 = termsAggregation.buckets().array().iterator(); // Itera sobre cada bucket en la agregación de
                                                                        // términos.

         while (var5.hasNext()) {
            StringTermsBucket termsBucket = (StringTermsBucket) var5.next();
            ExtendedStatsAggregate stats = ((Aggregate) termsBucket.aggregations().get("statistics")).extendedStats(); // Obtiene
                                                                                                                       // la
                                                                                                                       // agregación
                                                                                                                       // de
                                                                                                                       // estadísticas
                                                                                                                       // extendidas
                                                                                                                       // para
                                                                                                                       // el
                                                                                                                       // bucket
                                                                                                                       // actual.
            if (stats != null) {
               reportData.put(termsBucket.key().stringValue(), stats); // Añade al mapa el nombre de la actividad y sus
                                                                       // estadísticas correspondientes.
            }
         }
      }

      return reportData;
   }

   // Método que extrae los IDs de las instancias de proceso desde una respuesta de
   // búsqueda.
   protected List<String> getProcessInstanceIds(SearchResponse slowProcessInstancesReponse) {
      List<String> ids = new ArrayList();
      List<Hit> searchHits = slowProcessInstancesReponse.hits().hits(); // Obtiene la lista de resultados (hits) de la
                                                                        // respuesta de búsqueda.
      Iterator<Hit> it = searchHits.iterator(); // Crea un iterador para recorrer la lista de resultados. Cada "hit"
                                                // representa un documento en la base de datos que coincide con la
                                                // consulta de búsqueda.

      while (it.hasNext()) {
         Hit searchHit = (Hit) it.next(); // Obtiene el resultado actual.

         Map<String, Object> data = (Map) searchHit.source(); // Extrae los datos del resultado en forma de un mapa
                                                              // clave-valor.
         ids.add((String) data.get("id")); // Obtiene el valor del campo "id" y lo agrega a la lista de IDs.

      }

      return ids;
   }

   // // Método que obtiene el valor de una variable desde un mapa de datos de
   // variables.
   protected Object getVariableValue(Map<String, Object> variableData) {
      // Verifica si el mapa contiene una clave "stringValue" y retorna su valor si
      // existe.
      if (variableData.containsKey("stringValue")) {
         return variableData.get("stringValue");
      } else if (variableData.containsKey("booleanValue")) {
         return variableData.get("booleanValue");
      } else if (variableData.containsKey("longValue")) {
         return variableData.get("longValue");
      } else if (variableData.containsKey("integerValue")) {
         return variableData.get("integerValue");
      } else if (variableData.containsKey("doubleValue")) {
         return variableData.get("doubleValue");
      } else if (variableData.containsKey("shortValue")) {
         return variableData.get("shortValue");
      } else if (variableData.containsKey("dateValue")) {
         Object date = variableData.get("dateValue");
         if (date instanceof Date) { // Si el valor ya es un objeto Date, lo retorna tal cual.
            return date;
         } else {
            // Si el valor es un número Long, lo convierte en un objeto Date.
            return date instanceof Long ? new Date((Long) date) : date;
         }
      } else {
         // Si ninguna de las claves anteriores está presente, verifica si hay un valor
         // en formato JSON y lo retorna.
         return variableData.containsKey("jsonValue") ? variableData.get("jsonValue") : null;
      }
   }

   // Genera una tabla con detalles de las instancias de procesos más lentas.
   protected void generateSlowProcessInstancesTable(ReportDataRepresentation reportData,
         SearchResponse slowProcessInstancesReponse, Map<String, List<Pair<String, Object>>> processInstanceVariables) {
      // Obtiene los datos de las instancias de procesos más lentas a partir de la
      // respuesta de búsqueda. organizándolos en un mapa donde la clave es el ID de
      // la instancia de proceso y el valor es otro mapa que contiene los detalles de
      // la instancia.
      Map<String, Map<String, Object>> slowProcessInstancesTableData = this
            .getSlowProcessInstancesTableData(slowProcessInstancesReponse);
      // Crea la tabla de detalles de las instancias de procesos más lentas,
      // utilizando los datos de las instancias y sus variables asociadas.
      // Este método construye una representación de tabla maestro-detalle
      // (MasterDetailTableDataRepresentation) que muestra los detalles de cada
      // instancia de proceso junto con sus variables asociadas.
      MasterDetailTableDataRepresentation slowProcessInstancesTable = this
            .createSlowProcessInstancesTable(slowProcessInstancesTableData, processInstanceVariables);
      reportData.addReportDataElement(slowProcessInstancesTable);
   }

   // ​El método getSlowProcessInstancesTableData extrae los datos de las
   // instancias de procesos más lentas desde una respuesta de búsqueda de
   // Elasticsearch y los organiza en un mapa para su posterior uso en reportes.
   protected Map<String, Map<String, Object>> getSlowProcessInstancesTableData(
         SearchResponse slowProcessInstancesReponse) {

      // Crea un mapa para almacenar los datos del reporte, donde la clave es el ID de
      // la instancia de proceso
      // y el valor es otro mapa que contiene los detalles de la instancia.
      Map<String, Map<String, Object>> reportData = new HashMap();
      List<Hit> searchHits = slowProcessInstancesReponse.hits().hits(); // Obtiene la lista de resultados (hits) de la
                                                                        // respuesta de búsqueda.
      Iterator<Hit> it = searchHits.iterator();

      while (it.hasNext()) {
         Hit searchHit = (Hit) it.next();
         reportData.put(searchHit.id(), (Map) searchHit.source()); // Añade al mapa el ID de la instancia de proceso y
                                                                   // sus detalles correspondientes.
      }

      return reportData;
   }

   // Método auxiliar para estructurar los datos de la tabla.
   // Crea una tabla de datos detallada con las instancias de procesos más lentas.
   protected MasterDetailTableDataRepresentation createSlowProcessInstancesTable(
         Map<String, Map<String, Object>> reportData,
         Map<String, List<Pair<String, Object>>> processInstanceVariables) {
      // Se crea una instancia de MasterDetailTableDataRepresentation para almacenar
      // la tabla de datos.
      MasterDetailTableDataRepresentation tableData = new MasterDetailTableDataRepresentation();
      tableData.setTitle("Slowest process instances"); // Configuración del título de la tabla.
      tableData.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-TITLE");
      tableData.setDescriptionKey(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-DESCRIPTION");
      tableData.setShowRowIndex(true); // Indica que se debe mostrar un índice de fila en la tabla.

      tableData.setColumnNames(Arrays.asList("Duration", "Internal ID", "Business key")); // Define los nombres de las
                                                                                          // columnas de la tabla.

      // Define claves de localización para los nombres de las columnas.
      tableData.setColumnNameKeys(Arrays.asList(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-ACTIVITI-DURATION",
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-ID",
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-BUSINESS-KEY"));
      // Configura las columnas para que no estén centradas en la tabla.
      tableData.setColumnsCentered(Arrays.asList(false, false, false, false, false));

      TableDataRepresentation detailTableData;
      // Itera sobre cada instancia de proceso en los datos del reporte.
      for (Iterator var4 = reportData.keySet().iterator(); var4.hasNext(); tableData.addDetailTable(detailTableData)) {
         String reportVal = (String) var4.next(); // Obtiene el ID de la instancia de proceso.
         Map<String, Object> source = (Map) reportData.get(reportVal); // Obtiene el mapa de datos asociado a la
                                                                       // instancia de proceso.
         List<TableDataRepresentation.TableDataEntry> row = new ArrayList(2); // Crea una fila para la tabla con la
                                                                              // información de la instancia.

         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
               ReportingDataUtil.convertToHours((Number) source.get("duration")))); // Convierte la duración de la
                                                                                    // instancia de proceso a horas y la
                                                                                    // agrega a la fila.
         String processInstanceId = (String) source.get("id"); // Obtiene el ID de la instancia de proceso y lo agrega a
                                                               // la fila.

         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(processInstanceId));
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(source.get("businessKey"))); // Obtiene la clave
                                                                                                    // de negocio y la
                                                                                                    // agrega a la fila.
         tableData.addRow(row); // Agrega la fila a la tabla principal.

         // Crea una nueva tabla de detalles para almacenar las variables de la instancia
         // de proceso.
         detailTableData = new TableDataRepresentation();
         detailTableData.setTitle("Variables");
         detailTableData
               .setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLES"); // Se
                                                                                                                         // asigna
                                                                                                                         // la
                                                                                                                         // clave
                                                                                                                         // de
                                                                                                                         // localización
                                                                                                                         // para
                                                                                                                         // el
                                                                                                                         // título
                                                                                                                         // de
                                                                                                                         // la
                                                                                                                         // tabla
                                                                                                                         // de
                                                                                                                         // variables.
         detailTableData.setColumnNames(Arrays.asList("Variable name", "Variable value")); // Se establecen los nombres
                                                                                           // de las columnas de la
                                                                                           // tabla de variables.
         // Se establecen las claves de localización para las columnas de la tabla de
         // variables.
         detailTableData.setColumnNameKeys(Arrays.asList(
               "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLE-NAME",
               "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLE-VALUE"));
         if (processInstanceVariables.containsKey(processInstanceId)) { // Verifica si existen variables asociadas a la
                                                                        // instancia de proceso.
            Iterator var10 = ((List) processInstanceVariables.get(processInstanceId)).iterator(); // Itera sobre las
                                                                                                  // variables de la
                                                                                                  // instancia de
                                                                                                  // proceso.
            while (var10.hasNext()) {
               Pair<String, Object> variablePair = (Pair) var10.next();
               List<TableDataRepresentation.TableDataEntry> detailRow = new ArrayList(2); // Crea una fila de detalle
                                                                                          // con el nombre y valor de la
                                                                                          // variable.

               detailRow.add(new TableDataRepresentation.SimpleValueTableDataEntry(variablePair.getLeft()));
               detailRow.add(new TableDataRepresentation.SimpleValueTableDataEntry(variablePair.getRight()));
               detailTableData.addRow(detailRow);
            }
         }
      }

      return tableData;
   }

   // Genera una tabla con detalles de las instancias de procesos más lentas.
   protected MasterDetailTableDataRepresentation generateSlowProcessInstancesTable(
         SearchResponse slowProcessInstancesReponse, Map<String, List<Pair<String, Object>>> processInstanceVariables) {
      MasterDetailTableDataRepresentation tableData = new MasterDetailTableDataRepresentation();
      tableData.setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-TITLE");
      tableData.setDescriptionKey(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-DESCRIPTION");
      tableData.setShowRowIndex(true);
      tableData.setColumnNameKeys(Arrays.asList(
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-ACTIVITI-DURATION",
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-ID",
            "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-BUSINESS-KEY"));
      tableData.setColumnsCentered(Arrays.asList(false, false, false, false, false));
      List<Hit> searchHits = slowProcessInstancesReponse.hits().hits();

      TableDataRepresentation detailTableData;
      for (Iterator<Hit> it = searchHits.iterator(); it.hasNext(); tableData.addDetailTable(detailTableData)) {
         Hit searchHit = (Hit) it.next();
         List<TableDataRepresentation.TableDataEntry> row = new ArrayList(2);
         Map<String, Object> source = (Map) searchHit.source();
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(
               ReportingDataUtil.convertToHours((Number) source.get("duration"))));
         String processInstanceId = (String) source.get("id");
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(processInstanceId));
         row.add(new TableDataRepresentation.SimpleValueTableDataEntry(source.get("businessKey"))); // Obtiene la clave
                                                                                                    // de negocio y la
                                                                                                    // agrega a la fila.
         tableData.addRow(row);
         detailTableData = new TableDataRepresentation();
         detailTableData
               .setTitleKey("REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLES");
         detailTableData.setColumnNameKeys(Arrays.asList(
               "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLE-NAME",
               "REPORTING.DEFAULT-REPORTS.PROCESS-INSTANCES-OVERVIEW.SLOWEST-PROCESS-INSTANCES-VARIABLE-VALUE"));
         if (processInstanceVariables.containsKey(processInstanceId)) {
            Iterator var11 = ((List) processInstanceVariables.get(processInstanceId)).iterator();

            while (var11.hasNext()) {
               Pair<String, Object> variablePair = (Pair) var11.next();
               List<TableDataRepresentation.TableDataEntry> detailRow = new ArrayList(2);
               detailRow.add(new TableDataRepresentation.SimpleValueTableDataEntry(variablePair.getLeft()));
               detailRow.add(new TableDataRepresentation.SimpleValueTableDataEntry(variablePair.getRight()));
               detailTableData.addRow(detailRow);
            }
         }
      }

      return tableData;
   }

   /**
    * Agrega un reporte de duración de actividades a la lista de datos
    * proporcionada.
    *
    * @param data           Lista de arreglos de cadenas donde se agregará el
    *                       reporte.
    * @param searchResponse Respuesta de búsqueda que contiene los datos necesarios
    *                       para el reporte.
    */
   protected void addActivityDurationReport(List<String[]> data, SearchResponse searchResponse) {
      Map<String, Double> activityDurationData = this.getActivityDurationData(searchResponse); // Obtiene los datos de
                                                                                               // duración de
                                                                                               // actividades a partir
                                                                                               // de la respuesta de
                                                                                               // búsqueda.
      this.createActivityDurationReport(data, activityDurationData); // Crea el reporte de duración de actividades y lo
                                                                     // agrega a la lista de datos.
   }

   /**
    * Crea un reporte de la duración total de las actividades y lo agrega a la
    * lista de datos proporcionada.
    *
    * @param data                 Lista de arreglos de cadenas donde se agregará el
    *                             reporte.
    * @param activityDurationData Mapa que contiene los nombres de las actividades
    *                             y sus respectivas duraciones totales.
    */
   protected void createActivityDurationReport(List<String[]> data, Map<String, Double> activityDurationData) {
      List<String> headerList = new ArrayList(); // Lista para almacenar los encabezados del reporte.
      List<String> valueList = new ArrayList(); // Lista para almacenar los valores correspondientes a cada encabezado.
      Iterator var5 = activityDurationData.keySet().iterator();

      while (var5.hasNext()) { // Itera sobre las claves del mapa activityDurationData.
         String reportVal = (String) var5.next();
         headerList.add(reportVal); // Agrega el nombre de la actividad a la lista de encabezados
         valueList.add(((Double) activityDurationData.get(reportVal)).toString()); // Agrega la duración de la actividad
                                                                                   // (convertida a cadena) a la lista
                                                                                   // de valores.
      }

      String[] titleReport = new String[] { "Process steps total time" };
      data.add(titleReport);
      String[] header = (String[]) headerList.toArray(new String[headerList.size()]); // Convierte la lista de
                                                                                      // encabezados a un arreglo y lo
                                                                                      // agrega a la lista de datos.
      String[] value = (String[]) valueList.toArray(new String[valueList.size()]); // Convierte la lista de valores a un
                                                                                   // arreglo y lo agrega a la lista de
                                                                                   // datos.
      String[] carriageReturn = new String[] { "\n" }; // Agrega una línea en blanco (representada por un salto de
                                                       // línea) para separar este reporte de otros.
      data.add(header);
      data.add(value);
      data.add(carriageReturn);
   }

   /**
    * Agrega un reporte tabular de la duración de actividades a la lista de datos
    * proporcionada.
    *
    * @param data           Lista de arreglos de cadenas donde se agregará el
    *                       reporte.
    * @param searchResponse Respuesta de búsqueda que contiene los datos necesarios
    *                       para el reporte.
    */
   protected void addActivityDurationTableReport(List<String[]> data, SearchResponse searchResponse) {
      // Obtiene los datos de la tabla de duración de actividades a partir de la
      // respuesta de búsqueda.
      // ExtendedStatsAggregate contiene estadísticas extendidas sobre la duración de
      // esa actividad, como el conteo, suma, mínimo, máximo, promedio y desviación
      // estándar.
      Map<String, ExtendedStatsAggregate> activityDurationTableData = this.getActivityDurationTableData(searchResponse);
      // Crea el reporte de la tabla de duración de actividades y lo agrega a la lista
      // de datos.
      this.createActivityDurationTableReport(data, activityDurationTableData);
   }

   /**
    * Crea un reporte detallado de las duraciones de actividades y lo agrega a la
    * lista de datos proporcionada.
    *
    * @param data                      Lista de arreglos de cadenas donde se
    *                                  agregará el reporte.
    * @param activityDurationTableData Mapa que contiene las estadísticas
    *                                  extendidas de cada actividad.
    */
   protected void createActivityDurationTableReport(List<String[]> data,
         Map<String, ExtendedStatsAggregate> activityDurationTableData) {
      List<String[]> valueDetailList = new ArrayList(); // Lista para almacenar los detalles de cada actividad.
      Iterator var4 = activityDurationTableData.keySet().iterator();

      while (var4.hasNext()) {
         String activityName = (String) var4.next();
         List<String> valueDefDetailList = new ArrayList(); // Lista para almacenar los valores de una fila del reporte.
         ExtendedStatsAggregate stat = (ExtendedStatsAggregate) activityDurationTableData.get(activityName);
         valueDefDetailList.add(activityName);
         valueDefDetailList.add("" + stat.count());
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours(stat.sum()));
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours(stat.min()));
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours(stat.max()));
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours(stat.avg()));
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours(stat.stdDeviation()));
         String[] valueArray = (String[]) valueDefDetailList.toArray(new String[valueDefDetailList.size()]);
         valueDetailList.add(valueArray);
      }

      String[] titleReport = new String[] { "Activity duration details" };
      String[] headerDefDetail = new String[] { "Activity", "Count", "Sum", "Min. duration", "Max. duration", "Average",
            "Standard deviation" };
      String[] carriageReturn = new String[] { "\n" };
      data.add(titleReport);
      data.add(headerDefDetail);
      data.addAll(valueDetailList);
      data.add(carriageReturn);
   }

   /**
    * Agrega un reporte de las instancias de procesos más lentas a la lista de
    * datos proporcionada.
    *
    * @param data           Lista de arreglos de cadenas donde se agregará el
    *                       reporte.
    * @param searchResponse Respuesta de búsqueda que contiene los datos de las
    *                       instancias de procesos.
    */
   protected void addSlowProcessInstancesTableReport(List<String[]> data, SearchResponse searchResponse) {
      Map<String, Map<String, Object>> slowProcessInstancesTableData = this
            .getSlowProcessInstancesTableData(searchResponse);
      this.createSlowProcessInstancesTableReport(data, slowProcessInstancesTableData);
   }

   /**
    * Crea un informe detallado de las instancias de procesos más lentas y lo
    * agrega a la lista de datos proporcionada.
    *
    * @param data                          Lista de arreglos de cadenas donde se
    *                                      agregará el informe.
    * @param slowProcessInstancesTableData Mapa que contiene los datos de las
    *                                      instancias de procesos más lentas.
    */
   protected void createSlowProcessInstancesTableReport(List<String[]> data,
         Map<String, Map<String, Object>> slowProcessInstancesTableData) {
      List<String[]> valueDetailList = new ArrayList();
      Iterator var4 = slowProcessInstancesTableData.keySet().iterator();

      while (var4.hasNext()) {
         String reportVal = (String) var4.next();

         // Lista para almacenar los valores de una fila del informe.
         List<String> valueDefDetailList = new ArrayList();
         Map<String, Object> source = (Map) slowProcessInstancesTableData.get(reportVal);
         valueDefDetailList.add("" + ReportingDataUtil.convertToHours((Number) source.get("duration")));
         valueDefDetailList.add("" + (String) source.get("id"));
         String businessKey = "";
         if (source.get("businessKey") != null) {
            businessKey = "" + source.get("businessKey");
         }

         valueDefDetailList.add(businessKey);
         String[] valueArray = (String[]) valueDefDetailList.toArray(new String[valueDefDetailList.size()]);
         valueDetailList.add(valueArray);
      }

      String[] titleReport = new String[] { "Slowest process instances" };
      String[] headerDefDetail = new String[] { "Duration", "Internal Id", "Business Key" };
      String[] carriageReturn = new String[] { "\n" };
      data.add(titleReport);
      data.add(headerDefDetail);
      data.addAll(valueDetailList);
      data.add(carriageReturn);
   }

   /**
    * Ejecuta una consulta para obtener la duración de instancias de procesos
    * basada en los parámetros proporcionados.
    *
    * @param analyticsClient Cliente de analítica para ejecutar la consulta.
    * @param indexManager    Administrador de índices para gestionar los índices de
    *                        búsqueda.
    * @param currentUser     Usuario actual que realiza la consulta.
    * @param parameterMap    Mapa de parámetros que incluye 'status',
    *                        'processDefinitionId', 'slowProcessInstanceInteger' y
    *                        'dateRange'.
    * @return Respuesta de búsqueda con los resultados de la consulta.
    */
   protected SearchResponse getExecuteProcessInstanceDurationQuery(AnalyticsClient analyticsClient,
         ReportingIndexManager indexManager, User currentUser, Map<String, Object> parameterMap) {
      String status = (String) parameterMap.get("status");
      String processDefinitionId = (String) parameterMap.get("processDefinitionId");
      Integer nrOfSlowProcessInstancesToDisplay = (Integer) parameterMap.get("slowProcessInstanceInteger");
      Date startOfStartDate = this.getStartDate(parameterMap);
      Date endOfEndDate = this.getEndDate(parameterMap);
      return this.executeProcessInstanceDurationQuery(analyticsClient, indexManager, currentUser, processDefinitionId,
            startOfStartDate, endOfEndDate, nrOfSlowProcessInstancesToDisplay, status);
   }

   /**
    * Ejecuta una consulta para obtener la duración de actividades basada en los
    * parámetros proporcionados.
    *
    * @param analyticsClient Cliente de analítica para ejecutar la consulta.
    * @param indexManager    Administrador de índices para gestionar los índices de
    *                        búsqueda.
    * @param currentUser     Usuario actual que realiza la consulta.
    * @param parameterMap    Mapa de parámetros que incluye 'status',
    *                        'processDefinitionId' y 'dateRange'.
    * @return Respuesta de búsqueda con los resultados de la consulta.
    */
   protected SearchResponse getExecuteActivityDurationQuery(AnalyticsClient analyticsClient,
         ReportingIndexManager indexManager, User currentUser, Map<String, Object> parameterMap) {
      String status = (String) parameterMap.get("status");
      String processDefinitionId = (String) parameterMap.get("processDefinitionId");
      Date startOfStartDate = this.getStartDate(parameterMap);
      Date endOfEndDate = this.getEndDate(parameterMap);
      return this.executeActivityDurationQuery(analyticsClient, indexManager, currentUser, processDefinitionId,
            startOfStartDate, endOfEndDate, status);
   }

   /**
    * Obtiene la fecha de inicio del rango proporcionado en el mapa de parámetros.
    *
    * @param parameterMap Mapa de parámetros que incluye 'dateRange' con
    *                     'startDate'.
    * @return Fecha de inicio ajustada al comienzo del día.
    */
   protected Date getStartDate(Map<String, Object> parameterMap) {
      Map<String, String> dateRange = (Map) parameterMap.get("dateRange");
      Date startDate = ISO8601Utils.parse((String) dateRange.get("startDate"));
      return ReportingDataUtil.getStartOfDay(startDate);
   }

   /**
    * Obtiene la fecha de finalización del rango proporcionado en el mapa de
    * parámetros.
    *
    * @param parameterMap Mapa de parámetros que incluye 'dateRange' con 'endDate'.
    * @return Fecha de finalización ajustada al final del día.
    */
   protected Date getEndDate(Map<String, Object> parameterMap) {
      Map<String, String> dateRange = (Map) parameterMap.get("dateRange");
      Date endDate = ISO8601Utils.parse((String) dateRange.get("endDate"));
      return ReportingDataUtil.getEndOfDay(endDate);
   }
}

```