# myapp/signals.py

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Agenda, Siniestro
from .tasks import send_event_start_notification_agenda
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger('myapp.signals')

@receiver(post_save, sender=Agenda)
def schedule_event_start_notification(sender, instance, created, **kwargs):
    if instance.agenda_type == 'work':
        return

    if created:
        event_start_datetime = datetime.combine(instance.agenda_start_date, instance.agenda_start_time)
        notify_time = event_start_datetime - timedelta(minutes=2)
        current_time = timezone.now()

        delay = (notify_time - current_time).total_seconds()

        logger.info(f"Hora actual: {current_time.isoformat()}, Hora de notificación programada: {notify_time.isoformat()}")

        if delay > 0:
            send_event_start_notification_agenda.apply_async((instance.id,), countdown=delay)
            logger.info(f"Notificación programada para Agenda ID {instance.id} en {delay} segundos.")
        else:
            logger.info(f"El tiempo de notificación para Agenda ID {instance.id} ya ha pasado.")

from .consumers import broadcast_siniestro_update
@receiver(post_save, sender=Siniestro)
def send_siniestro_update(sender, instance, created, **kwargs):
    broadcast_siniestro_update(instance.id)
    logger.info(f"Actualización enviada para siniestro {instance.id}")




# signals.py
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Model

from .middleware import get_current_user
from .models import (
    VehiculoLog,
    Vehiculos,
    Servicio,
    VehiculoPropietario,
    Soat,
    RevisionTecnomecanica,
    TarjetaOperacion,
    PolizaContractual,
    PolizaExtracontractual,
    PolizaTodoRiesgo,
)

OLD_STATE = {}


def _serialize(value):
    if isinstance(value, Model):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return [_serialize(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value


def _to_dict(instance):
    data = {}
    for f in instance._meta.fields:
        val = getattr(instance, f.name)
        data[f.name] = _serialize(getattr(instance, f"{f.name}_id") if f.is_relation else val)
    return data


def _stash_state(model, pk, data):
    OLD_STATE[(model, str(pk))] = data


def _pop_changes(model, pk, new_obj):
    old = OLD_STATE.pop((model, str(pk)), None)
    new = _to_dict(new_obj)
    diff = {}
    if old is None:
        for k, v in new.items():
            diff[k] = {"old": None, "new": v}
    else:
        for k, v in new.items():
            if old.get(k) != v:
                diff[k] = {"old": old.get(k), "new": v}
    # if diff:
    #     print(f"[AUDIT] Cambios detectados en {model} pk={pk}: {diff}")  # <- DEBUG
    return diff or None



def _audit_user():
    return


def _log(vehiculo, modelo, pk, action, changes):
    if action == "updated" and changes is None:
        changes = {"no_changes": "patched without modifications"}
    # VehiculoLog.objects.create(
    #     vehiculo=vehiculo,
    #     modelo_afectado=modelo,
    #     instancia_pk=str(pk),
    #     accion=action,
    #     timestamp=timezone.now(),
    #     cambios=changes,
    #     usuario=_audit_user(),
    # )


def _register_presave(model):
    @receiver(pre_save, sender=model)
    def _presave(sender, instance, **kwargs):
        if instance.pk:
            try:
                _stash_state(
                    model.__name__,
                    instance.pk,
                    _to_dict(sender.objects.get(pk=instance.pk)),
                )
            except sender.DoesNotExist:
                pass

    return _presave


for _mdl in (
    Vehiculos,
    Servicio,
    VehiculoPropietario,
    Soat,
    RevisionTecnomecanica,
    TarjetaOperacion,
    PolizaContractual,
    PolizaExtracontractual,
    PolizaTodoRiesgo,
):
    _register_presave(_mdl)


def _register_posts(model, needs_vehicle=False):
    name = model.__name__

    @receiver(post_save, sender=model)
    def _postsave(sender, instance, created, **kwargs):
        vehiculo = instance.vehiculo if needs_vehicle else instance
        if vehiculo:
            _log(
                vehiculo=vehiculo,
                modelo=name,
                pk=instance.pk,
                action="created" if created else "updated",
                changes=_pop_changes(name, instance.pk, instance),
            )

    @receiver(post_delete, sender=model)
    def _postdelete(sender, instance, **kwargs):
        vehiculo = instance.vehiculo if needs_vehicle else instance
        if vehiculo:
            _log(
                vehiculo=vehiculo,
                modelo=name,
                pk=instance.pk,
                action="deleted",
                changes={
                    k: {"old": v, "new": None} for k, v in _to_dict(instance).items()
                },
            )

    return _postsave, _postdelete


for _mdl, _nv in (
    (Vehiculos, False),
    (Servicio, True),
    (VehiculoPropietario, True),
    (Soat, True),
    (RevisionTecnomecanica, True),
    (TarjetaOperacion, True),
    (PolizaContractual, True),
    (PolizaExtracontractual, True),
    (PolizaTodoRiesgo, True),
):
    _register_posts(_mdl, needs_vehicle=_nv)

# myapp/signals_propietario.py
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Model
from .models import Propietario, PropietarioLog

OLD_STATE_PROP = {}

def _serialize(value):
    from datetime import date, datetime
    from decimal import Decimal
    from uuid import UUID

    if isinstance(value, Model):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return [_serialize(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value

def _to_dict(instance):
    data = {}
    for f in instance._meta.fields:
        val = getattr(instance, f.name)
        data[f.name] = _serialize(
            getattr(instance, f"{f.name}_id") if f.is_relation else val
        )
    return data

@receiver(pre_save, sender=Propietario)
def _pre_save_propietario(sender, instance, **kwargs):
    if instance.pk:
        try:
            OLD_STATE_PROP[str(instance.pk)] = _to_dict(
                sender.objects.get(pk=instance.pk)
            )
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender=Propietario)
def _post_save_propietario(sender, instance, created, **kwargs):
    old = OLD_STATE_PROP.pop(str(instance.pk), None)
    new = _to_dict(instance)
    diff = {}
    if old is None:
        for k, v in new.items():
            diff[k] = {"old": None, "new": v}
    else:
        for k, v in new.items():
            if old.get(k) != v:
                diff[k] = {"old": old.get(k), "new": v}
    PropietarioLog.objects.create(
        propietario=instance,
        modelo_afectado='Propietario',
        instancia_pk=str(instance.pk),
        accion="created" if created else "updated",
        timestamp=timezone.now(),
        cambios=diff or None,
    )

@receiver(post_delete, sender=Propietario)
def _post_delete_propietario(sender, instance, **kwargs):
    old = _to_dict(instance)
    diff = {k: {"old": v, "new": None} for k, v in old.items()}
    PropietarioLog.objects.create(
        propietario=instance,
        modelo_afectado='Propietario',
        instancia_pk=str(instance.pk),
        accion="deleted",
        timestamp=timezone.now(),
        cambios=diff,
    )
