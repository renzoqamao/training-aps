package com.training.aps.listener;

import org.activiti.engine.delegate.DelegateExecution;
import org.activiti.engine.delegate.ExecutionListener;

/**
 * Execution listener por clase ({@code activiti:class}). Se engancha a eventos start/end de procesos y
 * actividades, o take de flujos de secuencia.
 *
 * <p>Registra el evento y la actividad en la variable {@code trazaListener}, acumulando, para ver el orden
 * real en que el motor dispara los eventos.
 *
 * <p>⚠ En el evento end del PROCESO no cree variables nuevas: en PostgreSQL da error de clave foránea
 * ({@code act_fk_var_exe}) porque la ejecución se borra en la misma transacción. Actualizar una existente sí funciona.
 */
public class InicioExecutionListener implements ExecutionListener {

    @Override
    public void notify(DelegateExecution execution) {
        String previo = (String) execution.getVariable("trazaListener");
        // En el start/end del PROCESO no hay actividad actual: getCurrentActivityId() devuelve null
        String actividad = execution.getCurrentActivityId() == null ? "proceso" : execution.getCurrentActivityId();
        String paso = execution.getEventName() + ":" + actividad;
        execution.setVariable("trazaListener", previo == null ? paso : previo + " > " + paso);
    }
}
