package com.activiti.extension.bean;

import org.springframework.stereotype.Component;

/**
 * Bean de Spring usado desde una EXPRESIÓN: {@code ${clienteService.categoria(total)}}.
 *
 * <p>Al estar en el paquete {@code com.activiti.extension.bean}, APS lo detecta en el arranque (component scan)
 * y lo trata como permitido: probado con {@code beans.whitelisting.enabled=true} y {@code el.whitelisting.enabled=true}
 * sin añadir nada a {@code beans-whitelist.conf} ni a {@code call-whitelist.conf}. Un bean de APS (p. ej.
 * {@code historyService}) en cambio necesita ambas listas.
 */
@Component("clienteService")
public class ClienteService {

    /** Clasifica el pedido por monto. El valor devuelto se guarda con activiti:resultVariable. */
    public String categoria(Number total) {
        double t = total.doubleValue();
        return t >= 1000 ? "ORO" : t >= 300 ? "PLATA" : "BRONCE";
    }
}
