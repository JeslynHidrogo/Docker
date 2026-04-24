from django.db import models
from config.choices import EstadoGeneral, EstadoEnvio
from clientes.models import Cliente
from rutas.models import Ruta
# Nuevas importaciones de validadores (Pág. 42-43)
from .validators import validar_peso_positivo, validar_codigo_encomienda
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class Empleado(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    estado = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO
    )
    fecha_ingreso = models.DateField()

    def __str__(self):
        return f'{self.codigo} - {self.apellidos}, {self.nombres}'

    class Meta:
        db_table = 'empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['apellidos']

class Encomienda(models.Model):
    # ── Identificación con VALIDATORS (Pág. 42) ──────────
    codigo = models.CharField(
        max_length=20, 
        unique=True,
        validators=[validar_codigo_encomienda]
    )
    descripcion = models.TextField()
    peso_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[
            validar_peso_positivo,
            MinValueValidator(0.01, message='El peso mínimo es 0.01 kg')
        ]
    )
    volumen_cm3 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # ── Relaciones ────────────────────────────────────
    remitente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='envios_como_remitente')
    destinatario = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='envios_como_destinatario')
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT, related_name='encomiendas')
    empleado_registro = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='encomiendas_registradas')

    # ── Estado y fechas ──────────────────────────────
    estado = models.CharField(
        max_length=2,
        choices=EstadoEnvio.choices,
        default=EstadoEnvio.PENDIENTE
    )
    costo_envio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_entrega_est = models.DateField(null=True, blank=True)
    fecha_entrega_real = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.codigo} [{self.get_estado_display()}]'
    
    # --- Métodos de Validación (Pág. 43-45) ---

    def clean(self):
        """
        Validaciones personalizadas que involucran múltiples campos.
        """
        errors = {}

        # 1. Validar que el remitente y destinatario no sean la misma persona (Pág. 43)
        if self.remitente_id and self.destinatario_id:
            if self.remitente_id == self.destinatario_id:
                errors['destinatario'] = ValidationError(
                    'El destinatario no puede ser el mismo que el remitente.'
                )

        # 2. Validar que la fecha estimada no sea en el pasado (Pág. 44)
        if self.fecha_entrega_est:
            if self.fecha_entrega_est < timezone.now().date():
                errors['fecha_entrega_est'] = ValidationError(
                    'La fecha de entrega estimada no puede ser en el pasado.'
                )

        # 3. Validar coherencia de fechas: real no puede ser antes que la estimada (Pág. 44)
        if self.fecha_entrega_est and self.fecha_entrega_real:
            if self.fecha_entrega_real < self.fecha_entrega_est:
                errors['fecha_entrega_real'] = ValidationError(
                    'La fecha de entrega real no puede ser antes de la fecha estimada.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Sobrescribimos el método save para forzar la validación completa (Pág. 45).
        """
        self.full_clean()  # Esto llama a los validators de los campos y al método clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'encomiendas'
        verbose_name = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering = ['-fecha_registro']

class HistorialEstado(models.Model):
    encomienda = models.ForeignKey(Encomienda, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=2, choices=EstadoEnvio.choices)
    estado_nuevo = models.CharField(max_length=2, choices=EstadoEnvio.choices)
    observacion = models.TextField(blank=True, null=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='cambios_estado')
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.encomienda.codigo}: {self.estado_anterior}→{self.estado_nuevo}'

    class Meta:
        db_table = 'historial_estados'
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historiales de Estados'
        ordering = ['-fecha_cambio']