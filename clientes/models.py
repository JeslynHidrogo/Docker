from django.db import models
from config.choices import EstadoGeneral, TipoDocumento

class Cliente(models.Model):
    tipo_doc = models.CharField(max_length=3, choices=TipoDocumento.choices, default=TipoDocumento.DNI)
    nro_doc = models.CharField(max_length=15, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    estado = models.IntegerField(choices=EstadoGeneral.choices, default=EstadoGeneral.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nro_doc} {self.apellidos}, {self.nombres}'

    class Meta:
        db_table = 'clientes' # Nombre real en la BD
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['apellidos', 'nombres']