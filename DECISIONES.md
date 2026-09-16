# Decisiones de la prueba técnica AQR

Este documento distingue acuerdos del usuario y propuestas pendientes. Una propuesta no autoriza su implementación. Se consultarán las decisiones de diseño y arquitectura antes de implementarlas.

## Acuerdos confirmados

| Tema | Acuerdo |
| --- | --- |
| Entrega | 16 de septiembre de 2026 a las 17:00, hora de Colombia. Revisión de código y defensa en vivo. |
| Lenguaje y arquitectura general | Python y LangGraph, con etapas explícitas. Sin interfaz gráfica. |
| Universo | Procesar los 275 radicados y producir una salida por radicado. |
| Alcance temporal | Analizar el expediente completo disponible. Distinguir solicitud, actuaciones y respuestas anteriores. |
| Tipologías | Asignar siempre una de las seis del enunciado. Señalar explícitamente los casos que requieran revisión y las asignaciones forzadas. |
| Causalidad | Tras aclarar el enunciado, el usuario pidió iniciar la implementación. La primera versión interpreta causalidad como motivo específico en texto con evidencia; no implementa el catálogo propuesto de nueve motivos. Causa documentada y duplicidad requieren respaldo separado. |
| Cruces ambiguos | Conservar los candidatos y los conflictos. No elegir una coincidencia arbitraria. |
| Cartas | Borradores. Responder de fondo solo donde haya evidencia y explicitar pendientes. |
| Revisión humana | 60 casos: 20 de desarrollo, 30 de prueba representativa y 10 difíciles. |
| Separación de evaluación | Los 40 de prueba no se utilizarán para ajustar el flujo antes de la evaluación final. Separar clientes y casos casi idénticos entre desarrollo y prueba. |
| Controles | Aplicar controles automáticos a los 275 casos. Los 20 de desarrollo también se procesarán con la versión final. |
| Presupuesto | Máximo USD 3 de consumo de API del proyecto, incluyendo pruebas, reintentos y evaluación. |
| Acceso | El usuario dispone de API OpenAI con saldo/créditos. No se ha proporcionado una clave a este proceso. |
| Comparación | Comparar OpenAI y ejecución local. Hardware actual: 16 GB RAM, gráfica integrada AMD con 512 MB dedicados y hasta 8 GB compartidos. El usuario puede usar otro equipo con Ollama. |
| Orden de proveedores | OpenAI en este equipo primero; comparar Ollama posteriormente sobre casos de desarrollo. |
| Llamadas | Tres llamadas LLM separadas por caso: clasificación, extracción de evidencia y redacción. Cruces y validaciones en Python. |
| Primera revisión | Automatización primero y revisión asistida de los 20 casos de desarrollo: mostrar predicciones y evidencia para que el usuario acepte o corrija explícitamente. Sustituye el acuerdo inicial de revisión ciega de desarrollo. Los 40 finales se etiquetarán sin ver sugerencias del modelo. |
| Selección de desarrollo | Diversa y reproducible, incluyendo solicitudes claras y dificultades de datos. |
| Entorno y persistencia | Entorno virtual aislado; guardar estado, presupuesto y resultados en archivos JSON. No usar SQLite. |
| Envío a OpenAI | El usuario confirma que tratará los datos como ficticios y autoriza enviarlos tal cual. No se aplicará saneamiento adicional. No equivale a una verificación independiente del carácter ficticio de los datos. |
| Bibliotecas directas | openpyxl para leer/generar Excel, Pydantic para validar y SDK oficial OpenAI dentro de LangGraph. |
| Modelo inicial | GPT-5.6 Luna para las tres etapas; comprobar acceso y evaluar antes de la selección definitiva. |

## Preguntas presentadas al usuario

El usuario solicitó comenzar la implementación después de revisar las propuestas y aclarar causalidad. Se construyó una primera versión secuencial con JSON atómico, reserva de coste y como máximo un reintento explícito. Las convenciones y parámetros iniciales se documentan como decisiones de implementación revisables, no como políticas oficiales del banco ni valores validados con evaluación.

## Decisiones pendientes que también se consultarán

- Ajustes de modelo y parámetros después de medir la primera versión.
- Cambios de contratos y convenciones de clasificación a partir de la revisión asistida.
- Posible normalización de causalidades; no imponer un catálogo antes de revisar los casos.
- Método concreto de selección y reserva de la muestra; tratamiento de grupos de clientes y notas similares.
- Rúbrica de revisión, métricas, criterios de aceptación y uso de un modelo evaluador.
- Estructura del Excel final, estilo y fecha de las cartas, formatos de documentación.

Las propuestas concretas se encuentran en PROPUESTA_TECNICA.md. Se pueden aprobar por bloque o modificar individualmente.

## Estado del trabajo

- Completado: lectura del enunciado, análisis de estructura/calidad de datos y revisión exploratoria de contenido potencialmente instructivo.
- Completado: entorno virtual `.venv` con Python 3.12.14 y las bibliotecas directas aprobadas. Versiones fijadas en `requirements.txt` y `requirements.lock.txt`; importaciones y `pip check` correctos.
- Completado: selección dirigida reproducible de 20 radicados de 20 clientes, JSON de revisión y Excel inicial con dos hojas. Veintisiete radicados asociados a esos clientes quedan excluidos de la selección final de prueba. Revisión de similitud pendiente.
- Completado: verificación de notas completas, campos humanos vacíos y revisión visual de ambas hojas del Excel.
- Implementado: flujo LangGraph con tres etapas LLM, contratos Pydantic, proveedor OpenAI, citas verificables, conservación de cruces ambiguos, presupuesto compartido, reanudación y exportación/importación de revisión asistida.
- Verificado sin API: lectura de los 275 expedientes y pruebas automatizadas de flujo, validación, presupuesto, reanudación y revisión humana explícita.
- Pendiente: configurar credencial y ejecutar modelos, revisar los 20, seleccionar los 40 finales, evaluar calidad, comparar Ollama y generar resultados finales de los 275.
- Consumo de API del proyecto por el flujo: USD 0; no se han ejecutado llamadas a modelos del proyecto. Este registro no representa el consumo de la cuenta de ChatGPT/Codex.
- Archivos originales conservados; no se han editado.
- Cambio de orden aprobado: construir y ejecutar el flujo inicial antes de solicitar etiquetas de desarrollo. El Excel inicial se conserva; no hace falta completarlo ahora. Las correcciones asistidas sirven para desarrollo, no como evaluación independiente.

## Límites de interpretación ya detectados

- Las 275 filas de clientes representan 248 identidades. Una unión directa con radicados produciría 345 filas.
- No hay etiquetas de referencia entregadas para clasificación.
- El texto puede contener solicitudes, conclusiones previas e instrucciones operativas: se analiza como evidencia, no como instrucciones para ejecutar acciones.
- Los adjuntos mencionados no están entre los archivos disponibles.
- Ambos Excel conservan metadatos de sensibilidad con la etiqueta «Confidencial histórico». El enunciado describe los datos como dummy; no se ha verificado que toda la información visible sea ficticia.
