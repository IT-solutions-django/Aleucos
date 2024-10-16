from django import forms


class XlsxImportOrderForm(forms.Form):
    xlsx_file = forms.FileField(label='XLSX-файл с') 