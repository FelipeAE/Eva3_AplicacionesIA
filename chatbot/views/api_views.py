from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.forms.models import model_to_dict

from ..models import Persona, Funcion, TiempoContrato, Contrato


@login_required
def detalle_contrato(request, id):
    contrato = get_object_or_404(Contrato, id_contrato=id)
    data = {
        "id": contrato.id_contrato,
        "honorario_total_bruto": contrato.honorario_total_bruto,
        "tipo_pago": contrato.tipo_pago,
        "viaticos": contrato.viaticos,
        "observaciones": contrato.observaciones,
        "enlace_funciones": contrato.enlace_funciones,
        "persona": contrato.persona.nombre_completo,
        "funcion": contrato.funcion.descripcion_funcion,
        "calificacion": contrato.funcion.calificacion_profesional,
        "mes": contrato.tiempo.mes,
        "anho": contrato.tiempo.anho,
        "region": contrato.tiempo.region,
    }
    return JsonResponse(data)


@login_required
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