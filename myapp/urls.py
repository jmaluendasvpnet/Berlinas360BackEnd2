from . import XlsxRptos, StoredProcedures, api, views, SendSurvey, views_whatsapp, view_rf_for
from . import crearExcel, rptoFuec, reporteAlcoholimetria, RptosConductores
# from myapp.ocr.layoutlm_inference import UploadLicenseView
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework import routers
from django.conf import settings

router = routers.DefaultRouter()
router.register('roles', api.RolesViewSet, "Roles")
router.register('login', api.LoginViewSet, "Login")
router.register('modulos', api.ModulosViewSet, "Modulos")
router.register('acciones', api.AccionesVS, "Acciones")
router.register('permisos', api.PermisosViewSet, "Permisos")
router.register('empresas', api.EmpresasViewSet, "Empresas")
router.register('departments', api.DepartmentsViewSet, "Departaments")
router.register('vehiculos', api.VehiculosVS, "Vehiculos")
router.register(r'servicios', api.ServicioVS)
router.register(r'propietarios', api.PropietarioVS)
router.register(r'contratos', api.ContratoVS)
router.register(r'tenedores', api.TenedorVS)
router.register(r'reportes-vencimientos', api.ReporteVencimientosDiarioVS, basename='reportevencimientosdiario')
router.register(r'soats', api.SoatVS)
router.register(r'revision-tecnomecanica', api.RevisionTecnomecanicaVS)
router.register(r'tarjeta-operacion', api.TarjetaOperacionVS)
router.register(r'licencia-transito', api.LicenciaTransitoVS)
router.register(r'polizas-contractuales', api.PolizaContractualVS, basename='polizacontractual')
router.register(r'polizas-extracontractuales', api.PolizaExtracontractualVS, basename='polizaextracontractual')
router.register(r'polizas-todo-riesgo', api.PolizaTodoRiesgoVS, basename='polizatodoriesgo')
router.register(r'polizas', api.PolizaVS)
router.register(r'novedades-vehiculo', api.NovedadVehiculoVS)
router.register(r'fichas-tecnicas', api.FichaTecnicaVS)
router.register(r'conductores-asociados', api.ConductorAsociadoVS)
router.register(r'procedimientos-juridicos', api.ProcedimientoJuridicoViewSet)
router.register('eventos-legales', api.EventoLegalViewSet)
router.register(r'mantenimientos', api.MantenimientoVS)
router.register(r'facturaciones', api.FacturacionVS)
router.register(r'marcas', api.MarcaVS, basename='marca')
router.register(r'tipos-linea', api.TipoLineaVS, basename='tipolinea')
router.register(r'clases-vehiculo', api.ClaseVehiculoVS)
router.register(r'carrocerias', api.CarroceriaVS, basename='carroceria')
router.register(r'combustibles', api.CombustibleVS)
router.register(r'tipos-operacion', api.TipoOperacionVS)
router.register(r'ciudades', api.CiudadVS)
router.register(r'niveles-servicio', api.NivelServicioVS)
router.register(r'categorias', api.CategoriaVS)
router.register(r'colores', api.ColorVS, basename='color')
router.register('headquarters', api.HeadquartersViewSet, "Sedes")
router.register('notifications', api.NotificationVS, "Notificaciones")
router.register('docsti', api.TipoDocumentoViewSet, "TipoDocumento")
router.register('colaboradores', api.ColaboradoresViewSet, "Colaboradores")
router.register('evento-documento', api.EventoDocumentoViewSet, basename='EventoDocumento')
router.register('events', api.EventsViewSet, "Events")
router.register('agenda', api.AgendaViewSet, "Agenda")
router.register('evaluations', api.EvaluationViewSet, "Evaluaciones")
router.register('trainings_categories', api.TrainingsCategoriesViewSet, "Capacitaciones categorias")
router.register('enviar-respuestas', api.EnviarRespuestasViewSet, "Enviar respuestas")
router.register('induction_doc', api.InductionDocViewSet, "Docuemto Induccion")
router.register('test', api.TestViewSet, "Test")
router.register('test_drivers', api.TestDriversViewSet, "Test Driverss")
router.register('test_driversession', api.TestDriversSessionViewSet, "Test Sessions")
router.register('written_test', api.WrittenTestViewSet, "Test Sessions3")
router.register('written_test_session', api.WrittenTestSessionVS, "Test Sessions2")
router.register('siniestros', api.SiniestroVS, "Formulario de siniestros")
router.register('siniestros_media', api.SiniestroMediaVS, "Formulario de siniestros2")
router.register('ipat', api.IpatVS, "ipat")
router.register('entes', api.EnteAtencionVS, "Entes de atención")
router.register('terceros', api.TerceroVS, "Terceros")
router.register('conciliaciones', api.ActaConciliacionVS, "Actas de Conciliación")
router.register('procesos-definicion', api.ProcesoDefinicionVS, basename="procesos_definicion")
router.register('etapas-definicion', api.EtapaDefinicionVS, basename="etapas_definicion")
router.register('subetapas-definicion', api.SubEtapaDefinicionVS, basename="subetapas_definicion")
router.register('actuaciones-definicion', api.ActuacionDefinicionVS, basename="actuaciones_definicion")

router.register('victimas', api.VictimaVS, basename="victimas")
router.register('victimas-procesos', api.VictimaProcesoVS, basename="victimas_procesos")
router.register('historial-actuaciones', api.HistorialActuacionVS, basename="historial_actuaciones")


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/upload/', csrf_exempt(views.upload_image)),
    path('siniestros/create/', csrf_exempt(views.create_siniestro)),
    path('siniestros/upload/', csrf_exempt(views.upload_media)),
    path('text/', csrf_exempt(views.text)),
    path('login/', views.LoginView.as_view(), name='Inicio de sesion'),
    path('whatsapp_webhook/', views_whatsapp.whatsapp_webhook, name='webhook_whatsapp'),


    path('upload-license/', views.UploadLicenseView.as_view(), name='upload-license'),
    path('upload-licenses-xlsx/', views.BulkUploadDocsAPIView.as_view(), name='upload-licenses-xlsx'),
    path('upload-corrected-xlsx/', views.UploadCorrectedXlsxAPIView.as_view(), name='upload-corrected-xlsx'),
    path('upload-license2/', view_rf_for.UploadLicenseView.as_view(), name='upload-license'),
#     path('UploadColombianLicenseView/', views.UploadColombianLicenseView.as_view(), name='upload-license-col'),

    path('upload/', views.UploadView.as_view(), name='upload'),

    path('api/export-vehiculos-data/', views.export_vehiculos_data, name='export_vehiculos_data'),
    path('api/generate-excel-report/', views.generate_excel_report2, name='generate_excel_report'),


path('upload-excel/', views.upload_excel, name='upload_excel'),
path('generar_documento_con_imagen/', views.generar_documento_con_imagen, name='word'),
path('analisis_recomendaciones_openai/', views.analisis_recomendaciones_openai, name='openai'),

#     path('events/<int:event_id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('loginface/', views.LoginFaceView.as_view(),
         name='Login con Face Id'),

     path('convert-pdf/', SendSurvey.docx_to_pdf_view, name='Docx to PDF'),
     path('convert-pdf-and-save/', SendSurvey.docx_to_pdf_and_save_in_model, name='docx_to_pdf_and_save_in_model'),
     path('docx_to_pdf_and_save_in_model/', views.docx_to_pdf_and_save_in_model),
     
     path('print_data/', views.print_data, name='Mostrar datos del Bird'),
     # path('send_survey/', SendSurvey.process_excel, name='send_survey'),

    # Crud Usuarios
    path('addUsers/', views.UsersView.as_view({'post': 'post'})),
     path('create_temp_user/', views.UsersView.as_view({'post': 'create_temp_user'})),
    # Lectura de menu
    path('menu/<rol>/',
         views.MenuView.as_view({'get': 'get'}), name='Lista Menu'),
    # Cambio de contraseña con correo de verificacion
    path('reset_password/',
         views.ResetPass.as_view({'post': 'send_reset_email'}), name='send_reset_email'),
    path('reset_password/change/',
         views.ResetPass.as_view({'post': 'new_pass'}), name='change pass'),
    path('subir_foto/',
         views.subir_foto, name='subir_foto'),
#     path('subir_fto/',
#          csrf_exempt(view_rf_for.reconocimiento_facial), name='subir_fto'),
#     path('time_record/', csrf_exempt(view_rf_for.time_record), name='subir_fto'),
    path('generar_excel/', crearExcel.generar_excel, name='generar_excel'),
    path('callViajes/', rptoFuec.rptoFuec, name='Llamar Viajes'),
    path('callRptoViaje/', rptoFuec.rptoFuecPDF,
         name='Llamar datos para el reporte'),
    path('saveRpto/', csrf_exempt(rptoFuec.saveRpto), name='Guardar el reporte'),
    #    Handle reportes WsDx
    path('RP_consultas01/', csrf_exempt(StoredProcedures.RP_consultas01),
         name='Reporte Estadistica Comercial'),
    path('XlsxRP_consultas01/', csrf_exempt(XlsxRptos.XlsxRP_consultas01),
         name='Generacion de reporte en excel de Comercial'),
     path('RP_Consultas05/', views.RP_Consultas05, name='Reporte Domicilios'),
    path('XlsxRP_Consultas05/', views.XlsxRP_Consultas05, name='Generacion de reporte en excel'),
#     path('RP_Consultas05/', csrf_exempt(StoredProcedures.RP_Consultas05),
#          name='Reporte Domicilios'),
#     path('XlsxRP_Consultas05/', csrf_exempt(XlsxRptos.XlsxRP_Consultas05),
#          name='Generacion de reporte en excel'),
    path('RP_CuotaAdmon/', csrf_exempt(StoredProcedures.RP_CuotaAdmon),
         name='Reporte cuota de administracion'),
    path('XlsxRP_CuotaAdmon/', csrf_exempt(XlsxRptos.XlsxRP_CuotaAdmon),
         name='Generacion de excel en plantilla'),
    path('Rp_certificaciones/', csrf_exempt(StoredProcedures.Rp_certificaciones),
         name='Reporte Estadistica Certificados'),
    path('RP_Macarena/', csrf_exempt(StoredProcedures.RP_Macarena),
         name='Reporte Macarena'),
    path('XlxsRP_Macarena/', csrf_exempt(XlsxRptos.XlxsRP_Macarena),
         name='Generacion de reporte en excel de Macarena'),
    path('Sp_RptHistoFuec/', csrf_exempt(StoredProcedures.Sp_RptHistoFuec),
         name='Reporte Historico del Fuec'),
    path('XlsxSp_RptHistoFuec/', csrf_exempt(XlsxRptos.XlsxSp_RptHistoFuec),
         name='Generacion de reporte en excel del FUEC'),
    path('RP_Prueba_Alcoholimetria/', csrf_exempt(StoredProcedures.RP_Prueba_Alcoholimetria),
         name='Reporte de alcoholimetria'),
    path('XlsxFics_MicroSegurosGET/', csrf_exempt(XlsxRptos.XlsxFics_MicroSegurosGET),
         name='Reporte Excel de Tiquetes con Microseguros'),
    path('generarRptoAlcoholimetria/', csrf_exempt(reporteAlcoholimetria.generarRptoAlcoholimetria),
         name='Generacion de reporte en excel de alcoholimetria'),
    path('UsuarioFrecuente/',
         csrf_exempt(StoredProcedures.UsuarioFrecuente), name='Pvu'),
    path('VO_ViajeroFrecuente/',
         csrf_exempt(StoredProcedures.VO_ViajeroFrecuente), name='Pvu'),
    path('RP_Dominicales/', csrf_exempt(StoredProcedures.RP_Dominicales), name='Pvu'),
    path('Rp_CRM/', csrf_exempt(StoredProcedures.Rp_CRM),
         name='Rpto Tiquetes CRM'),
    path('RP_CondvigFICS/', csrf_exempt(StoredProcedures.RP_CondvigFICS), name=''),
    path('generarRptoConductores/', csrf_exempt(RptosConductores.generarRptoConductores),
         name='Generacion de reporte en excel de Conductores'),
    path('RP_MIGRACION/', csrf_exempt(StoredProcedures.RP_MIGRACION),
         name='Reporte Historico de Migracion'),
    path('XlsxRP_MIGRACION/', csrf_exempt(XlsxRptos.XlsxRP_MIGRACION),
         name='Generacion de reporte en excel de Migracion'),
    path('RPT_EstadisticaXTaquilla/', csrf_exempt(StoredProcedures.RPT_EstadisticaXTaquilla),
         name='Reporte Taquillas Bogota'),
    path('XlsxRPT_EstadisticaXTaquilla/', csrf_exempt(XlsxRptos.XlsxRPT_EstadisticaXTaquilla),
         name='Reporte Excel Taquillas Bogota'),
    path('Fics_MicroSegurosGET/', csrf_exempt(StoredProcedures.Fics_MicroSegurosGET),
         name='Reporte MicroSeguros'),
    path('RP_Consultas04/', csrf_exempt(StoredProcedures.RP_Consultas04),
         name='Reporte Tiquetes con MicroSeguros'),
    path('Rp_VF3/', csrf_exempt(StoredProcedures.Rp_VF3),
         name='Reporte Turismo'),
    path('PD_GetExtractoTER/', csrf_exempt(StoredProcedures.PD_GetExtractoTER),
         name='Reporte Extractos Directivo Contabilidad'),
    path('XlsxPD_GetExtractoTER/', csrf_exempt(XlsxRptos.XlsxPD_GetExtractoTER),
         name='Reporte Extractos Directivo Contabilidad'),
    path('AC_ComTaqNoNomina/', csrf_exempt(StoredProcedures.AC_ComTaqNoNomina),
         name='Liquidacion de Comisiones Taquilleros NO NOMINA'),
    path('XlsxAC_ComTaqNoNomina/', csrf_exempt(XlsxRptos.XlsxAC_ComTaqNoNomina),
         name='Liquidacion de Comisiones Taquilleros NO NOMINA'),
    path('RP_ConsultaVO/', csrf_exempt(StoredProcedures.RP_ConsultaVO),
         name='Reporte Taquillas Bogota'),
#     path('loginface/', view_rf_for.LoginFaceView.as_view(),
#          name='Login con Face Id'),

     path('gen_xlsx/', csrf_exempt(views.generate_excel_report), name="GenXlsx")

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
