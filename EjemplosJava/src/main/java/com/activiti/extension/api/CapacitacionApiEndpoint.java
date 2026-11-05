package com.activiti.extension.api;

import java.util.Map;

import org.activiti.engine.HistoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.activiti.domain.idm.User;
import com.activiti.security.SecurityUtils;

/**
 * Endpoint REST propio dentro de la API pública. Las clases del paquete {@code com.activiti.extension.api}
 * se publican bajo {@code /activiti-app/api/} con la misma seguridad que la API pública (Basic auth).
 *
 * <p>GET /activiti-app/api/enterprise/capacitacion/resumen/{processDefinitionKey}
 * devuelve el usuario que llama y cuántas instancias en curso y terminadas tiene ese proceso.
 */
@RestController
@RequestMapping("/enterprise/capacitacion")
public class CapacitacionApiEndpoint {

    @Autowired
    private HistoryService historyService;

    @GetMapping("/resumen/{key}")
    public Map<String, Object> resumen(@PathVariable("key") String key) {
        User u = SecurityUtils.getCurrentUserObject();
        long abiertas = historyService.createHistoricProcessInstanceQuery().processDefinitionKey(key).unfinished().count();
        long cerradas = historyService.createHistoricProcessInstanceQuery().processDefinitionKey(key).finished().count();
        return Map.of("usuario", u.getEmail(), "proceso", key, "enCurso", abiertas, "terminadas", cerradas);
    }
}
