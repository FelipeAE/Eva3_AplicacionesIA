from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ..models import Persona, Funcion, TiempoContrato, Contrato


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def detalle_contrato(request, id):
    """Obtiene detalles completos de un contrato con información relacionada"""
    contrato = get_object_or_404(Contrato, id_contrato=id)
    
    # Helper function to convert to float, handling strings like "No informa"
    def safe_float_convert(value):
        if not value:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None  # Return None for non-numeric strings like "No informa"
        return None

    data = {
        "id_contrato": contrato.id_contrato,
        "honorario_total_bruto": safe_float_convert(contrato.honorario_total_bruto),
        "tipo_pago": contrato.tipo_pago,
        "viaticos": safe_float_convert(contrato.viaticos),
        "observaciones": contrato.observaciones,
        "enlace_funciones": contrato.enlace_funciones,
        
        # Información de la persona
        "persona": {
            "id": contrato.persona.id_persona,
            "nombre_completo": contrato.persona.nombre_completo,
            "rut": contrato.persona.rut if hasattr(contrato.persona, 'rut') else None,
        },
        
        # Información de la función
        "funcion": {
            "id": contrato.funcion.id_funcion,
            "descripcion": contrato.funcion.descripcion_funcion,
            "calificacion_profesional": contrato.funcion.calificacion_profesional,
        },
        
        # Información del tiempo/periodo
        "periodo": {
            "id": contrato.tiempo.id_tiempo,
            "mes": contrato.tiempo.mes,
            "anho": contrato.tiempo.anho,
            "region": contrato.tiempo.region,
        }
    }
    return JsonResponse(data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def detalle_contratos_bulk(request):
    """Obtiene detalles de múltiples contratos en una sola llamada"""
    
    try:
        contract_ids = request.data.get('contract_ids', [])
        
        if not contract_ids or not isinstance(contract_ids, list):
            return JsonResponse({"error": "Se requiere una lista de IDs de contratos"}, status=400)
        
        # Limitar a máximo 50 contratos por seguridad
        if len(contract_ids) > 50:
            return JsonResponse({"error": "Máximo 50 contratos por consulta"}, status=400)
        
        contratos = Contrato.objects.filter(
            id_contrato__in=contract_ids
        ).select_related('persona', 'funcion', 'tiempo')
        
        contracts_data = []
        for contrato in contratos:
            try:
                # Handle viaticos - could be string or number
                viaticos_value = None
                if contrato.viaticos and contrato.viaticos != "No informa":
                    try:
                        viaticos_value = float(contrato.viaticos)
                    except (ValueError, TypeError):
                        viaticos_value = contrato.viaticos  # Keep as string if can't convert
                
                contract_data = {
                    "id_contrato": contrato.id_contrato,
                    "honorario_total_bruto": float(contrato.honorario_total_bruto) if contrato.honorario_total_bruto else None,
                    "tipo_pago": contrato.tipo_pago or "",
                    "viaticos": viaticos_value,
                    "observaciones": contrato.observaciones or "",
                    "enlace_funciones": contrato.enlace_funciones or "",
                    "persona": {
                        "id": contrato.persona.id_persona if contrato.persona else None,
                        "nombre_completo": contrato.persona.nombre_completo if contrato.persona else "N/A",
                        "rut": getattr(contrato.persona, 'rut', None) if contrato.persona else None,
                    },
                    "funcion": {
                        "id": contrato.funcion.id_funcion if contrato.funcion else None,
                        "descripcion": contrato.funcion.descripcion_funcion if contrato.funcion else "N/A",
                        "calificacion_profesional": getattr(contrato.funcion, 'calificacion_profesional', None) if contrato.funcion else None,
                    },
                    "periodo": {
                        "id": contrato.tiempo.id_tiempo if contrato.tiempo else None,
                        "mes": contrato.tiempo.mes if contrato.tiempo else "N/A",
                        "anho": contrato.tiempo.anho if contrato.tiempo else None,
                        "region": getattr(contrato.tiempo, 'region', None) if contrato.tiempo else None,
                    }
                }
            except Exception as field_error:
                print(f"Error processing contract {contrato.id_contrato}: {field_error}")
                continue
            contracts_data.append(contract_data)
        
        return JsonResponse({"contracts": contracts_data})
        
    except Exception as e:
        import traceback
        print(f"Error in detalle_contratos_bulk: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def detalle_generico(request, tipo, id):
    # Normalizar tipo (e.g., id_personas → persona)
    tipo_normalizado = tipo.replace("id_", "").rstrip("s")

    modelos = {
        "persona": Persona,
        "funcion": Funcion,
        "tiempo": TiempoContrato,
        "contrato": Contrato,
    }

    if tipo_normalizado not in modelos:
        return JsonResponse({"error": "Tipo no reconocido"}, status=400)

    modelo = modelos[tipo_normalizado]
    obj = get_object_or_404(modelo, pk=id)
    data = model_to_dict(obj)

    # Relaciones legibles si es contrato
    if tipo_normalizado == "contrato":
        data["persona"] = obj.persona.nombre_completo
        data["funcion"] = obj.funcion.descripcion_funcion
        data["tiempo"] = f"{obj.tiempo.mes} {obj.tiempo.anho}"

    return JsonResponse(data)