import win32com.client as win32

excel_file = r'C:\Users\jemal\Downloads\FORMATO INVESTIGACION ACCIDENTE LABORAL.xlsx'
word_file = r'C:\Users\jemal\Downloads\FORMATO_INVESTIGACION_ACCIDENTE_LABORAL.docx'

MARGIN_POINTS = 28.35

excel = win32.Dispatch('Excel.Application')
excel.Visible = False

wb = excel.Workbooks.Open(excel_file)
ws = wb.ActiveSheet

ws.Range("A1:F122").Copy()

word = win32.Dispatch('Word.Application')
word.Visible = False

doc = word.Documents.Add()

section = doc.Sections(1)
section.PageSetup.TopMargin = MARGIN_POINTS
section.PageSetup.BottomMargin = MARGIN_POINTS
section.PageSetup.LeftMargin = MARGIN_POINTS
section.PageSetup.RightMargin = MARGIN_POINTS

# Pegado especial para tablas de Excel
word.Selection.PasteExcelTable(False, False, False)

try:
    from win32com.client import constants
    tabla = doc.Tables(1)
    tabla.AutoFitBehavior(constants.wdAutoFitWindow)
    tabla.AllowAutoFit = True
    tabla.PreferredWidthType = constants.wdPreferredWidthPercent
    tabla.PreferredWidth = 100
except:
    pass

doc.SaveAs(word_file, FileFormat=16)
doc.Close()

word.Quit()
wb.Close()
excel.Quit()
