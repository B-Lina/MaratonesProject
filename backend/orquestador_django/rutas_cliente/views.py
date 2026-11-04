import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def solicitar_optimizacion(request):
    # Coordenadas enviadas desde el frontend
    lat = request.data.get('lat_origen')
    lon = request.data.get('lon_origen')

    if lat is None or lon is None:
        return Response({"error": "Faltan coordenadas de origen (lat_origen, lon_origen)"}, status=400)

    # Reenviar el token de autorización enviado desde el frontend (OAuth 2.0 / Firebase)
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', 'Bearer token_simulado_123')

    # URL del microservicio FastAPI
    fastapi_url = f"http://127.0.0.1:8000/api/routes/optimize?lat_origen={lat}&lon_origen={lon}"
    
    try:
        headers = {"Authorization": auth_header}
        respuesta_microservicio = requests.post(fastapi_url, headers=headers)
        
        if respuesta_microservicio.status_code == 200:
            return Response(respuesta_microservicio.json(), status=200)
        else:
            return Response(
                respuesta_microservicio.json() if respuesta_microservicio.content else {"error": "Fallo en el microservicio"}, 
                status=respuesta_microservicio.status_code
            )
            
    except requests.exceptions.ConnectionError:
        return Response({"error": "El microservicio de FastAPI está apagado"}, status=503)