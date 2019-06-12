import csv
import xlsxwriter
import sys

if len(sys.argv) != 2:
    sys.exit("Reads a csv file on stdin and writes out an Excel file.\nusage: csv2xlsx.py <outfilename>\n")

workbook = xlsxwriter.Workbook(sys.argv[1])
worksheet = workbook.add_worksheet()
for i, row in enumerate(csv.reader(sys.stdin)):
    for j, cell in enumerate(row):
        worksheet.write_string(i, j, cell)
workbook.close
