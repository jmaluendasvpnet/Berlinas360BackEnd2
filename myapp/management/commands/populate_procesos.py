import json # Not strictly needed if data is directly in Python
from django.core.management.base import BaseCommand
from django.db import transaction

# Assuming your models are in 'your_app_name.models'
# Replace 'my_app' with the actual name of your Django app where these models are defined
from myapp.models import ProcesoDefinicion, EtapaDefinicion, SubEtapaDefinicion, ActuacionDefinicion

# This is the JavaScript/TypeScript data translated to Python
PROCESOS_DATA = [
    {
      "nombre": 'Declarativo - Responsabilidad Civil Contractual',
      "codigoProceso": 'DRC',
      "etapas": [
        {
          "nombre": 'Recepción Doc/ reporte', "codigoEtapa": 'REC',
          "subEtapas": [
            { "nombre": 'Poder', "codigoSubEtapa": 'POD', "actuaciones": [{ "nombre": 'Elaboración Poder', "codigoActuacion": 'POD', "terminaProceso": False, "estadoResultado": 'Poder Elaborado' }] },
            { "nombre": 'Documentos', "codigoSubEtapa": 'DOC', "actuaciones": [{ "nombre": 'Recepción Documentos Iniciales', "codigoActuacion": 'DOC', "terminaProceso": False, "estadoResultado": 'Documentos Recibidos' }] },
          ]
        },
        {
          "nombre": 'Radicación', "codigoEtapa": 'RAD',
          "subEtapas": [
            { "nombre": 'Juzgado', "codigoSubEtapa": 'JUZ', "actuaciones": [{ "nombre": 'Envío solicitud radicación', "codigoActuacion": 'PTE', "terminaProceso": False, "estadoResultado": 'Solicitud Enviada' }] },
            { "nombre": 'Pretensiones', "codigoSubEtapa": 'PRET', "actuaciones": [{ "nombre": 'Registro Pretensiones', "codigoActuacion": 'PRET', "terminaProceso": False, "estadoResultado": 'Pretensiones Registradas' }] },
            { "nombre": 'Pruebas', "codigoSubEtapa": 'PRU', "actuaciones": [{ "nombre": 'Revisión Pruebas Iniciales', "codigoActuacion": 'REV', "terminaProceso": False, "estadoResultado": 'Pruebas Revisadas' }] },
            { "nombre": 'Inadmisión', "codigoSubEtapa": 'INAD', "actuaciones": [{ "nombre": 'Notificación Inadmisión', "codigoActuacion": 'INAD', "terminaProceso": False, "estadoResultado": 'Inadmitido' }] },
            { "nombre": 'Subsanación', "codigoSubEtapa": 'SUB', "actuaciones": [{ "nombre": 'Elaboración Subsanación', "codigoActuacion": 'DDA', "terminaProceso": False, "estadoResultado": 'Subsanación Elaborada' }] },
            { "nombre": 'Rechazo', "codigoSubEtapa": 'R', "actuaciones": [{ "nombre": 'Notificación Rechazo', "codigoActuacion": 'R', "terminaProceso": True, "estadoResultado": 'Rechazado' }] },
          ]
        },
        {
          "nombre": 'Admite Demanda', "codigoEtapa": 'ADM',
          "subEtapas": [
              { "nombre": 'Admisión', "codigoSubEtapa": 'ADM', "actuaciones": [{ "nombre": 'Auto Admisorio', "codigoActuacion": 'ADM', "terminaProceso": False, "estadoResultado": 'Admitido' }] },
          ]
        },
        {
          "nombre": 'Notificación', "codigoEtapa": 'NOT',
          "subEtapas": [
            { "nombre": 'Notificación L2213/2022 por Email', "codigoSubEtapa": 'L2213', "actuaciones": [{ "nombre": 'Envío Email Notificación', "codigoActuacion": 'L2213', "terminaProceso": False, "estadoResultado": 'Email Enviado' }] },
            { "nombre": 'Citatorio 291', "codigoSubEtapa": '291', "actuaciones": [{ "nombre": 'Envío Citatorio', "codigoActuacion": '291', "terminaProceso": False, "estadoResultado": 'Citatorio Enviado' }] },
            { "nombre": 'Aviso 292', "codigoSubEtapa": '292', "actuaciones": [{ "nombre": 'Envío Aviso', "codigoActuacion": '292', "terminaProceso": False, "estadoResultado": 'Aviso Enviado' }] },
            { "nombre": 'Notificación Personal', "codigoSubEtapa": 'NP', "actuaciones": [{ "nombre": 'Realización Notificación Personal', "codigoActuacion": 'NP', "terminaProceso": False, "estadoResultado": 'Notificado Personalmente' }] },
            { "nombre": 'Conducta Concluyente', "codigoSubEtapa": 'CY', "actuaciones": [{ "nombre": 'Registro Conducta Concluyente', "codigoActuacion": 'CY', "terminaProceso": False, "estadoResultado": 'Conducta Registrada' }] },
            { "nombre": 'Emplazamiento', "codigoSubEtapa": 'EMP', "actuaciones": [{ "nombre": 'Publicación Emplazamiento', "codigoActuacion": 'EMP', "terminaProceso": False, "estadoResultado": 'Emplazado' }] },
            { "nombre": 'Curador', "codigoSubEtapa": 'CU', "actuaciones": [{ "nombre": 'Nombramiento Curador Ad Litem', "codigoActuacion": 'CU', "terminaProceso": False, "estadoResultado": 'Curador Nombrado' }] },
            { "nombre": 'Suspensión del Proceso', "codigoSubEtapa": 'SP', "actuaciones": [{ "nombre": 'Auto Suspende Proceso', "codigoActuacion": 'SP', "terminaProceso": False, "estadoResultado": 'Proceso Suspendido' }] },
          ]
        },
        {
          "nombre": 'Contestación', "codigoEtapa": 'CONT',
          "subEtapas": [
              { "nombre": 'Contestación Demanda', "codigoSubEtapa": 'CONT', "actuaciones": [{ "nombre": 'Recepción Contestación', "codigoActuacion": 'CONT', "terminaProceso": False, "estadoResultado": 'Contestado' }] },
          ]
        },
        {
          "nombre": 'Llamamiento en Garantía', "codigoEtapa": 'LLG',
          "subEtapas": [
              { "nombre": 'Solicitud Llamamiento', "codigoSubEtapa": 'LLG', "actuaciones": [{ "nombre": 'Presentación Solicitud Llamamiento', "codigoActuacion": 'LLG', "terminaProceso": False, "estadoResultado": 'Llamamiento Solicitado' }] },
          ]
        },
        {
          "nombre": 'Audiencia', "codigoEtapa": 'AU',
          "subEtapas": [
              { "nombre": 'Fijación Fecha Audiencia', "codigoSubEtapa": 'AU', "actuaciones": [{ "nombre": 'Auto Fija Fecha', "codigoActuacion": 'AU', "terminaProceso": False, "estadoResultado": 'Audiencia Programada' }] },
              { "nombre": 'Realización Audiencia', "codigoSubEtapa": 'AU_REAL', "actuaciones": [{ "nombre": 'Acta Audiencia', "codigoActuacion": 'AU_REAL', "terminaProceso": False, "estadoResultado": 'Audiencia Realizada' }] },
          ]
        },
        {
          "nombre": 'Sentencia', "codigoEtapa": 'S',
          "subEtapas": [
            { "nombre": 'Conciliación', "codigoSubEtapa": 'CONC', "actuaciones": [{ "nombre": 'Indemnización por Aseguradora/Propietario', "codigoActuacion": 'C', "terminaProceso": True, "estadoResultado": 'Conciliado (Indemnizado)' }] },
            { "nombre": 'Condena', "codigoSubEtapa": 'CONDENA', "actuaciones": [{ "nombre": 'Registro Valores Condena', "codigoActuacion": 'CD', "terminaProceso": False, "estadoResultado": 'Condenado' }] },
            { "nombre": 'Sentencia Segunda Instancia', "codigoSubEtapa": 'S2', "actuaciones": [
                { "nombre": 'Revoca', "codigoActuacion": 'S2_REV', "terminaProceso": True, "estadoResultado": 'Revocado (2da Instancia)' },
                { "nombre": 'Confirma', "codigoActuacion": 'S2_CONF', "terminaProceso": True, "estadoResultado": 'Confirmado (2da Instancia)' },
            ] },
          ]
        },
        {
          "nombre": 'Liquidación de Costas', "codigoEtapa": 'LCO',
          "subEtapas": [
              { "nombre": 'Liquidación', "codigoSubEtapa": 'LCO', "actuaciones": [{ "nombre": 'Aprobación Liquidación Costas', "codigoActuacion": 'LCO', "terminaProceso": False, "estadoResultado": 'Costas Liquidadas' }] },
          ]
        },
        {
          "nombre": 'Ejecutivo', "codigoEtapa": 'EJE',
          "subEtapas": [
              { "nombre": 'Mandamiento de Pago', "codigoSubEtapa": 'EJE', "actuaciones": [{ "nombre": 'Librar Mandamiento de Pago', "codigoActuacion": 'EJE', "terminaProceso": False, "estadoResultado": 'Mandamiento Librado' }] },
          ]
        },
        {
          "nombre": 'Medidas Cautelares', "codigoEtapa": 'MC',
          "subEtapas": [
              { "nombre": 'Solicitud Medida', "codigoSubEtapa": 'MC_SOL', "actuaciones": [{ "nombre": 'Presentar Solicitud', "codigoActuacion": 'MC_SOL', "terminaProceso": False, "estadoResultado": 'Medida Solicitada' }] },
              { "nombre": 'Decreto Medida', "codigoSubEtapa": 'MC_DEC', "actuaciones": [{ "nombre": 'Auto Decreta Medida', "codigoActuacion": 'MC_DEC', "terminaProceso": False, "estadoResultado": 'Medida Decretada' }] },
              { "nombre": 'Práctica Medida', "codigoSubEtapa": 'MC_PRAC', "actuaciones": [{ "nombre": 'Oficio Práctica Medida', "codigoActuacion": 'MC_PRAC', "terminaProceso": False, "estadoResultado": 'Medida Practicada' }] },
          ]
        },
        {
          "nombre": 'Terminación', "codigoEtapa": 'T',
          "subEtapas": [
              { "nombre": 'Terminación Anormal', "codigoSubEtapa": 'T_ANORMAL', "actuaciones": [{ "nombre": 'Auto Terminación Proceso', "codigoActuacion": 'T', "terminaProceso": True, "estadoResultado": 'Terminado Anormalmente' }] },
          ]
        },
      ]
    },
    {
      "nombre": 'Declarativo - Responsabilidad Civil Extracontractual',
      "codigoProceso": 'DRCE',
      "etapas": [
        {
          "nombre": 'Recepción Doc/ reporte', "codigoEtapa": 'REC',
          "subEtapas": [
            { "nombre": 'Poder', "codigoSubEtapa": 'POD', "actuaciones": [{ "nombre": 'Elaboración Poder', "codigoActuacion": 'POD', "terminaProceso": False, "estadoResultado": 'Poder Elaborado' }] },
            { "nombre": 'Documentos', "codigoSubEtapa": 'DOC', "actuaciones": [{ "nombre": 'Recepción Documentos Iniciales', "codigoActuacion": 'DOC', "terminaProceso": False, "estadoResultado": 'Documentos Recibidos' }] },
          ]
        },
        {
          "nombre": 'Radicación', "codigoEtapa": 'RAD',
          "subEtapas": [
            { "nombre": 'Juzgado', "codigoSubEtapa": 'JUZ', "actuaciones": [{ "nombre": 'Envío solicitud radicación', "codigoActuacion": 'PTE', "terminaProceso": False, "estadoResultado": 'Solicitud Enviada' }] },
            { "nombre": 'Pretensiones', "codigoSubEtapa": 'PRET', "actuaciones": [{ "nombre": 'Registro Pretensiones', "codigoActuacion": 'PRET', "terminaProceso": False, "estadoResultado": 'Pretensiones Registradas' }] },
            { "nombre": 'Pruebas', "codigoSubEtapa": 'PRU', "actuaciones": [{ "nombre": 'Revisión Pruebas Iniciales', "codigoActuacion": 'REV', "terminaProceso": False, "estadoResultado": 'Pruebas Revisadas' }] },
          ]
        },
        { "nombre": 'Inadmisión', "codigoEtapa": 'INAD', "subEtapas": [ { "nombre": 'Notificación Inadmisión', "codigoSubEtapa": 'INAD', "actuaciones": [{ "nombre": 'Auto Inadmite', "codigoActuacion": 'INAD', "terminaProceso": False, "estadoResultado": 'Inadmitido' }] } ] },
        { "nombre": 'Subsanación', "codigoEtapa": 'SUB', "subEtapas": [ { "nombre": 'Presentación Subsanación', "codigoSubEtapa": 'SUB', "actuaciones": [{ "nombre": 'Recepción Escrito Subsanación', "codigoActuacion": 'SUB', "terminaProceso": False, "estadoResultado": 'Subsanado' }] } ] },
        { "nombre": 'Rechaza', "codigoEtapa": 'RZ', "subEtapas": [ { "nombre": 'Notificación Rechazo', "codigoSubEtapa": 'RZ', "actuaciones": [{ "nombre": 'Auto Rechaza Demanda', "codigoActuacion": 'RZ', "terminaProceso": True, "estadoResultado": 'Rechazado' }] } ] },
        { "nombre": 'Admite Demanda', "codigoEtapa": 'ADM', "subEtapas": [ { "nombre": 'Admisión', "codigoSubEtapa": 'ADM', "actuaciones": [{ "nombre": 'Auto Admisorio', "codigoActuacion": 'ADM', "terminaProceso": False, "estadoResultado": 'Admitido' }] } ] },
        { "nombre": 'Notificación', "codigoEtapa": 'NOT', "subEtapas": [
            { "nombre": 'Notificación Personal', "codigoSubEtapa": 'NP', "actuaciones": [{ "nombre": 'Realización Notificación Personal', "codigoActuacion": 'NP', "terminaProceso": False, "estadoResultado": 'Notificado Personalmente' }] },
            { "nombre": 'Emplazamiento', "codigoSubEtapa": 'EMP', "actuaciones": [{ "nombre": 'Publicación Emplazamiento', "codigoActuacion": 'EMP', "terminaProceso": False, "estadoResultado": 'Emplazado' }] },
            { "nombre": 'Curador', "codigoSubEtapa": 'CU', "actuaciones": [{ "nombre": 'Nombramiento Curador Ad Litem', "codigoActuacion": 'CU', "terminaProceso": False, "estadoResultado": 'Curador Nombrado' }] },
          ]
        },
        { "nombre": 'Contestación', "codigoEtapa": 'CONT', "subEtapas": [
            { "nombre": 'Recepción Contestación', "codigoSubEtapa": 'CONT', "actuaciones": [{ "nombre": 'Registro Contestación', "codigoActuacion": 'CONT', "terminaProceso": False, "estadoResultado": 'Contestado' }] },
            { "nombre": 'Llamamiento en Garantía', "codigoSubEtapa": 'G', "actuaciones": [{ "nombre": 'Solicitud Llamamiento', "codigoActuacion": 'G', "terminaProceso": False, "estadoResultado": 'Llamamiento Solicitado' }] },
            { "nombre": 'Pruebas de Contestación', "codigoSubEtapa": 'CLL', "actuaciones": [{ "nombre": 'Recepción Pruebas Contestación', "codigoActuacion": 'CLL', "terminaProceso": False, "estadoResultado": 'Pruebas Recibidas (Cont.)' }] },
            { "nombre": 'Contestación Llamamiento', "codigoSubEtapa": 'G_CONT', "actuaciones": [{ "nombre": 'Recepción Contestación Llamamiento', "codigoActuacion": 'G_CONT', "terminaProceso": False, "estadoResultado": 'Llamamiento Contestado' }] },
          ]
        },
        { "nombre": 'Audiencia', "codigoEtapa": 'AU', "subEtapas": [
            { "nombre": 'Fijación Fecha Audiencia', "codigoSubEtapa": 'AU_FIJA', "actuaciones": [{ "nombre": 'Auto Fija Fecha', "codigoActuacion": 'AU_FIJA', "terminaProceso": False, "estadoResultado": 'Audiencia Programada' }] },
            { "nombre": 'Conciliación en Audiencia', "codigoSubEtapa": 'C', "actuaciones": [{ "nombre": 'Registro Acuerdo Conciliatorio', "codigoActuacion": 'C', "terminaProceso": True, "estadoResultado": 'Conciliado en Audiencia' }] },
            { "nombre": 'Realización Audiencia (Instrucción y Juzgamiento)', "codigoSubEtapa": 'AU_REAL', "actuaciones": [{ "nombre": 'Acta Audiencia Completa', "codigoActuacion": 'AU_REAL', "terminaProceso": False, "estadoResultado": 'Audiencia Realizada' }] },
          ]
        },
        { "nombre": 'Sentencia', "codigoEtapa": 'S', "subEtapas": [
            { "nombre": 'Absuelto', "codigoSubEtapa": 'AB', "actuaciones": [{ "nombre": 'Sentencia Absolutoria', "codigoActuacion": 'AB', "terminaProceso": True, "estadoResultado": 'Absuelto' }] },
            { "nombre": 'Condena', "codigoSubEtapa": 'CD', "actuaciones": [{ "nombre": 'Sentencia Condenatoria', "codigoActuacion": 'CD', "terminaProceso": False, "estadoResultado": 'Condenado' }] },
            { "nombre": 'Apelación', "codigoSubEtapa": 'APL', "actuaciones": [{ "nombre": 'Interposición Recurso Apelación', "codigoActuacion": 'APL', "terminaProceso": False, "estadoResultado": 'Apelado' }] },
            { "nombre": 'Sentencia Segunda Instancia', "codigoSubEtapa": 'S2', "actuaciones": [
                { "nombre": 'Sentencia Confirma (2da Instancia)', "codigoActuacion": 'S2_CONF', "terminaProceso": True, "estadoResultado": 'Confirmado (2da Instancia)' },
                { "nombre": 'Sentencia Revoca (2da Instancia)', "codigoActuacion": 'S2_REV', "terminaProceso": True, "estadoResultado": 'Revocado (2da Instancia)' },
              ]
            },
            { "nombre": 'Terminación por Transacción', "codigoSubEtapa": 'TTR', "actuaciones": [{ "nombre": 'Aprobación Transacción', "codigoActuacion": 'TTR', "terminaProceso": True, "estadoResultado": 'Terminado por Transacción' }] },
          ]
        },
        { "nombre": 'Liquidación de Costas', "codigoEtapa": 'LCO', "subEtapas": [ { "nombre": 'Liquidación', "codigoSubEtapa": 'LCO', "actuaciones": [{ "nombre": 'Aprobación Liquidación Costas', "codigoActuacion": 'LCO', "terminaProceso": False, "estadoResultado": 'Costas Liquidadas' }] } ] },
        { "nombre": 'Ejecutivo', "codigoEtapa": 'EJE', "subEtapas": [ { "nombre": 'Mandamiento de Pago', "codigoSubEtapa": 'EJE', "actuaciones": [{ "nombre": 'Librar Mandamiento de Pago', "codigoActuacion": 'EJE', "terminaProceso": False, "estadoResultado": 'Mandamiento Librado' }] } ] },
        { "nombre": 'Medidas Cautelares', "codigoEtapa": 'MC', "subEtapas": [
            { "nombre": 'Solicitud Medida', "codigoSubEtapa": 'MC_SOL', "actuaciones": [{ "nombre": 'Presentar Solicitud', "codigoActuacion": 'MC_SOL', "terminaProceso": False, "estadoResultado": 'Medida Solicitada' }] },
            { "nombre": 'Decreto Medida', "codigoSubEtapa": 'MC_DEC', "actuaciones": [{ "nombre": 'Auto Decreta Medida', "codigoActuacion": 'MC_DEC', "terminaProceso": False, "estadoResultado": 'Medida Decretada' }] },
            { "nombre": 'Práctica Medida', "codigoSubEtapa": 'MC_PRAC', "actuaciones": [{ "nombre": 'Oficio Práctica Medida', "codigoActuacion": 'MC_PRAC', "terminaProceso": False, "estadoResultado": 'Medida Practicada' }] },
          ]
        },
        { "nombre": 'Terminación', "codigoEtapa": 'T', "subEtapas": [
            { "nombre": 'Terminación por Transacción', "codigoSubEtapa": 'TTR', "actuaciones": [{ "nombre": 'Aprobación Transacción', "codigoActuacion": 'TTR', "terminaProceso": True, "estadoResultado": 'Terminado por Transacción' }] },
            { "nombre": 'Terminación por Desistimiento Conjunto', "codigoSubEtapa": 'TDC', "actuaciones": [{ "nombre": 'Aprobación Desistimiento Conjunto', "codigoActuacion": 'TDC', "terminaProceso": True, "estadoResultado": 'Terminado por Desistimiento Conjunto' }] },
            { "nombre": 'Terminación por Desistimiento Tácito', "codigoSubEtapa": 'TDT', "actuaciones": [{ "nombre": 'Declaración Desistimiento Tácito', "codigoActuacion": 'TDT', "terminaProceso": True, "estadoResultado": 'Terminado por Desistimiento Tácito' }] },
            { "nombre": 'Terminación - Absuelto', "codigoSubEtapa": 'TAB', "actuaciones": [{ "nombre": 'Archivo por Absolución', "codigoActuacion": 'TAB', "terminaProceso": True, "estadoResultado": 'Terminado (Absuelto)' }] },
            { "nombre": 'Terminación - Condena', "codigoSubEtapa": 'TC', "actuaciones": [{ "nombre": 'Archivo por Cumplimiento Condena/Pago', "codigoActuacion": 'TC', "terminaProceso": True, "estadoResultado": 'Terminado (Condena Cumplida)' }] },
            { "nombre": 'Valor Indemnización', "codigoSubEtapa": 'VI', "actuaciones": [{ "nombre": 'Registro Pago Indemnización Final', "codigoActuacion": 'VI', "terminaProceso": True, "estadoResultado": 'Indemnización Pagada' }] },
          ]
        },
      ]
    },
    {
      "nombre": 'Demanda Administrativa*',
      "codigoProceso": 'DAD',
      "etapas": [
          { "nombre": 'Recepción Doc/ reporte', "codigoEtapa": 'REC', "subEtapas": [ { "nombre": 'Documentos Iniciales', "codigoSubEtapa": 'REC', "actuaciones": [{ "nombre": 'Recibir Documentos DDA ADM', "codigoActuacion": 'REC', "terminaProceso": False, "estadoResultado": 'Recibido' }] } ] },
          { "nombre": 'Radicación', "codigoEtapa": 'RAD', "subEtapas": [ { "nombre": 'Asignación Juzgado', "codigoSubEtapa": 'RAD', "actuaciones": [{ "nombre": 'Radicar y Asignar', "codigoActuacion": 'RAD', "terminaProceso": False, "estadoResultado": 'Radicado' }] } ] },
          { "nombre": 'Inadmisión', "codigoEtapa": 'INAD', "subEtapas": [ { "nombre": 'Auto Inadmite', "codigoSubEtapa": 'INAD', "actuaciones": [{ "nombre": 'Emitir Auto Inadmisión', "codigoActuacion": 'INAD', "terminaProceso": False, "estadoResultado": 'Inadmitido' }] } ] },
          { "nombre": 'Subsanación', "codigoEtapa": 'SUB', "subEtapas": [ { "nombre": 'Recepción Subsanación', "codigoSubEtapa": 'SUB', "actuaciones": [{ "nombre": 'Recibir Escrito Subsanación', "codigoActuacion": 'SUB', "terminaProceso": False, "estadoResultado": 'Subsanado' }] } ] },
          { "nombre": 'Rechaza', "codigoEtapa": 'RZ', "subEtapas": [ { "nombre": 'Auto Rechaza', "codigoSubEtapa": 'RZ', "actuaciones": [{ "nombre": 'Emitir Auto Rechazo', "codigoActuacion": 'RZ', "terminaProceso": True, "estadoResultado": 'Rechazado' }] } ] },
          { "nombre": 'Admite Demanda', "codigoEtapa": 'ADM', "subEtapas": [ { "nombre": 'Auto Admisorio', "codigoSubEtapa": 'ADM', "actuaciones": [{ "nombre": 'Emitir Auto Admisorio', "codigoActuacion": 'ADM', "terminaProceso": False, "estadoResultado": 'Admitido' }] } ] },
          { "nombre": 'Notificación', "codigoEtapa": 'NOT', "subEtapas": [ { "nombre": 'Notificación Entidad Demandada', "codigoSubEtapa": 'NOT_ENT', "actuaciones": [{ "nombre": 'Oficio Notificación', "codigoActuacion": 'NOT_ENT', "terminaProceso": False, "estadoResultado": 'Entidad Notificada' }] } ] },
          { "nombre": 'Contestación', "codigoEtapa": 'CONT', "subEtapas": [ { "nombre": 'Recepción Contestación', "codigoSubEtapa": 'CONT', "actuaciones": [{ "nombre": 'Recibir Contestación Demanda', "codigoActuacion": 'CONT', "terminaProceso": False, "estadoResultado": 'Contestado' }] } ] },
          { "nombre": 'Audiencia', "codigoEtapa": 'AU', "subEtapas": [
              { "nombre": 'Fijación Fecha Audiencia Inicial', "codigoSubEtapa": 'AU_INI_FIJ', "actuaciones": [{ "nombre": 'Auto Fija Fecha Audiencia Inicial', "codigoActuacion": 'AU_INI_FIJ', "terminaProceso": False, "estadoResultado": 'Aud. Inicial Programada' }] },
              { "nombre": 'Realización Audiencia Inicial', "codigoSubEtapa": 'AU_INI_REAL', "actuaciones": [{ "nombre": 'Acta Audiencia Inicial', "codigoActuacion": 'AU_INI_REAL', "terminaProceso": False, "estadoResultado": 'Aud. Inicial Realizada' }] },
              { "nombre": 'Audiencia de Pruebas', "codigoSubEtapa": 'AU_PRU', "actuaciones": [{ "nombre": 'Realización Audiencia Pruebas', "codigoActuacion": 'AU_PRU', "terminaProceso": False, "estadoResultado": 'Aud. Pruebas Realizada' }] },
              { "nombre": 'Alegatos de Conclusión', "codigoSubEtapa": 'AU_ALE', "actuaciones": [{ "nombre": 'Presentación Alegatos', "codigoActuacion": 'AU_ALE', "terminaProceso": False, "estadoResultado": 'Alegatos Presentados' }] },
            ]
          },
          { "nombre": 'Sentencia Primera Instancia', "codigoEtapa": 'ST1', "subEtapas": [ { "nombre": 'Emisión Sentencia', "codigoSubEtapa": 'ST1', "actuaciones": [{ "nombre": 'Emitir Sentencia 1ra Instancia', "codigoActuacion": 'ST1', "terminaProceso": False, "estadoResultado": 'Sentencia 1ra Instancia' }] } ] },
          { "nombre": 'Liquidación de Costas', "codigoEtapa": 'LCO', "subEtapas": [ { "nombre": 'Liquidación', "codigoSubEtapa": 'LCO', "actuaciones": [{ "nombre": 'Aprobación Liquidación Costas', "codigoActuacion": 'LCO', "terminaProceso": False, "estadoResultado": 'Costas Liquidadas' }] } ] },
          { "nombre": 'Medidas Cautelares', "codigoEtapa": 'MC', "subEtapas": [
              { "nombre": 'Solicitud Medida Cautelar', "codigoSubEtapa": 'MC_SOL', "actuaciones": [{ "nombre": 'Presentar Solicitud MC', "codigoActuacion": 'MC_SOL', "terminaProceso": False, "estadoResultado": 'MC Solicitada' }] },
              { "nombre": 'Decreto Medida Cautelar', "codigoSubEtapa": 'MC_DEC', "actuaciones": [{ "nombre": 'Auto Decreta MC', "codigoActuacion": 'MC_DEC', "terminaProceso": False, "estadoResultado": 'MC Decretada' }] },
            ]
          },
          { "nombre": 'Terminación', "codigoEtapa": 'T', "subEtapas": [ { "nombre": 'Terminación Proceso Administrativo', "codigoSubEtapa": 'T_DAD', "actuaciones": [{ "nombre": 'Auto Archivo Definitivo', "codigoActuacion": 'T_DAD', "terminaProceso": True, "estadoResultado": 'Terminado (DAD)' }] } ] },
        ]
    },
    {
      "nombre": 'Laboral*',
      "codigoProceso": 'LAB',
      "etapas": [
          { "nombre": 'Recepción Doc/ reporte', "codigoEtapa": 'REC', "subEtapas": [ { "nombre": 'Documentos Iniciales', "codigoSubEtapa": 'REC', "actuaciones": [{ "nombre": 'Recibir Documentos Demanda Laboral', "codigoActuacion": 'REC', "terminaProceso": False, "estadoResultado": 'Recibido' }] } ] },
          { "nombre": 'Radicación', "codigoEtapa": 'RAD', "subEtapas": [ { "nombre": 'Asignación Juzgado Laboral', "codigoSubEtapa": 'RAD', "actuaciones": [{ "nombre": 'Radicar y Asignar', "codigoActuacion": 'RAD', "terminaProceso": False, "estadoResultado": 'Radicado' }] } ] },
          { "nombre": 'Inadmisión', "codigoEtapa": 'INAD', "subEtapas": [ { "nombre": 'Auto Inadmite', "codigoSubEtapa": 'INAD', "actuaciones": [{ "nombre": 'Emitir Auto Inadmisión', "codigoActuacion": 'INAD', "terminaProceso": False, "estadoResultado": 'Inadmitido' }] } ] },
          { "nombre": 'Subsanación', "codigoEtapa": 'SUB', "subEtapas": [ { "nombre": 'Recepción Subsanación', "codigoSubEtapa": 'SUB', "actuaciones": [{ "nombre": 'Recibir Escrito Subsanación', "codigoActuacion": 'SUB', "terminaProceso": False, "estadoResultado": 'Subsanado' }] } ] },
          { "nombre": 'Rechaza', "codigoEtapa": 'RZ', "subEtapas": [ { "nombre": 'Auto Rechaza', "codigoSubEtapa": 'RZ', "actuaciones": [{ "nombre": 'Emitir Auto Rechazo', "codigoActuacion": 'RZ', "terminaProceso": True, "estadoResultado": 'Rechazado' }] } ] },
          { "nombre": 'Admite Demanda', "codigoEtapa": 'ADM', "subEtapas": [ { "nombre": 'Auto Admisorio', "codigoSubEtapa": 'ADM', "actuaciones": [{ "nombre": 'Emitir Auto Admisorio', "codigoActuacion": 'ADM', "terminaProceso": False, "estadoResultado": 'Admitido' }] } ] },
          { "nombre": 'Notificación', "codigoEtapa": 'NOT', "subEtapas": [ { "nombre": 'Notificación Demandado', "codigoSubEtapa": 'NOT_DEM', "actuaciones": [{ "nombre": 'Realizar Notificación', "codigoActuacion": 'NOT_DEM', "terminaProceso": False, "estadoResultado": 'Demandado Notificado' }] } ] },
          { "nombre": 'Contestación', "codigoEtapa": 'CONT', "subEtapas": [ { "nombre": 'Recepción Contestación', "codigoSubEtapa": 'CONT', "actuaciones": [{ "nombre": 'Recibir Contestación Demanda', "codigoActuacion": 'CONT', "terminaProceso": False, "estadoResultado": 'Contestado' }] } ] },
          { "nombre": 'Audiencia', "codigoEtapa": 'AU', "subEtapas": [
              { "nombre": 'Fijación Fecha Audiencia Conciliación', "codigoSubEtapa": 'AU_CONC_FIJ', "actuaciones": [{ "nombre": 'Auto Fija Fecha Audiencia', "codigoActuacion": 'AU_CONC_FIJ', "terminaProceso": False, "estadoResultado": 'Aud. Conciliación Programada' }] },
              { "nombre": 'Realización Audiencia Conciliación', "codigoSubEtapa": 'AU_CONC_REAL', "actuaciones": [{ "nombre": 'Acta Audiencia Conciliación', "codigoActuacion": 'AU_CONC_REAL', "terminaProceso": False, "estadoResultado": 'Aud. Conciliación Realizada' }] },
              { "nombre": 'Audiencia Trámite y Juzgamiento', "codigoSubEtapa": 'AU_TRAM_JUZG', "actuaciones": [{ "nombre": 'Realización Audiencia Trámite/Juzgamiento', "codigoActuacion": 'AU_TRAM_JUZG', "terminaProceso": False, "estadoResultado": 'Aud. Trámite/Juzgamiento Realizada' }] },
            ]
          },
          { "nombre": 'Sentencia Primera Instancia', "codigoEtapa": 'ST1', "subEtapas": [ { "nombre": 'Emisión Sentencia', "codigoSubEtapa": 'ST1', "actuaciones": [{ "nombre": 'Emitir Sentencia 1ra Instancia', "codigoActuacion": 'ST1', "terminaProceso": False, "estadoResultado": 'Sentencia 1ra Instancia' }] } ] },
          { "nombre": 'Liquidación de Costas', "codigoEtapa": 'LCO', "subEtapas": [ { "nombre": 'Liquidación', "codigoSubEtapa": 'LCO', "actuaciones": [{ "nombre": 'Aprobación Liquidación Costas', "codigoActuacion": 'LCO', "terminaProceso": False, "estadoResultado": 'Costas Liquidadas' }] } ] },
          { "nombre": 'Ejecutivo', "codigoEtapa": 'EJE', "subEtapas": [ { "nombre": 'Mandamiento de Pago', "codigoSubEtapa": 'EJE', "actuaciones": [{ "nombre": 'Librar Mandamiento de Pago', "codigoActuacion": 'EJE', "terminaProceso": False, "estadoResultado": 'Mandamiento Librado' }] } ] },
          { "nombre": 'Terminación', "codigoEtapa": 'T', "subEtapas": [ { "nombre": 'Terminación Proceso Laboral', "codigoSubEtapa": 'T_LAB', "actuaciones": [{ "nombre": 'Auto Archivo Definitivo', "codigoActuacion": 'T_LAB', "terminaProceso": True, "estadoResultado": 'Terminado (LAB)' }] } ] },
        ]
    },
    {
      "nombre": 'Penal',
      "codigoProceso": 'PEN',
      "etapas": [
          { "nombre": 'Recepción de Documentos/reporte', "codigoEtapa": 'REC', "subEtapas": [
              { "nombre": 'Poder', "codigoSubEtapa": 'POD', "actuaciones": [{ "nombre": 'Recepción Poder', "codigoActuacion": 'POD', "terminaProceso": False, "estadoResultado": 'Poder Recibido' }] },
              { "nombre": 'Documentos Pendientes', "codigoSubEtapa": 'PTE', "actuaciones": [{ "nombre": 'Solicitud Documentos Pendientes', "codigoActuacion": 'PTE', "terminaProceso": False, "estadoResultado": 'Documentos Solicitados' }] },
              { "nombre": 'Aviso Aseguradora', "codigoSubEtapa": 'AVAS', "actuaciones": [{ "nombre": 'Envío Aviso a Aseguradora', "codigoActuacion": 'AVAS', "terminaProceso": False, "estadoResultado": 'Aviso Enviado' }] },
            ]
          },
          { "nombre": 'Indagación', "codigoEtapa": 'IND', "subEtapas": [
              { "nombre": 'Informe de Accidente de Tránsito', "codigoSubEtapa": 'IPAT', "actuaciones": [{ "nombre": 'Recepción IPAT', "codigoActuacion": 'IPAT', "terminaProceso": False, "estadoResultado": 'IPAT Recibido' }] },
              { "nombre": 'Documentos Vehículo', "codigoSubEtapa": 'DVH', "actuaciones": [{ "nombre": 'Recepción Documentos Vehículo', "codigoActuacion": 'DVH', "terminaProceso": False, "estadoResultado": 'Docs. Vehículo Recibidos' }] },
              { "nombre": 'Informe Preliminar de Investigador', "codigoSubEtapa": 'IPI', "actuaciones": [{ "nombre": 'Recepción Informe Investigador', "codigoActuacion": 'IPI', "terminaProceso": False, "estadoResultado": 'Informe Inv. Recibido' }] },
              { "nombre": 'Versión Conductor', "codigoSubEtapa": 'VC', "actuaciones": [{ "nombre": 'Recepción Versión Conductor', "codigoActuacion": 'VC', "terminaProceso": False, "estadoResultado": 'Versión Recibida' }] },
              { "nombre": 'Capacitación Conductor', "codigoSubEtapa": 'CCON', "actuaciones": [{ "nombre": 'Verificación Capacitación', "codigoActuacion": 'CCON', "terminaProceso": False, "estadoResultado": 'Capacitación Verificada' }] },
              { "nombre": 'Mantenimiento Vehículo', "codigoSubEtapa": 'MVH', "actuaciones": [{ "nombre": 'Verificación Mantenimiento', "codigoActuacion": 'MVH', "terminaProceso": False, "estadoResultado": 'Mantenimiento Verificado' }] },
              { "nombre": 'Testigos', "codigoSubEtapa": 'TS', "actuaciones": [{ "nombre": 'Recepción Testimonios', "codigoActuacion": 'TS', "terminaProceso": False, "estadoResultado": 'Testimonios Recibidos' }] },
              { "nombre": 'Víctimas', "codigoSubEtapa": 'VIC', "actuaciones": [{ "nombre": 'Entrevista Víctimas/Familiares', "codigoActuacion": 'VIC', "terminaProceso": False, "estadoResultado": 'Víctimas Entrevistadas' }] },
              { "nombre": 'Extinción de la Acción', "codigoSubEtapa": 'EXAC', "actuaciones": [{ "nombre": 'Declaración Extinción Acción', "codigoActuacion": 'EXAC', "terminaProceso": True, "estadoResultado": 'Acción Extinguida' }] },
              { "nombre": 'Entrega Provisional del Vehículo', "codigoSubEtapa": 'EPVH', "actuaciones": [{ "nombre": 'Auto Entrega Provisional Vehículo', "codigoActuacion": 'EPVH', "terminaProceso": False, "estadoResultado": 'Vehículo Entregado (Prov.)' }] },
              { "nombre": 'Entrega Definitiva del Vehículo', "codigoSubEtapa": 'EDVH', "actuaciones": [{ "nombre": 'Auto Entrega Definitiva Vehículo', "codigoActuacion": 'EDVH', "terminaProceso": True, "estadoResultado": 'Vehículo Entregado (Def.)' }] },
              { "nombre": 'Audiencia Preliminar', "codigoSubEtapa": 'APR', "actuaciones": [{ "nombre": 'Realización Audiencia Preliminar', "codigoActuacion": 'APR', "terminaProceso": False, "estadoResultado": 'Audiencia Preliminar Realizada' }] },
              { "nombre": 'Material Probatorio Defensa', "codigoSubEtapa": 'MPD', "actuaciones": [{ "nombre": 'Recepción Material Probatorio Defensa', "codigoActuacion": 'MPD', "terminaProceso": False, "estadoResultado": 'Pruebas Defensa Recibidas' }] },
            ]
          },
          { "nombre": 'Investigación', "codigoEtapa": 'INV', "subEtapas": [
              { "nombre": 'Audiencia Formulación de Imputación', "codigoSubEtapa": 'AFI', "actuaciones": [{ "nombre": 'Realización Audiencia Imputación', "codigoActuacion": 'AFI', "terminaProceso": False, "estadoResultado": 'Imputado' }] },
              { "nombre": 'Audiencia Preclusión', "codigoSubEtapa": 'AP', "actuaciones": [{ "nombre": 'Solicitud/Decisión Preclusión', "codigoActuacion": 'AP', "terminaProceso": True, "estadoResultado": 'Precluido' }] },
            ]
          },
          { "nombre": 'Juzgamiento', "codigoEtapa": 'JZ', "subEtapas": [
              { "nombre": 'Formulación de Acusación', "codigoSubEtapa": 'FA', "actuaciones": [{ "nombre": 'Presentación Escrito Acusación', "codigoActuacion": 'FA_ESC', "terminaProceso": False, "estadoResultado": 'Acusación Presentada' }, { "nombre": 'Audiencia Formulación Acusación', "codigoActuacion": 'FA_AUD', "terminaProceso": False, "estadoResultado": 'Acusado Formalmente' }] },
              { "nombre": 'Material Probatorio Acusación', "codigoSubEtapa": 'MPA', "actuaciones": [{ "nombre": 'Descubrimiento Probatorio', "codigoActuacion": 'MPA', "terminaProceso": False, "estadoResultado": 'Pruebas Acusación Descubiertas' }] },
              { "nombre": 'Audiencia Preparatoria', "codigoSubEtapa": 'APRE', "actuaciones": [{ "nombre": 'Realización Audiencia Preparatoria', "codigoActuacion": 'APRE', "terminaProceso": False, "estadoResultado": 'Audiencia Preparatoria Realizada' }] },
              { "nombre": 'Audiencia Juicio Oral', "codigoSubEtapa": 'JO', "actuaciones": [{ "nombre": 'Instalación Juicio Oral', "codigoActuacion": 'JO_INI', "terminaProceso": False, "estadoResultado": 'Juicio Oral Iniciado' }, { "nombre": 'Práctica Pruebas Juicio', "codigoActuacion": 'JO_PRU', "terminaProceso": False, "estadoResultado": 'Pruebas Practicadas' }, { "nombre": 'Alegatos Finales Juicio', "codigoActuacion": 'JO_ALE', "terminaProceso": False, "estadoResultado": 'Alegatos Presentados' }] },
            ]
          },
          { "nombre": 'Sentencia Primera Instancia', "codigoEtapa": 'ST1', "subEtapas": [
              { "nombre": 'Sentido del Fallo', "codigoSubEtapa": 'SF', "actuaciones": [{ "nombre": 'Anuncio Sentido del Fallo', "codigoActuacion": 'SF', "terminaProceso": False, "estadoResultado": 'Sentido del Fallo Anunciado' }] },
              { "nombre": 'Lectura de Fallo', "codigoSubEtapa": 'LF', "actuaciones": [{ "nombre": 'Lectura Sentencia 1ra Instancia', "codigoActuacion": 'LF', "terminaProceso": False, "estadoResultado": 'Sentencia 1ra Instancia Leída' }] },
            ]
          },
          { "nombre": 'Incidente Reparación', "codigoEtapa": 'IR', "subEtapas": [
              { "nombre": 'Pretensiones', "codigoSubEtapa": 'PRT', "actuaciones": [{ "nombre": 'Solicitud Apertura Incidente', "codigoActuacion": 'PRT', "terminaProceso": False, "estadoResultado": 'Incidente Solicitado' }] },
              { "nombre": 'Pruebas', "codigoSubEtapa": 'PRU', "actuaciones": [{ "nombre": 'Práctica Pruebas Incidente', "codigoActuacion": 'PRU', "terminaProceso": False, "estadoResultado": 'Pruebas Incidente Practicadas' }] },
              { "nombre": 'Fallo', "codigoSubEtapa": 'FL', "actuaciones": [{ "nombre": 'Decisión Incidente Reparación', "codigoActuacion": 'FL', "terminaProceso": True, "estadoResultado": 'Incidente Decidido' }] },
            ]
          },
          { "nombre": 'Terminación', "codigoEtapa": 'T', "subEtapas": [
              { "nombre": 'Terminación por Transacción', "codigoSubEtapa": 'TTR', "actuaciones": [{ "nombre": 'Aprobación Transacción Penal', "codigoActuacion": 'TTR', "terminaProceso": True, "estadoResultado": 'Terminado por Transacción' }] },
              { "nombre": 'Terminación - Absuelto', "codigoSubEtapa": 'TAB', "actuaciones": [{ "nombre": 'Archivo por Absolución Firme', "codigoActuacion": 'TAB', "terminaProceso": True, "estadoResultado": 'Terminado (Absuelto)' }] },
              { "nombre": 'Terminación - Condena', "codigoSubEtapa": 'TC', "actuaciones": [{ "nombre": 'Archivo por Cumplimiento Pena', "codigoActuacion": 'TC', "terminaProceso": True, "estadoResultado": 'Terminado (Condena Cumplida)' }] },
              { "nombre": 'Valor Indemnización', "codigoSubEtapa": 'VI', "actuaciones": [{ "nombre": 'Registro Pago Indemnización (Penal)', "codigoActuacion": 'VI', "terminaProceso": True, "estadoResultado": 'Indemnización Pagada (Penal)' }] },
            ]
          },
        ]
    },
    {
      "nombre": 'Tutela*',
      "codigoProceso": 'TUT',
      "etapas": [
          { "nombre": 'Recepción Doc/ reporte', "codigoEtapa": 'REC', "subEtapas": [ { "nombre": 'Recepción Acción de Tutela', "codigoSubEtapa": 'REC', "actuaciones": [{ "nombre": 'Recibir Escrito Tutela', "codigoActuacion": 'REC', "terminaProceso": False, "estadoResultado": 'Tutela Recibida' }] } ] },
          { "nombre": 'Radicación', "codigoEtapa": 'RAD', "subEtapas": [ { "nombre": 'Radicación y Reparto', "codigoSubEtapa": 'RAD', "actuaciones": [{ "nombre": 'Radicar y Asignar Juez', "codigoActuacion": 'RAD', "terminaProceso": False, "estadoResultado": 'Tutela Radicada' }] } ] },
          { "nombre": 'Admite Tutela', "codigoEtapa": 'ADM', "subEtapas": [ { "nombre": 'Auto Admite Tutela', "codigoSubEtapa": 'ADM', "actuaciones": [{ "nombre": 'Emitir Auto Admisorio', "codigoActuacion": 'ADM', "terminaProceso": False, "estadoResultado": 'Tutela Admitida' }] } ] },
          { "nombre": 'Notificación', "codigoEtapa": 'NOT', "subEtapas": [ { "nombre": 'Notificación Accionado/Vinculados', "codigoSubEtapa": 'NOT', "actuaciones": [{ "nombre": 'Oficio Notificación Tutela', "codigoActuacion": 'NOT', "terminaProceso": False, "estadoResultado": 'Accionado Notificado' }] } ] },
          { "nombre": 'Contestación', "codigoEtapa": 'CONT', "subEtapas": [ { "nombre": 'Recepción Informe/Contestación', "codigoSubEtapa": 'CONT', "actuaciones": [{ "nombre": 'Recibir Respuesta Accionado', "codigoActuacion": 'CONT', "terminaProceso": False, "estadoResultado": 'Respuesta Recibida' }] } ] },
          { "nombre": 'Fallo', "codigoEtapa": 'FL1', "subEtapas": [ { "nombre": 'Emisión Fallo Tutela', "codigoSubEtapa": 'FL1', "actuaciones": [{ "nombre": 'Emitir Fallo 1ra Instancia', "codigoActuacion": 'FL1', "terminaProceso": False, "estadoResultado": 'Fallo 1ra Instancia Emitido' }] } ] },
          { "nombre": 'Impugnación', "codigoEtapa": 'IMP', "subEtapas": [
              { "nombre": 'Recepción Impugnación', "codigoSubEtapa": 'IMP_REC', "actuaciones": [{ "nombre": 'Recibir Escrito Impugnación', "codigoActuacion": 'IMP_REC', "terminaProceso": False, "estadoResultado": 'Impugnación Recibida' }] },
              { "nombre": 'Fallo Segunda Instancia', "codigoSubEtapa": 'FL2', "actuaciones": [{ "nombre": 'Emitir Fallo 2da Instancia', "codigoActuacion": 'FL2', "terminaProceso": False, "estadoResultado": 'Fallo 2da Instancia Emitido' }] },
            ]
          },
          { "nombre": 'Revisión Corte Constitucional', "codigoEtapa": 'REVCC', "subEtapas": [
              { "nombre": 'Selección para Revisión', "codigoSubEtapa": 'REVCC_SEL', "actuaciones": [{ "nombre": 'Auto Selección Corte', "codigoActuacion": 'REVCC_SEL', "terminaProceso": False, "estadoResultado": 'Seleccionada para Revisión' }] },
              { "nombre": 'Sentencia de Revisión', "codigoSubEtapa": 'REVCC_SEN', "actuaciones": [{ "nombre": 'Emitir Sentencia T', "codigoActuacion": 'REVCC_SEN', "terminaProceso": True, "estadoResultado": 'Sentencia Revisión (T)' }] },
              { "nombre": 'No Selección para Revisión', "codigoSubEtapa": 'REVCC_NOSEL', "actuaciones": [{ "nombre": 'Auto No Selección Corte', "codigoActuacion": 'REVCC_NOSEL', "terminaProceso": True, "estadoResultado": 'No Seleccionada (Firme)' }] },
            ]
          },
        ]
    },
    {
      "nombre": 'Investigación Administrativa*',
      "codigoProceso": 'INAD',
      "etapas": [
          { "nombre": 'Requerimiento Previo', "codigoEtapa": 'RQ', "subEtapas": [ { "nombre": 'Envío Requerimiento', "codigoSubEtapa": 'RQ', "actuaciones": [{ "nombre": 'Emitir y Enviar Requerimiento', "codigoActuacion": 'RQ', "terminaProceso": False, "estadoResultado": 'Requerimiento Enviado' }] } ] },
          { "nombre": 'Formulación de Cargos', "codigoEtapa": 'FC', "subEtapas": [ { "nombre": 'Auto Formula Cargos', "codigoSubEtapa": 'FC', "actuaciones": [{ "nombre": 'Emitir Auto Formulación Cargos', "codigoActuacion": 'FC', "terminaProceso": False, "estadoResultado": 'Cargos Formulados' }] } ] },
          { "nombre": 'Descargos', "codigoEtapa": 'DS', "subEtapas": [ { "nombre": 'Recepción Descargos', "codigoSubEtapa": 'DS', "actuaciones": [{ "nombre": 'Recibir Escrito Descargos', "codigoActuacion": 'DS', "terminaProceso": False, "estadoResultado": 'Descargos Recibidos' }] } ] },
          { "nombre": 'Resolución de Pruebas', "codigoEtapa": 'PRU', "subEtapas": [ { "nombre": 'Decreto y Práctica Pruebas', "codigoSubEtapa": 'PRU', "actuaciones": [{ "nombre": 'Auto Decreta Pruebas / Práctica', "codigoActuacion": 'PRU', "terminaProceso": False, "estadoResultado": 'Pruebas Decretadas/Practicadas' }] } ] },
          { "nombre": 'Alegatos', "codigoEtapa": 'ALE', "subEtapas": [ { "nombre": 'Presentación Alegatos', "codigoSubEtapa": 'ALE', "actuaciones": [{ "nombre": 'Recibir Alegatos de Conclusión', "codigoActuacion": 'ALE', "terminaProceso": False, "estadoResultado": 'Alegatos Recibidos' }] } ] },
          { "nombre": 'Resolución de Fallo', "codigoEtapa": 'RFLL', "subEtapas": [ { "nombre": 'Emisión Resolución Sancionatoria/Absolutoria', "codigoSubEtapa": 'RFLL', "actuaciones": [{ "nombre": 'Emitir Resolución Final', "codigoActuacion": 'RFLL', "terminaProceso": False, "estadoResultado": 'Fallo Emitido' }] } ] },
          { "nombre": 'Recursos', "codigoEtapa": 'RC', "subEtapas": [
              { "nombre": 'Interposición Recurso', "codigoSubEtapa": 'RC_INT', "actuaciones": [{ "nombre": 'Recibir Recurso Reposición/Apelación', "codigoActuacion": 'RC_INT', "terminaProceso": False, "estadoResultado": 'Recurso Interpuesto' }] },
              { "nombre": 'Resolución Recurso', "codigoSubEtapa": 'RC_RES', "actuaciones": [{ "nombre": 'Resolver Recurso', "codigoActuacion": 'RC_RES', "terminaProceso": True, "estadoResultado": 'Recurso Resuelto (Firme)' }] },
            ]
          },
          { "nombre": 'Nulidades', "codigoEtapa": 'N', "subEtapas": [
              { "nombre": 'Solicitud Nulidad', "codigoSubEtapa": 'N_SOL', "actuaciones": [{ "nombre": 'Presentar Solicitud Nulidad', "codigoActuacion": 'N_SOL', "terminaProceso": False, "estadoResultado": 'Nulidad Solicitada' }] },
              { "nombre": 'Decisión Nulidad', "codigoSubEtapa": 'N_DEC', "actuaciones": [{ "nombre": 'Resolver Solicitud Nulidad', "codigoActuacion": 'N_DEC', "terminaProceso": False, "estadoResultado": 'Nulidad Resuelta' }] },
            ]
          },
          { "nombre": 'Revocatoria', "codigoEtapa": 'RV', "subEtapas": [
              { "nombre": 'Solicitud Revocatoria Directa', "codigoSubEtapa": 'RV_SOL', "actuaciones": [{ "nombre": 'Presentar Solicitud Revocatoria', "codigoActuacion": 'RV_SOL', "terminaProceso": False, "estadoResultado": 'Revocatoria Solicitada' }] },
              { "nombre": 'Decisión Revocatoria Directa', "codigoSubEtapa": 'RV_DEC', "actuaciones": [{ "nombre": 'Resolver Revocatoria', "codigoActuacion": 'RV_DEC', "terminaProceso": True, "estadoResultado": 'Revocatoria Resuelta (Firme)' }] },
            ]
          },
          { "nombre": 'Terminación', "codigoEtapa": 'T', "subEtapas": [ { "nombre": 'Archivo Expediente', "codigoSubEtapa": 'T_INAD', "actuaciones": [{ "nombre": 'Auto Archivo Investigación', "codigoActuacion": 'T_INAD', "terminaProceso": True, "estadoResultado": 'Terminado (INAD)' }] } ] },
          { "nombre": 'Coactivo', "codigoEtapa": 'COAC', "subEtapas": [ { "nombre": 'Mandamiento de Pago (Coactivo)', "codigoSubEtapa": 'COAC_MAN', "actuaciones": [{ "nombre": 'Librar Mandamiento Pago Coactivo', "codigoActuacion": 'COAC_MAN', "terminaProceso": False, "estadoResultado": 'Mandamiento Pago (Coactivo)' }] } ] },
        ]
    },
]


class Command(BaseCommand):
    help = 'Populates the database with initial Proceso, Etapa, SubEtapa, and Actuacion definitions.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to populate process definitions...")

        for proceso_idx, proceso_data in enumerate(PROCESOS_DATA):
            proceso_obj, created_proceso = ProcesoDefinicion.objects.update_or_create(
                codigoProceso=proceso_data['codigoProceso'],
                defaults={'nombre': proceso_data['nombre']}
            )
            if created_proceso:
                self.stdout.write(self.style.SUCCESS(f"Created Proceso: {proceso_obj.nombre}"))
            else:
                self.stdout.write(f"Updated/Found Proceso: {proceso_obj.nombre}")

            for etapa_idx, etapa_data in enumerate(proceso_data.get('etapas', [])):
                etapa_obj, created_etapa = EtapaDefinicion.objects.update_or_create(
                    proceso_definicion=proceso_obj,
                    nombre=etapa_data['nombre'], # Using nombre for uniqueness within a proceso
                    defaults={
                        'codigoEtapa': etapa_data.get('codigoEtapa'),
                        'orden': etapa_idx
                    }
                )
                if created_etapa:
                    self.stdout.write(self.style.SUCCESS(f"  Created Etapa: {etapa_obj.nombre} (Order: {etapa_idx}) for {proceso_obj.nombre}"))
                else:
                    self.stdout.write(f"  Updated/Found Etapa: {etapa_obj.nombre} (Order: {etapa_idx}) for {proceso_obj.nombre}")


                for sub_etapa_idx, sub_etapa_data in enumerate(etapa_data.get('subEtapas', [])):
                    sub_etapa_obj, created_sub_etapa = SubEtapaDefinicion.objects.update_or_create(
                        etapa_definicion=etapa_obj,
                        nombre=sub_etapa_data['nombre'], # Using nombre for uniqueness within an etapa
                        defaults={
                            'codigoSubEtapa': sub_etapa_data.get('codigoSubEtapa'),
                            'orden': sub_etapa_idx
                        }
                    )
                    if created_sub_etapa:
                        self.stdout.write(self.style.SUCCESS(f"    Created SubEtapa: {sub_etapa_obj.nombre} (Order: {sub_etapa_idx}) for {etapa_obj.nombre}"))
                    else:
                        self.stdout.write(f"    Updated/Found SubEtapa: {sub_etapa_obj.nombre} (Order: {sub_etapa_idx}) for {etapa_obj.nombre}")

                    for actuacion_idx, actuacion_data in enumerate(sub_etapa_data.get('actuaciones', [])):
                        actuacion_defaults = {
                            'codigoActuacion': actuacion_data.get('codigoActuacion'),
                            'terminaProceso': actuacion_data.get('terminaProceso', False),
                            'estadoResultado': actuacion_data.get('estadoResultado'),
                            'descripcion': actuacion_data.get('descripcion'), # Optional
                            'orden': actuacion_idx
                        }
                        # Filter out None values from defaults if your model fields don't allow null for some of these
                        actuacion_defaults_cleaned = {k: v for k, v in actuacion_defaults.items() if v is not None}


                        actuacion_obj, created_actuacion = ActuacionDefinicion.objects.update_or_create(
                            sub_etapa_definicion=sub_etapa_obj,
                            nombre=actuacion_data['nombre'], # Using nombre for uniqueness within a subetapa
                            defaults=actuacion_defaults_cleaned
                        )
                        if created_actuacion:
                            self.stdout.write(self.style.SUCCESS(f"      Created Actuacion: {actuacion_obj.nombre} (Order: {actuacion_idx}) for {sub_etapa_obj.nombre}"))
                        else:
                             self.stdout.write(f"      Updated/Found Actuacion: {actuacion_obj.nombre} (Order: {actuacion_idx}) for {sub_etapa_obj.nombre}")
        
        self.stdout.write(self.style.SUCCESS("Successfully populated all process definitions."))