package com.activiti.extension.bean;

import org.activiti.engine.HistoryService;
import org.activiti.engine.delegate.DelegateExecution;
import org.activiti.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Delegate Expression: un JavaDelegate que además es bean de Spring, así puede recibir servicios con @Autowired.
 * En el Service Task se usa {@code activiti:delegateExpression="${auditoriaDelegate}"}; el motor llama a execute().
 *
 * <p>Cuenta cuántas instancias anteriores existen de la misma definición y lo guarda en {@code instanciasPrevias}.
 * Usar el servicio desde Java no pasa por las listas blancas de expresiones (sólo se resuelve el bean).
 */
@Component("auditoriaDelegate")
public class AuditoriaDelegate implements JavaDelegate {

    @Autowired
    private HistoryService historyService;

    @Override
    public void execute(DelegateExecution execution) {
        // La instancia actual todavía no está guardada en BD en esta transacción, así que no se cuenta.
        long previas = historyService.createHistoricProcessInstanceQuery()
                .processDefinitionId(execution.getProcessDefinitionId())
                .count();
        execution.setVariable("instanciasPrevias", previas);
    }
}
