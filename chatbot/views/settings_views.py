from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from ..models import TerminoExcluido


@login_required
def excluir_terminos(request):
    if request.method == "POST":
        nuevo = request.POST.get("nuevo_termino", "").strip()
        if nuevo:
            TerminoExcluido.objects.get_or_create(usuario=request.user, palabra=nuevo)
        eliminar = request.POST.getlist("eliminar")
        TerminoExcluido.objects.filter(usuario=request.user, palabra__in=eliminar).delete()
        return redirect('excluir_terminos')

    terminos = TerminoExcluido.objects.filter(usuario=request.user)
    return render(request, 'chatbot/excluir.html', {'terminos': terminos})