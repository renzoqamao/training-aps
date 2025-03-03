# Mensajes y señales

El ``RuntimeService`` se utiliza para informar al motor de procesos que se ha recibido un mensaje o una señal.

## Mensajes

Los mensajes siempre están dirigidos a una instancia de proceso específica (execution).
```
runtimeService.messageEventReceived(messageName, executionId);
runtimeService.messageEventReceived(messageName, executionId, processVariables);
```

## Señales

Las señales son de naturaleza de difusión predeterminada; las recibe todo el motor de procesos. Alfresco Process Services también permite que una señal esté dirigida a una instancia de proceso específica (esta es una extensión que no es de BPMN 2).

```
runtimeService.signalEventReceived(signalName);
runtimeService.signalEventReceived(signalName, processVariables);
runtimeService.signalEventReceived(signalName, executionId);
runtimeService.signalEventReceived(signalName, executionId, processVariables);
```

Las siguientes construcciones BPMN que se pueden incluir en una definición de proceso se activan "informando" al motor de proceso que se han recibido:

- Evento de señal de límite (Boundary Signal Event)
- Evento de mensaje de límite (Boundary Message Event)
- Evento de captura de señal intermedia (Intermediate Signal Catching Event)
- Evento de lanzamiento de señal intermedia (Intermediate Signal Throwing Event)