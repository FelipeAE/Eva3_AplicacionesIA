from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField

class Persona(models.Model):
    id_persona = models.AutoField(primary_key=True)
    nombre_completo = models.TextField()

    class Meta:
        managed = False
        db_table = 'persona'

class Funcion(models.Model):
    id_funcion = models.AutoField(primary_key=True)
    grado_eus = models.IntegerField()
    descripcion_funcion = models.TextField()
    calificacion_profesional = models.TextField()

    class Meta:
        managed = False
        db_table = 'funcion'

class TiempoContrato(models.Model):
    id_tiempo = models.AutoField(primary_key=True)
    anho = models.IntegerField()
    mes = models.TextField()
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField()
    region = models.TextField()

    class Meta:
        managed = False
        db_table = 'tiempo_contrato'

class Contrato(models.Model):
    id_contrato = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, to_field='id_persona', db_column='id_persona', on_delete=models.DO_NOTHING)
    funcion = models.ForeignKey(Funcion, to_field='id_funcion', db_column='id_funcion', on_delete=models.DO_NOTHING)
    tiempo = models.ForeignKey(TiempoContrato, to_field='id_tiempo', db_column='id_tiempo', on_delete=models.DO_NOTHING)
    honorario_total_bruto = models.IntegerField()
    tipo_pago = models.TextField()
    viaticos = models.TextField()
    observaciones = models.TextField()
    enlace_funciones = models.TextField()

    class Meta:
        managed = False
        db_table = 'contrato'

class SesionChat(models.Model):
    id_sesion = models.AutoField(primary_key=True)
    fecha_inicio = models.DateTimeField()
    fecha_termino = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20)
    nombre_sesion = models.TextField()

    class Meta:
        managed = False
        db_table = 'sesion_chat'

class MensajeChat(models.Model):
    id_mensaje = models.AutoField(primary_key=True)
    sesion = models.ForeignKey(SesionChat, to_field='id_sesion', db_column='id_sesion', on_delete=models.DO_NOTHING)
    tipo_emisor = models.CharField(max_length=10)
    contenido = models.TextField()
    fecha = models.DateTimeField()
    metadata = JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'mensaje_chat'

class PreguntaBloqueada(models.Model):
    id = models.AutoField(primary_key=True)
    sesion = models.ForeignKey(SesionChat, to_field='id_sesion', db_column='id_sesion', on_delete=models.DO_NOTHING)
    pregunta = models.TextField()
    razon = models.TextField()
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'preguntas_bloqueadas'
        
class TerminoExcluido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    palabra = models.CharField(max_length=100)

    class Meta:
        db_table = 'terminos_excluidos'
        
class ContextoPrompt(models.Model):
    nombre = models.CharField(max_length=100)
    prompt_sistema = models.TextField()
    activo = models.BooleanField(default=False)

    class Meta:
        db_table = 'contextos_prompt'

    def __str__(self):
        return self.nombre

