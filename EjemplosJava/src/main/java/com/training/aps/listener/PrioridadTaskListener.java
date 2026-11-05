package com.training.aps.listener;

import java.util.Date;

import org.activiti.engine.delegate.DelegateTask;
import org.activiti.engine.delegate.TaskListener;

/**
 * Task listener por clase, evento create: ajusta la tarea antes de que la vea el usuario.
 * <ul>
 *   <li>Categoría ORO (variable de proceso {@code categoria}): prioridad 100 y vencimiento en 1 día.</li>
 *   <li>Resto: prioridad 50 y vencimiento en 3 días.</li>
 * </ul>
 * También deja la variable LOCAL de la tarea {@code reglaAplicada} (no se ve a nivel de proceso).
 */
public class PrioridadTaskListener implements TaskListener {

    private static final long DIA = 24L * 60 * 60 * 1000;

    @Override
    public void notify(DelegateTask task) {
        boolean oro = "ORO".equals(task.getVariable("categoria"));
        task.setPriority(oro ? 100 : 50);
        task.setDueDate(new Date(System.currentTimeMillis() + (oro ? 1 : 3) * DIA));
        task.setVariableLocal("reglaAplicada", oro ? "urgente" : "normal");
    }
}
