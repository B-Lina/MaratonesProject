# Optimización de Rutas de Salud en Zonas Rurales

## Consideraciones Éticas y Sesgos del Algoritmo
El uso de algoritmos para priorizar atención en salud rural presenta riesgos de sesgo sistemático. Al utilizar una heurística que evalúa distancia y vulnerabilidad, existe el peligro de marginar a comunidades extremadamente aisladas (penalizadas por su lejanía geográfica) frente a veredas con vulnerabilidad similar pero más cercanas al centro de salud.

Para mitigar este sesgo, el modelo matemático implementado balancea la puntuación protegiendo el peso de la vulnerabilidad y aplicando una compensación en la distancia. 

**Limitaciones del Modelo:**
Este microservicio está diseñado como una herramienta de soporte a la decisión clínica (arquitectura *Human-in-the-loop*). No reemplaza el criterio humano. Los datos espaciales calculan distancias lineales o rutas ideales, lo cual en la ruralidad dispersa de Cundinamarca puede variar por el estado del clima y las vías, haciendo obligatoria la auditoría humana final.