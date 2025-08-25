from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages


def registro(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Usuario {username} creado exitosamente.")
            login(request, user)  # Login automático después del registro
            return redirect('chat_home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})