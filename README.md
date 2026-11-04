# Documentación Técnica de Arquitectura e Implementación

**Proyecto:** Sistema de Optimización de Rutas de Salud Rural Dispersa  
**Documento:** Especificación Técnica de Arquitectura, Integración y Consideraciones Éticas  
**Versión:** 1.0.0  
**Estado:** Evaluación Maratón de Programación  

---

## 1. Resumen Ejecutivo

El presente documento detalla la arquitectura de software, la especificación técnica y las consideraciones éticas del **Sistema de Optimización de Rutas de Salud Rural Dispersa**. La solución aborda la problemática logística del personal de salud en zonas de difícil acceso, optimizando la atención diaria mediante la selección y ordenamiento de 5 veredas prioritarias a partir de un dataset base de 10 a 15 veredas.

El sistema utiliza una arquitectura orientada a servicios (SOA) modular y desacoplada, compuesta por un **Microservicio Heurístico en FastAPI**, un **Orquestador Backend en Django REST Framework**, un **Frontend Web Interactivo** y mecanismos de seguridad basados en **OAuth 2.0 (Firebase)** con trazabilidad continua en **Google Cloud Firestore**.

---

## 2. Arquitectura de Software

El sistema sigue una topología desacoplada en tres capas principales para garantizar escalabilidad, mantenibilidad y separación estricta de responsabilidades:

```text
[ Frontend Web (HTML5 / JS / Tailwind) ] 
                   │
                   │ (Peticiones HTTPS + Bearer Token OAuth 2.0)
                   ▼
 [ Orquestador Backend (Django REST Framework) ]
                   │
                   │ (Comunicación REST Interna HTTP)
                   ▼
  [ Microservicio Heurístico (FastAPI) ] ──► [ Persistencia & Auditoría (Firestore) ]
```

### 2.1 Descripción de Capas

1. **Capa de Presentación (`frontend/`):**
   * Diseñada como una interfaz ligera optimizada para dispositivos móviles de campo.
   * Maneja el ciclo de vida del usuario e integración con Firebase Authentication SDK.
   * Emite peticiones autenticadas enviando tokens JWT mediante el encabezado `Authorization`.

2. **Capa de Orquestación (`backend/orquestador_django/`):**
   * Actúa como API Gateway intermedio.
   * Valida la estructura de los payloads de entrada y gestiona políticas de origen cruzado (**CORS**) con `django-cors-headers`.
   * Enruta la solicitud al microservicio de cálculo y retorna una respuesta consolidada al cliente.

3. **Capa de Cómputo y Persistencia (`backend/microservicio_fastapi/`):**
   * Microservicio de alto rendimiento encargado del cálculo de distancias y scoring de vulnerabilidad.
   * Implementa la validación de firmas JWT en cada solicitud usando `firebase_admin.auth`.
   * Registra los eventos de cálculo de manera inmutable en **Google Cloud Firestore**.

---

## 3. Algoritmo de Optimización Heurística

El motor de optimización selecciona la secuencia de visita para **5 veredas por jornada** minimizando el costo de recorrido global y maximizando la prioridad de atención social.

### 3.1 Modelo Matemático

Para cada vereda no visitada $i$, el algoritmo calcula dinámicamente un **Score de Prioridad ($S_i$)**:

$$S_i = \frac{V_i^\alpha}{d_i^\beta + \epsilon}$$

Donde:
* $V_i \in [0.0, 1.0]$: Índice de Vulnerabilidad Social de la vereda (obtenido del dataset `veredas.json`).
* $d_i$: Distancia en kilómetros desde la posición actual hasta la vereda $i$, calculada mediante la **Fórmula de Haversine**:

$$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$

* $R = 6371.0 \text{ km}$ (Radio medio de la Tierra).
* $\alpha, \beta$: Coeficientes de ponderación para equilibrar la urgencia social y la penalización por distancia física.
* $\epsilon = 10^{-6}$: Valor de regularización para evitar la división por cero.

### 3.2 Estrategia de Selección
El algoritmo aplica una estrategia de **Búsqueda Voraz Ponderada (Weighted Greedy Approach)**. En cada paso, el sistema selecciona la vereda con el score $S_i$ más alto, actualiza las coordenadas de origen a dicha vereda y repite el proceso iterativamente hasta completar el cupo de 5 veredas.

---

## 4. Seguridad, OAuth 2.0 y Registro de Auditoría

### 4.1 Autenticación y Autorización (OAuth 2.0)
* **Esquema:** OAuth 2.0 mediante Bearer Tokens JWT.
* **Flujo de Trabajo:**
  1. El cliente autentica al personal médico en Firebase Auth y obtiene el ID Token.
  2. La cabecera HTTP es transmitida: `Authorization: Bearer <FIREBASE_JWT_TOKEN>`.
  3. FastAPI ejecuta `auth.verify_id_token(token)` para confirmar la validez, firma y vigencia antes de procesar el cálculo.

### 4.2 Registro de Auditoría (Trazabilidad)
Cada ejecución exitosa registra un documento en la colección `auditoria` de Firestore con la siguiente estructura:

```json
{
  "timestamp": "2026-11-04T15:30:00Z",
  "usuario_uid": "usr_medico_8f93a02",
  "coordenadas_origen": {
    "latitud": 5.300,
    "longitud": -73.810
  },
  "veredas_seleccionadas": [
    {"id": 1, "nombre": "Vereda Sucuncho"},
    {"id": 2, "nombre": "Vereda Volcán"},
    {"id": 5, "nombre": "Vereda Carrizal"},
    {"id": 8, "nombre": "Vereda El Salitre"},
    {"id": 11, "nombre": "Vereda La Palma"}
  ],
  "distancia_total_km": 14.85
}
```

---

## 5. Especificación de Endpoints API

### 5.1 Endpoint del Orquestador (Django)
* **Ruta:** `/api/orquestador/optimizar/`
* **Método:** `POST`
* **Encabezados:**
  * `Content-Type: application/json`
  * `Authorization: Bearer <TOKEN_OAUTH2>`
* **Cuerpo de la Petición:**
  ```json
  {
    "lat_origen": 5.300,
    "lon_origen": -73.810
  }
  ```
* **Respuesta Exitosa (200 OK):**
  ```json
  {
    "origen": { "latitud": 5.300, "longitud": -73.810 },
    "distancia_total_km": 14.85,
    "ruta": [
      {
        "id": 1,
        "nombre": "Vereda Sucuncho",
        "vulnerabilidad": 0.8,
        "distancia_tramo_km": 0.78
      },
      {
        "id": 2,
        "nombre": "Vereda Volcán",
        "vulnerabilidad": 0.9,
        "distancia_tramo_km": 2.15
      }
    ]
  }
  ```

### 5.2 Endpoint del Microservicio (FastAPI)
* **Ruta:** `/api/routes/optimize`
* **Método:** `POST`
* **Parámetros Query:** `lat_origen` (float), `lon_origen` (float)
* **Encabezados:** `Authorization: Bearer <TOKEN>`
* **Documentación OpenAPI:** `http://127.0.0.1:8000/docs`

---

## 6. Integración Continua (CI/CD)

El repositorio cuenta con un pipeline automatizado configurado mediante **GitHub Actions** en `.github/workflows/ci.yml`.

### Etapas del Pipeline:
1. **Ambiente:** Aprovisionamiento de contenedor Ubuntu con Python 3.10.
2. **Dependencias:** Instalación automatizada desde `requirements.txt` en ambas aplicaciones.
3. **Control de Calidad (Linting):** Evaluación estática de código mediante `flake8` para descartar errores sintácticos o bloqueos en tiempo de ejecución antes de la fusión en la rama principal.

---

## 7. Consideraciones Éticas y Limitaciones del Modelo

### 7.1 Mitigación de Sesgos de Estigmatización Geográfica y Social
* **Uso Estrictamente Operativo:** El Índice de Vulnerabilidad Social se utiliza únicamente como criterio técnico de ponderación logística para priorizar visitas preventivas. No se utiliza para catalogar ni condicionar la calidad del servicio de las comunidades.
* **Privacidad de Datos:** Los índices socioeconómicos no se asocian a identidades de ciudadanos particulares y permanecen protegidos bajo políticas de acceso interno.
* **Prevención de Margiación por Distancia:** Al integrar vulnerabilidad y distancia en el mismo score $S_i$, el modelo evita penalizar de forma indefinida a veredas distantes pero con alto nivel de riesgo social.

### 7.2 Limitaciones del Modelo
1. **Simplificación Geométrica:** El cálculo mediante la Fórmula de Haversine obtiene la distancia en línea recta sobre la esfera terrestre. En entornos reales, las variaciones topográficas, caminos no pavimentados e imponderables climáticos alteran el tiempo real de desplazamiento.
2. **Modelo Human-in-the-Loop:** El algoritmo entrega una **recomendación de ruta priorizada** diseñada como soporte a la toma de decisiones. El equipo médico y los coordinadores de campo mantienen la autoridad final para alterar el orden sugerido ante emergencias en tiempo real.
3. **Dataset Simulado:** El dataset de 10 a 15 veredas constituye una prueba de concepto (PoC). El paso a un entorno de producción requerirá la integración de servicios de matrices de distancia (OpenStreetMap/Google Maps API) y datos demográficos en tiempo real.
