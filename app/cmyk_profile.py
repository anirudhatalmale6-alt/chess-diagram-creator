"""Generate a minimal ICC v2 CMYK output profile for naive RGB↔CMYK.

The profile embeds A2B0 (CMYK→Lab) and B2A0 (Lab→CMYK) CLUTs that
describe the exact naive conversion Pillow uses, so viewing software
can correctly interpret the CMYK values and display accurate colors.
"""

import math
import struct

# D50 white point (ICC PCS illuminant)
_D50_X, _D50_Y, _D50_Z = 0.9505, 1.0000, 1.0890

# Bradford chromatic-adaptation matrix D65→D50
_M_D65_D50 = [
    [1.0478112, 0.0228866, -0.0501270],
    [0.0295424, 0.9904844, -0.0170491],
    [-0.0092345, 0.0150436, 0.7521316],
]

# sRGB to XYZ (D65) matrix
_SRGB_MAT = [
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
]


def _s15f16(val):
    return struct.pack('>i', int(round(val * 65536)))


def _srgb_linearise(v):
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def _srgb_delinearise(v):
    v = max(0.0, min(1.0, v))
    if v <= 0.0031308:
        return v * 12.92
    return 1.055 * (v ** (1.0 / 2.4)) - 0.055


def _rgb_to_lab(r, g, b):
    """sRGB (0-1) → Lab (D50)."""
    rl = _srgb_linearise(r)
    gl = _srgb_linearise(g)
    bl = _srgb_linearise(b)

    # Linear RGB → XYZ (D65)
    x65 = _SRGB_MAT[0][0] * rl + _SRGB_MAT[0][1] * gl + _SRGB_MAT[0][2] * bl
    y65 = _SRGB_MAT[1][0] * rl + _SRGB_MAT[1][1] * gl + _SRGB_MAT[1][2] * bl
    z65 = _SRGB_MAT[2][0] * rl + _SRGB_MAT[2][1] * gl + _SRGB_MAT[2][2] * bl

    # D65 → D50
    x = _M_D65_D50[0][0] * x65 + _M_D65_D50[0][1] * y65 + _M_D65_D50[0][2] * z65
    y = _M_D65_D50[1][0] * x65 + _M_D65_D50[1][1] * y65 + _M_D65_D50[1][2] * z65
    z = _M_D65_D50[2][0] * x65 + _M_D65_D50[2][1] * y65 + _M_D65_D50[2][2] * z65

    def _f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else 7.787 * t + 16.0 / 116.0

    fx = _f(x / _D50_X)
    fy = _f(y / _D50_Y)
    fz = _f(z / _D50_Z)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)
    return L, a, b_val


def _cmyk_to_lab(c, m, y, k):
    """Naive CMYK (0-255) → Lab via reverse naive conversion."""
    r = max(0.0, 1.0 - (c + k) / 255.0)
    g = max(0.0, 1.0 - (m + k) / 255.0)
    b = max(0.0, 1.0 - (y + k) / 255.0)
    return _rgb_to_lab(r, g, b)


# Inverse D65→D50 (i.e. D50→D65)
_M_D50_D65 = [
    [0.9555766, -0.0230393, 0.0631636],
    [-0.0282895, 1.0099416, 0.0210077],
    [0.0122982, -0.0204830, 1.3299098],
]

# Inverse sRGB matrix (XYZ D65 → linear sRGB)
_SRGB_INV = [
    [3.2404542, -1.5371385, -0.4985314],
    [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252],
]


def _lab_to_cmyk(L, a, b_val):
    """Lab → sRGB → naive CMYK (0-255)."""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b_val / 200.0

    def _finv(t):
        return t ** 3 if t > 6.0 / 29.0 else (t - 16.0 / 116.0) / 7.787

    x = _finv(fx) * _D50_X
    y = _finv(fy) * _D50_Y
    z = _finv(fz) * _D50_Z

    # D50 → D65
    x65 = _M_D50_D65[0][0] * x + _M_D50_D65[0][1] * y + _M_D50_D65[0][2] * z
    y65 = _M_D50_D65[1][0] * x + _M_D50_D65[1][1] * y + _M_D50_D65[1][2] * z
    z65 = _M_D50_D65[2][0] * x + _M_D50_D65[2][1] * y + _M_D50_D65[2][2] * z

    rl = _SRGB_INV[0][0] * x65 + _SRGB_INV[0][1] * y65 + _SRGB_INV[0][2] * z65
    gl = _SRGB_INV[1][0] * x65 + _SRGB_INV[1][1] * y65 + _SRGB_INV[1][2] * z65
    bl = _SRGB_INV[2][0] * x65 + _SRGB_INV[2][1] * y65 + _SRGB_INV[2][2] * z65

    r = _srgb_delinearise(rl)
    g = _srgb_delinearise(gl)
    b = _srgb_delinearise(bl)

    # Naive RGB → CMYK
    c = 1.0 - r
    m = 1.0 - g
    y_c = 1.0 - b
    k = min(c, m, y_c)
    if k >= 1.0:
        return 0, 0, 0, 255
    c = (c - k)
    m = (m - k)
    y_c = (y_c - k)

    return (
        max(0, min(255, int(round(c * 255)))),
        max(0, min(255, int(round(m * 255)))),
        max(0, min(255, int(round(y_c * 255)))),
        max(0, min(255, int(round(k * 255)))),
    )


def _lab16(L, a, b_val):
    """Encode Lab as ICC v2 uint16 triplet."""
    L16 = max(0, min(65535, int(round(L * 65535.0 / 100.0))))
    a16 = max(0, min(65535, int(round((a + 128.0) * 65535.0 / 256.0))))
    b16 = max(0, min(65535, int(round((b_val + 128.0) * 65535.0 / 256.0))))
    return L16, a16, b16


def _build_lut16(input_ch, output_ch, grid, clut_func):
    """Build a lut16Type (mft2) tag payload."""
    data = bytearray()
    data += b'mft2' + b'\x00' * 4          # type + reserved
    data += struct.pack('BBBB', input_ch, output_ch, grid, 0)

    # Identity 3x3 matrix (unused for 4-channel input, required by format)
    for row in range(3):
        for col in range(3):
            data += _s15f16(1.0 if row == col else 0.0)

    n_in = 256
    n_out = 256
    data += struct.pack('>HH', n_in, n_out)

    # Linear input tables
    for _ in range(input_ch):
        for i in range(n_in):
            data += struct.pack('>H', int(round(i * 65535 / (n_in - 1))))

    # CLUT — input channels vary outermost-first
    total = grid ** input_ch
    indices = [0] * input_ch
    for _ in range(total):
        vals = [idx * 255.0 / (grid - 1) for idx in indices]
        out = clut_func(*vals)
        for v in out:
            data += struct.pack('>H', max(0, min(65535, int(round(v)))))

        # Increment indices (last channel fastest)
        carry = True
        for ch in range(input_ch - 1, -1, -1):
            if carry:
                indices[ch] += 1
                if indices[ch] >= grid:
                    indices[ch] = 0
                else:
                    carry = False

    # Linear output tables
    for _ in range(output_ch):
        for i in range(n_out):
            data += struct.pack('>H', int(round(i * 65535 / (n_out - 1))))

    return bytes(data)


def _build_desc(text):
    """Build a profileDescriptionType tag."""
    t = text.encode('ascii') + b'\x00'
    data = b'desc' + b'\x00' * 4
    data += struct.pack('>I', len(t))
    data += t
    data += struct.pack('>II', 0, 0)        # unicode lang + count
    data += struct.pack('>HB', 0, 0)        # scriptcode
    data += b'\x00' * 67                    # scriptcode string
    pad = (4 - len(data) % 4) % 4
    return data + b'\x00' * pad


def _build_text(text):
    """Build a textType tag."""
    data = b'text' + b'\x00' * 4
    data += text.encode('ascii') + b'\x00'
    pad = (4 - len(data) % 4) % 4
    return data + b'\x00' * pad


def _build_xyz(x, y, z):
    """Build an XYZType tag."""
    return b'XYZ ' + b'\x00' * 4 + _s15f16(x) + _s15f16(y) + _s15f16(z)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_CACHED_PROFILE = None


def get_naive_cmyk_profile():
    """Return bytes of a valid ICC v2 CMYK output profile.

    Describes the naive CMYK ↔ sRGB conversion so viewers can
    correctly display CMYK data produced by the simple formula.
    Result is cached after first call.
    """
    global _CACHED_PROFILE
    if _CACHED_PROFILE is not None:
        return _CACHED_PROFILE

    grid = 9

    # A2B0: CMYK (4ch) → Lab (3ch)
    def _a2b0_func(c, m, y, k):
        L, a, b = _cmyk_to_lab(c, m, y, k)
        return _lab16(L, a, b)

    a2b0_data = _build_lut16(4, 3, grid, _a2b0_func)

    # B2A0: Lab (3ch) → CMYK (4ch)
    def _b2a0_func(L_enc, a_enc, b_enc):
        L = L_enc / 255.0 * 100.0
        a = a_enc / 255.0 * 256.0 - 128.0
        b = b_enc / 255.0 * 256.0 - 128.0
        c, m, y, k = _lab_to_cmyk(L, a, b)
        return (c * 257, m * 257, y * 257, k * 257)  # scale 0-255 → 0-65535

    b2a0_data = _build_lut16(3, 4, grid, _b2a0_func)

    desc_data = _build_desc("Chess Diagram CMYK")
    cprt_data = _build_text("Public Domain")
    wtpt_data = _build_xyz(_D50_X, _D50_Y, _D50_Z)

    tags = [
        (b'A2B0', a2b0_data),
        (b'B2A0', b2a0_data),
        (b'cprt', cprt_data),
        (b'desc', desc_data),
        (b'wtpt', wtpt_data),
    ]
    # Sort by tag signature (required by ICC spec)
    tags.sort(key=lambda t: t[0])

    num_tags = len(tags)
    header_size = 128
    tag_table_size = 4 + num_tags * 12
    data_offset = header_size + tag_table_size

    entries = []
    offset = data_offset
    for sig, payload in tags:
        entries.append((sig, offset, len(payload)))
        offset += len(payload)
        offset += (4 - len(payload) % 4) % 4  # pad

    profile_size = offset

    # ---- Header (128 bytes) ----
    hdr = bytearray(128)
    struct.pack_into('>I', hdr, 0, profile_size)
    hdr[4:8] = b'lcms'
    struct.pack_into('>I', hdr, 8, 0x02100000)  # v2.1
    hdr[12:16] = b'prtr'                         # output device
    hdr[16:20] = b'CMYK'
    hdr[20:24] = b'Lab '
    struct.pack_into('>HHHHHH', hdr, 24, 2024, 1, 1, 0, 0, 0)
    hdr[36:40] = b'acsp'
    struct.pack_into('>i', hdr, 68, int(round(_D50_X * 65536)))
    struct.pack_into('>i', hdr, 72, int(round(_D50_Y * 65536)))
    struct.pack_into('>i', hdr, 76, int(round(_D50_Z * 65536)))

    # ---- Assemble ----
    buf = bytes(hdr)
    buf += struct.pack('>I', num_tags)
    for sig, off, sz in entries:
        buf += sig + struct.pack('>II', off, sz)
    for _, payload in tags:
        buf += payload
        pad = (4 - len(payload) % 4) % 4
        buf += b'\x00' * pad

    _CACHED_PROFILE = buf
    return buf
