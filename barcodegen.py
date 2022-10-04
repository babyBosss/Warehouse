from barcode import EAN13
import barcode
from barcode.writer import ImageWriter


def save_bc(file_name, code):
    with open(file_name, 'wb') as f:
        EAN13(code, writer=ImageWriter()).write(f)

# EAN = barcode.get_barcode_class('ean13')
# ean = EAN(u'123456789011', writer=ImageWriter())
# fullname = ean.save('my_ean13_barcode')

