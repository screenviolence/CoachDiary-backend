def create_excel_formats(workbook):
    """Создает и возвращает словарь форматов для Excel."""
    formats = {
        'header': workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'center',
            'align': 'center',
            'border': 1
        }),
        'cell': workbook.add_format({
            'align': 'center',
            'valign': 'center',
            'border': 1
        }),
        'gray_cell': workbook.add_format({
            'align': 'center',
            'valign': 'center',
            'border': 1,
            'bg_color': '#F2F2F2'
        }),
        'boy': workbook.add_format({
            'align': 'center',
            'valign': 'center',
            'border': 1,
            'bg_color': '#DCEBFF'
        }),
        'girl': workbook.add_format({
            'align': 'center',
            'valign': 'center',
            'border': 1,
            'bg_color': '#FFDEEB'
        })
    }
    return formats


def write_headers_and_data(worksheet, df, formats, gender_col=None):
    """Общий метод для записи заголовков и данных таблицы с форматированием."""
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, formats['header'])

    for row_num in range(len(df)):
        is_gray_row = row_num % 2 == 1
        row_format = formats['gray_cell'] if is_gray_row else formats['cell']

        for col_num, value in enumerate(df.iloc[row_num]):
            if gender_col is not None and col_num == gender_col:
                gender = df.iloc[row_num, gender_col] == 'м'
                gender_format = formats['boy'] if gender else formats['girl']
                worksheet.write(row_num + 1, col_num, value, gender_format)
            else:
                worksheet.write(row_num + 1, col_num, value, row_format)
