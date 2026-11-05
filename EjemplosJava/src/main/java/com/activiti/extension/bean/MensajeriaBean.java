package com.activiti.extension.bean;

import org.activiti.engine.RuntimeService;
import org.activiti.engine.runtime.Execution;
import org.activiti.engine.runtime.ProcessInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Envía mensajes y señales desde Java con {@link RuntimeService} (lo mismo que la API REST del motor).
 * Se usa desde un Service Task: {@code ${mensajeriaBean.notificarPago(pedidoId, importe)}}.
 */
@Component("mensajeriaBean")
public class MensajeriaBean {

    @Autowired
    private RuntimeService runtimeService;

    /**
     * Busca la ejecución que espera el mensaje {@code pagoRecibido} en el pedido cuyo business key es
     * {@code pedidoId} y se lo entrega con la variable {@code importe}. Devuelve true si había alguien esperando.
     * Un mensaje va SIEMPRE dirigido a una ejecución concreta.
     *
     * <p>Se busca en dos pasos porque el business key sólo está en la ejecución RAÍZ, mientras que la suscripción
     * al mensaje está en una ejecución HIJA: filtrar por ambos en una misma consulta no devuelve nada (probado).
     */
    public boolean notificarPago(String pedidoId, Number importe) {
        ProcessInstance pi = runtimeService.createProcessInstanceQuery()
                .processInstanceBusinessKey(pedidoId)
                .singleResult();
        if (pi == null) {
            return false;
        }
        Execution ex = runtimeService.createExecutionQuery()
                .processInstanceId(pi.getId())
                .messageEventSubscriptionName("pagoRecibido")
                .singleResult();
        if (ex == null) {
            return false;
        }
        runtimeService.messageEventReceived("pagoRecibido", ex.getId(), Map.of("importe", importe));
        return true;
    }

    /**
     * Difunde una señal a todo el tenant. En APS las definiciones viven en un tenant (tenant_1), por eso se usa
     * la variante con tenantId; sin ella la señal no alcanza a esos procesos.
     */
    public void alertar(String tenantId) {
        runtimeService.signalEventReceivedWithTenantId("alertaGlobal", tenantId);
    }
}
