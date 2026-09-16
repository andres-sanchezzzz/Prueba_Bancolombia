# Propuestas técnicas pendientes de decisión

Este documento conserva las alternativas discutidas antes de implementar. El estado vigente está en README.md, DECISIONES.md y DISENO_INICIAL.md. Las menciones siguientes a componentes pendientes corresponden a aquella propuesta, no al estado actual del código. El catálogo controlado no se implementó: la primera versión extrae causalidad en texto con evidencia.

## A Entorno y portabilidad

Propuesta: entorno virtual del proyecto con Python 3.12 y dependencias fijadas después de comprobar compatibilidad. Evitar modificar el Python del sistema o el runtime administrado de herramientas.

Ventaja: el proyecto puede reconstruirse en el otro computador con las mismas versiones. Coste: requiere instalar dependencias en cada equipo; no se debe copiar el entorno virtual entre máquinas.

Alternativas: usar Python del sistema o un contenedor. El primero puede mezclar dependencias; el segundo añade instalación y preparación para una entrega cercana.

## B Flujo y contratos

Propuesta de secuencia lógica: validar entrada → clasificar → recuperar candidatos de cliente → extraer evidencia → redactar → validar → exportar.

Cruces, presupuesto y validaciones se ejecutarían en Python. El LLM no dispondría de herramientas para enviar mensajes, ejecutar código o consultar arbitrariamente otros clientes.

Contratos propuestos:

| Salida | Contenido propuesto |
| --- | --- |
| Clasificación | Tipología, motivo principal, solicitudes secundarias, evidencia textual, asignación forzada, revisión requerida y razón. |
| Investigación | Hechos con origen, campos ausentes, candidatos en conflicto, manifestaciones del cliente, actuaciones documentadas, causa sustentada si existe y asuntos pendientes. |
| Respuesta | Borrador y relación entre sus afirmaciones factuales y las evidencias utilizadas. |
| Validación | Errores estructurales, conflictos no resueltos, afirmaciones sin respaldo detectadas y estado técnico del procesamiento. |

Propuesta: contratos Pydantic y salida estructurada del proveedor cuando esté disponible. Un JSON válido no demuestra que sus hechos sean correctos; hacen falta controles separados.

Decisión recibida: tres llamadas separadas por caso, con cruces y validaciones en Python entre las etapas.

## C Estado y presupuesto

Decisión: guardar progreso, presupuesto y resultados en archivos JSON. No utilizar SQLite. Propuesta pendiente: identificar cada ejecución por caso, datos y versiones de configuración/prompts/modelo, con escritura atómica y ejecución secuencial.

Ventaja: archivos fáciles de inspeccionar y trasladar. Coste: implementar el guardado coherente entre estado y presupuesto, controlar ejecuciones simultáneas y no duplicar llamadas al reanudar.

Se puede ejecutar LangGraph sin su checkpoint persistente y controlar explícitamente qué etapas están completas en el estado JSON. El comportamiento concreto de reanudación está pendiente de revisión. Memoria temporal sola no conserva progreso tras cerrar el proceso.

Regla de presupuesto propuesta:

1. Antes de enviar una llamada, calcular una reserva conservadora de entrada y salida máxima, con la tarifa verificada del modelo y el límite de salida configurado.
2. Autorizarla solo si gasto registrado + reservas pendientes + nueva reserva no supera USD 3.
3. Registrar el consumo reportado por el proveedor y ajustar la reserva al finalizar.
4. Si se desconoce si una llamada se facturó, conservar su reserva hasta reconciliar; evitar reintentos invisibles del SDK.
5. Si no hay saldo de presupuesto suficiente, detener nuevas llamadas y conservar resultados, sin inventar respuestas para los casos pendientes.

Este control cubriría el consumo de este proyecto. No puede limitar el gasto de otras aplicaciones que usen la misma cuenta. La contabilidad final se contrastaría con el consumo disponible del proveedor.

Propuesta inicial para simplificar el límite: ejecución secuencial y reintentos explícitos limitados. Número de intentos, modelos y topes de tokens pendientes de aprobación y medición.

## D Datos enviados y registros

Decisión recibida: mantener los originales intactos y enviar las notas tal cual a OpenAI. El usuario confirma que las tratará como datos ficticios según el enunciado. No se aplicará sustitución adicional de nombres, contactos ni identificadores.

La inspección encontró enmascaramiento parcial y datos reconocibles. La decisión anterior corresponde a la autorización del usuario y no a una verificación independiente del carácter ficticio de cada dato.

Propuesta: registros locales y credencial mediante variable de entorno. No incluir secretos en archivos entregables ni habilitar trazas externas automáticamente.

No hay llamadas de datos del proyecto a proveedores realizadas hasta este momento.

## E Muestra y evaluación

Acuerdo: 20 de desarrollo, 30 representativos y 10 difíciles; los 275 casos pasan por el flujo final.

Decisión: selección diversa y reproducible de desarrollo. Propuesta concreta: selección dirigida por condiciones observadas en los archivos, fijada en un manifest con radicados, filas y huellas de fuentes. No presentarla como selección aleatoria ni atribuirle una semilla aleatoria inexistente. Cuidar que clientes y casos casi idénticos no crucen desarrollo y evaluación. Los casos difíciles se identificarían por criterios observables, no por errores descubiertos después de ejecutar el modelo.

Los grupos, tamaños exactos y representatividad pueden entrar en tensión: si hay que ajustar una selección para respetar la separación por cliente, se documentará. Una muestra dirigida o con restricciones no se presentará como aleatoria simple del universo.

Decisión actualizada: automatización primero y revisión asistida de los 20 casos de desarrollo ya seleccionados. Mostrar predicción, evidencia y borrador, y registrar aceptación o corrección explícita sin confundir la predicción con la etiqueta humana. Conservar el Excel inicial sin sobrescribirlo. Los 40 finales se etiquetarán sin ver las sugerencias del modelo, después de fijar el flujo.

Propuesta de métricas: matriz de confusión y macro-F1 con soporte por categoría; extracción por campo; falsos duplicados; afirmaciones sin respaldo; cobertura de solicitudes; fallos de formato y ejecución; latencia y consumo. Casos difíciles y sintéticos se reportarían separadamente de los representativos.

Las etiquetas humanas finales, catálogo, métricas exactas, rúbrica y umbrales siguen pendientes. Un juez LLM sería auxiliar, consumiría parte del mismo presupuesto y tendría que contrastarse con la revisión humana.

## F Comparación de proveedores

Propuesta: mismo subconjunto de 10–12 casos de desarrollo para una comparación pareada entre un modelo local pequeño y un modelo económico de OpenAI. Mismas evidencias y contratos; registrar las diferencias necesarias de configuración y formato entre proveedores.

Candidatos exploratorios citados en la conversación: Qwen3.5 4B cuantizado local y GPT-5.6 Luna por API. No hay selección definitiva ni comprobación de acceso de la cuenta. Las tarifas y disponibilidad se verificarán antes de ejecutar.

La ejecución local debe medirse; 8 GB de memoria gráfica compartida no equivalen a 8 GB de VRAM dedicada. Decisión recibida: comenzar con OpenAI en este equipo y comparar Ollama posteriormente. Cambiar de equipo no es requisito para preparar la solución.

## Referencias consultadas

- [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
- [Persistencia de LangGraph](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Salidas estructuradas de OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Evaluación de aplicaciones LLM](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- [Modelo candidato OpenAI](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- [Modelo candidato local](https://ollama.com/library/qwen3.5:4b)
