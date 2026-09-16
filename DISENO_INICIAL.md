# Diseño de la primera implementación

El usuario solicitó comenzar la implementación tras aclarar el significado de causalidad. Esta versión concreta el flujo propuesto; sus convenciones y parámetros son hipótesis iniciales para revisar con los 20 casos, no reglas oficiales del banco.

## Clasificación

- Las seis tipologías proceden del enunciado.
- Causalidad significa motivo específico en texto con evidencia. **No se implementó el catálogo de nueve motivos propuesto anteriormente.**
- La causa comprobada es un hallazgo de investigación separado, solo si existe evidencia.
- Duplicidad requiere documentación expresa sobre la misma solicitud. Cliente repetido, otro número o reenvío no bastan.
- Falta de información requiere un estado documentado no superado posteriormente; no equivale a anexos ausentes aquí.
- Si ambos estados son aplicables, el prompt inicial prioriza duplicidad documentada. En otros casos elige la solicitud principal.
- Fuera de catálogo fuerza la categoría más próxima y exige revisión. Sin solicitud identificable usa falta de información como asignación forzada, sin afirmar ese estado real del banco.

La taxonomía mezcla temas y estados; las convenciones anteriores requieren evaluación humana y permanecen editables en los prompts.

## Investigación y respuesta

Tres llamadas separadas. Cruces y validaciones en Python entre etapas. Pydantic define las salidas. Cada fuente conserva archivo, hoja, fila y campo. Se comprueba la existencia literal de las citas.

Investigación recibe todos los candidatos del mismo documento. Los conflictos permanecen visibles y no se selecciona una fila arbitrariamente.

La carta se ensambla desde párrafos que identifican evidencias o pendientes. Una referencia válida no garantiza una interpretación correcta. No hay envíos, firma, fecha de emisión ni operaciones bancarias.

Las notas y respuestas anteriores son datos sin autoridad sobre el flujo. Los nodos no tienen herramientas externas.

## Operación

Ejecución secuencial, JSON atómico, bloqueo del proceso y una contabilidad compartida hasta USD 3. Reserva previa, recibo antes de liquidación y conservación de costes inciertos. Caché por fuentes, configuración, prompts, esquemas, código y versiones.

README.md documenta topes de tokens, reintentos, credenciales y límites de recuperación. Son valores iniciales, no resultados optimizados.

## Revisión y evaluación

Los 20 casos se revisan con sugerencias y aceptación/corrección explícita. Los 40 finales siguen reservados para etiquetado sin sugerencias. Faltan selección final, rúbrica y umbrales.

## Trade-offs

- Tres llamadas permiten localizar errores, con más consumo y latencia que una sola.
- Causalidad libre evita atribuir al banco un catálogo propio; complica agregación y métricas de coincidencia exacta.
- JSON facilita inspección y traslado; requiere bloqueo y ejecución secuencial para coherencia.
- Detener citas inválidas evita propagar errores, pero puede reducir cobertura hasta ajustar prompts.
- La revisión asistida agiliza desarrollo y puede sesgar al revisor; no constituye evaluación independiente.

