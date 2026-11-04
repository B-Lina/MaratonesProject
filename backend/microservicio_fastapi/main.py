from fastapi import FastAPI, HTTPException, Header, Depends
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import math
from typing import Optional

# Inicialización de Firebase y Firestore
# Asegúrate de que 'serviceAccountKey.json' esté en la misma carpeta
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

#def verify_firebase_token(authorization: Optional[str] = Header(None)):
 #   if not authorization or not authorization.startswith("Bearer "):
  #      raise HTTPException(status_code=401, detail="Token OAuth 2.0 requerido")
   # token = authorization.split("Bearer ")[1]
    #try:
     #   decoded_token = auth.verify_id_token(token)
      #  return decoded_token['uid']
    # except Exception as e:
     #   raise HTTPException(status_code=403, detail="Token inválido o expirado")

def verify_firebase_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token OAuth 2.0 requerido")
    
    token = authorization.split("Bearer ")[1]
    try:
        # Decodifica y verifica la firma del token emitido por Firebase
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Token inválido o expirado: {str(e)}")

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.post("/api/routes/optimize")
def optimizar_ruta(lat_origen: float, lon_origen: float, uid: str = Depends(verify_firebase_token)):
    try:
        with open('veredas.json', 'r', encoding='utf-8') as f:
            veredas = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Datos de veredas no encontrados")

    # 1. Priorización: Score combinado de vulnerabilidad y cercanía
    for v in veredas:
        dist = calcular_distancia(lat_origen, lon_origen, v['lat'], v['lon'])
        v['score'] = v['vulnerabilidad'] / (dist + 1) # +1 evita división por cero

    # Filtrar las 5 con mayor prioridad
    top_5 = sorted(veredas, key=lambda x: x['score'], reverse=True)[:5]

    # 2. Heurística: Vecino más cercano para armar la ruta óptima
    ruta_final = []
    nodo_actual = {"lat": lat_origen, "lon": lon_origen}
    pendientes = top_5.copy()
    distancia_total = 0.0

    while pendientes:
        siguiente = min(pendientes, key=lambda v: calcular_distancia(nodo_actual['lat'], nodo_actual['lon'], v['lat'], v['lon']))
        dist = calcular_distancia(nodo_actual['lat'], nodo_actual['lon'], siguiente['lat'], siguiente['lon'])
        
        distancia_total += dist
        ruta_final.append({
            "id": siguiente['id'],
            "nombre": siguiente['nombre'],
            "vulnerabilidad": siguiente['vulnerabilidad'],
            "distancia_tramo_km": round(dist, 2)
        })
        
        nodo_actual = siguiente
        pendientes.remove(siguiente)

    resultado = {
        "ruta": ruta_final,
        "distancia_total_km": round(distancia_total, 2)
    }

    # 3. Registro de auditoría en Firestore
    try:
        auditoria_ref = db.collection('auditoria')
        auditoria_ref.add({
            "usuario_uid": uid,
            "parametros": {"lat_origen": lat_origen, "lon_origen": lon_origen},
            "resultado": resultado,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Error guardando auditoría: {e}")
        # Decidimos no bloquear la respuesta si falla el log, pero lo registramos en consola

    return resultado