import random
import zlib

import pikepdf

from magazine.pdf import _shrink


def _image(pdf, w, h, data):
    return pdf.make_stream(zlib.compress(data), Filter=pikepdf.Name.FlateDecode, Type=pikepdf.Name.XObject, Subtype=pikepdf.Name.Image, Width=w, Height=h,
                           ColorSpace=pikepdf.Name.DeviceRGB, BitsPerComponent=8)


def test_shrink_keeps_one_copy_of_an_image_and_makes_big_ones_jpeg():
    pdf = pikepdf.new()
    noise = random.Random(0).randbytes(400 * 300 * 3)  # big and lossless, like a photograph: worth a JPEG
    for _ in range(2):  # the same picture on two pages, embedded twice, as Chromium does
        pdf.add_blank_page()
        page = pdf.pages[-1]
        page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im0=_image(pdf, 400, 300, noise)))
        page.Contents = pdf.make_stream(b"q 400 0 0 300 0 0 cm /Im0 Do Q")
    _shrink(pdf)
    a, b = (p.Resources.XObject.Im0 for p in pdf.pages)
    assert a.objgen == b.objgen
    assert a.Filter == pikepdf.Name.DCTDecode
