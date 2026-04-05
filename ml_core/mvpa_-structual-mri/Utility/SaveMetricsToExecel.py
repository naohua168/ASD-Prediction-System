import xlwt
from Utility.PerformanceMetrics import allMetrics
from datetime import datetime
import os
from xlrd import open_workbook
from xlutils.copy import copy
class SaveMetrics:
    def __init__(self,file_name):
        self.result_file_name=file_name

    def initMetricHeader(self,m,sheet,row,col):
        for key in m.metric.keys():
            sheet.write(row, col, key)
            col = col + 1
        return col
    def writeMetrics(self,m,sheet,row,col):
        for key in m.metric.keys():
            sheet.write(row, col, m.metric[key][0])
            col = col + 1
        return col
    def getexcel_row_sheet(self):
        if not os.path.exists(self.result_file_name):
            row=0
            excel=xlwt.Workbook(encoding='utf-8', style_compression=0)
            sheet = excel.add_sheet('Results', cell_overwrite_ok=True)
        else:
            book = open_workbook(self.result_file_name) # 读取excel文件
            row = book.sheets()[0].nrows
            excel = copy(book)
            sheet = excel.get_sheet(0)
        return row,excel,sheet
    def writeResultsHeader(self,metric,**kwargs):
        row,excel,sheet=self.getexcel_row_sheet()
        #写结果
        col = 0
        sheet.write(row,col,'Method_name')
        col = col +1
        if metric != None:
            col=self.initMetricHeader(metric,sheet,row,col)
        sheet.write(row,col,'Log_file_name')
        for key, value in kwargs.items():
            col = col + 1
            sheet.write(row, col, value)
        excel.save(self.result_file_name)
    def writeResultsMetrics(self,metric,method_name,log_file,**kwargs):
        row, excel, sheet = self.getexcel_row_sheet()
        #写结果
        col=0
        sheet.write(row, col, method_name)
        col = col +1
        if metric != None:
            col=self.writeMetrics(metric,sheet,row,col)
        sheet.write(row, col, log_file)
        for key, value in kwargs.items():
            col = col + 1
            sheet.write(row, col, value)
        excel.save(self.result_file_name)