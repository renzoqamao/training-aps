package com.training.aps.delegate;

import org.activiti.engine.delegate.DelegateExecution;
import org.activiti.engine.delegate.Expression;
import org.activiti.engine.delegate.JavaDelegate;

/**
 * Java Delegate clásico: se usa en el Service Task con la propiedad "Class"
 * ({@code activiti:class="com.training.aps.delegate.CalcularTotalDelegate"}).
 *
 * <p>El motor crea UNA instancia por definición de proceso (no es un bean de Spring: no hay @Autowired) y
 * la comparte entre todas las ejecuciones, por eso no se guarda estado en atributos propios.
 *
 * <p>Campos inyectados desde el BPMN (field extensions, "Class fields" en el modeler):
 * <ul>
 *   <li>{@code tasa}: valor fijo o expresión, p. ej. {@code 0.18}</li>
 *   <li>{@code variableSalida}: nombre de la variable donde se guarda el total</li>
 * </ul>
 * Lee la variable de proceso {@code monto} y guarda {@code monto * (1 + tasa)}.
 */
public class CalcularTotalDelegate implements JavaDelegate {

    private Expression tasa;            // el motor los rellena por reflexión (mismo nombre que el field del BPMN)
    private Expression variableSalida;

    @Override
    public void execute(DelegateExecution execution) {
        double monto = ((Number) execution.getVariable("monto")).doubleValue();
        double t = Double.parseDouble(String.valueOf(tasa.getValue(execution)));
        String salida = variableSalida != null ? String.valueOf(variableSalida.getValue(execution)) : "total";
        execution.setVariable(salida, Math.round(monto * (1 + t) * 100) / 100.0);
    }
}
