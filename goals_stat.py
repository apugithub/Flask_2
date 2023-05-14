import xlrd
from paths import blue_bird_mf


workbook = xlrd.open_workbook(blue_bird_mf + 'Simple-financial-planning-sheet.xlsm')

ret = workbook.sheet_by_name(sheet_name='Ret-Allocation')
ret_equity = round(ret.cell_value(29, 3))
ret_debt = round(ret.cell_value(30, 3))

# print(ret_equity)
# print(ret_debt)

ch1_mar = workbook.sheet_by_name(sheet_name='CH1-Mar')
ch1_mar_equity = round(ch1_mar.cell_value(11, 6) * 100)
ch1_mar_debt = round(ch1_mar.cell_value(12, 6) * 100)

# print(ch1_mar_equity)
# print(ch1_mar_debt)

ant = workbook.sheet_by_name(sheet_name='Antarctica')
ant_equity = round(ant.cell_value(14, 8)*100)
ant_debt = round(ant.cell_value(15, 8)*100)

# print(ant_equity)
# print(ant_debt)
