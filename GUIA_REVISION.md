# Revisión de los casos de desarrollo

La primera revisión será asistida: el flujo procesará los 20 casos elegidos por diversidad antes de pedir tus etiquetas. Verás sus predicciones y evidencias para aceptarlas o corregirlas. Esta revisión sirve para ajustar el flujo; no permite estimar su precisión general ni constituye una evaluación independiente.

## Cómo revisar cada caso

1. Lee la nota completa del expediente. Las notas largas se mostrarán en fragmentos consecutivos para que Excel no oculte su contenido.
2. Consulta las filas de cliente relacionadas. Si hay varias, no supongas que la primera pertenece al radicado concreto.
3. Contrasta la tipología propuesta con la nota y acepta o corrige explícitamente una de las seis tipologías del enunciado. Si el encaje es débil, deja constancia en la revisión requerida y en tus observaciones.
4. Contrasta la causalidad propuesta: debe describir el motivo específico de la solicitud y estar sustentada en la nota. Corrígela en tus palabras cuando sea necesario. No existe un catálogo oficial de causalidades entre los insumos.
5. Copia el fragmento que respalda tu interpretación. No es necesario copiar toda la nota.
6. Indica si el expediente documenta una causa del problema. Distingue la afirmación del cliente de una actuación o conclusión de investigación. Si no hay evidencia suficiente, escribe «No determinada».
7. Indica qué datos o documentos faltan para responder, y cualquier conflicto que deba revisarse.

Las predicciones se distinguirán de tus respuestas. Una sugerencia sin aceptación explícita no contará como etiqueta humana. Revisa también las afirmaciones del borrador: que una cita exista no demuestra por sí solo que respalde su interpretación. El Excel inicial sin sugerencias se conserva y no hace falta completarlo ahora.

En el nuevo Excel, marca «Aceptar» o «Corregir» en Decisión humana. Si corriges, completa tipología, causalidad y evidencia/justificación. Marca por separado si la investigación y la carta son correctas o requieren cambios, y explica estos últimos en Observaciones. Una fila sin decisión sigue sin revisar. Las instrucciones de exportación e importación están en README.md.

## Tipologías permitidas

- Aclaraciones Cartera Hipotecaria
- Retiros por Pin Pad Cuenta Corriente
- Gravamen a Movimiento AFC
- Requerimiento de Extractos Libranza
- Doblemente Radicado
- No tramitado por falta de información

## Distinciones útiles

- Un dato enmascarado no puede reconstruirse por intuición.
- Que una nota diga «se adjunta» no significa que el archivo adjunto esté disponible.
- Un radicado anterior puede corresponder a una réplica o reenvío, no necesariamente a duplicidad.
- Una actuación previa puede estar documentada en la nota; el nuevo flujo no la ha ejecutado ni verificado en sistemas bancarios.
- Un cliente puede tener más de un crédito o varios casos.

## Evaluación posterior

Después de ajustar con estos 20 casos, se fijarán las reglas, prompts y configuración antes de evaluar 30 casos representativos y 10 difíciles. Esos 40 se etiquetarán sin ver las predicciones del modelo, para reducir el sesgo de aceptar una sugerencia por haberla visto primero. Los grupos se mantendrán separados y se documentarán las limitaciones de la selección.

Los 275 radicados se procesarán con la versión final, incluidos los casos de desarrollo. La clasificación forzada y la revisión requerida seguirán visibles.
