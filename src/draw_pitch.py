import sys
import re


def hira_to_mora(hira):
    """Example:
    in:  'しゅんかしゅうとう'
    out: ['しゅ', 'ん', 'か', 'しゅ', 'う', 'と', 'う']
    """

    mora_arr = []
    combiners = [
        "ゃ",
        "ゅ",
        "ょ",
        "ぁ",
        "ぃ",
        "ぅ",
        "ぇ",
        "ぉ",
        "ャ",
        "ュ",
        "ョ",
        "ァ",
        "ィ",
        "ゥ",
        "ェ",
        "ォ",
    ]

    i = 0
    while i < len(hira):
        if i + 1 < len(hira) and hira[i + 1] in combiners:
            mora_arr.append("{}{}".format(hira[i], hira[i + 1]))
            i += 2
        else:
            mora_arr.append(hira[i])
            i += 1
    return mora_arr


def circle(x, y, o=False):
    r = f'<circle r="5" cx="{x}" cy="{y}" />'
    if o:
        r += f'<circle r="3.25" cx="{x}" cy="{y}" />'
    return r


def text(x, mora):
    # letter positioning tested with Noto Sans CJK JP
    if len(mora) == 1:
        return f'<text x="{x}" y="67.5">{mora}</text>'
    else:
        return f'<text x="{x - 5}" y="67.5">{mora[0]}</text><text x="{x + 12}" y="67.5" class="youon">{mora[1]}</text>'


def path(x, y, typ, step_width):
    if typ == "s":  # straight
        delta = f"{step_width},0"
    elif typ == "u":  # up
        delta = f"{step_width},-25"
    elif typ == "d":  # down
        delta = f"{step_width},25"
    return f'<path d="m {x},{y} {delta}" stroke-width="1.5" />'


def get_pitch_accent_class(patt, is_potential_kifuku=False):
    match = re.search(r"[H, h, 1, 2]{1}[L, l, 0]{1}", patt)

    drop_loc = match.start() if match else None

    if drop_loc is None:
        return "heiban"

    if is_potential_kifuku:
        return "kifuku"

    if drop_loc == 0:
        return "atamadaka"

    if drop_loc == len(patt):
        return "odaka"

    return "nakadaka"


def pitch_svg(word, patt, silent=False):
    """Draw pitch accent patterns in SVG

    Examples:
        はし HLL (箸)
        はし LHL (橋)
        はし LHH (端)
    """

    mora = hira_to_mora(word)

    if len(patt) - len(mora) != 1 and not silent:
        print(f"pattern should be number of morae + 1 (got: {word}, {patt})")

    positions = max(len(mora), len(patt))
    step_width = 35
    margin_lr = 16
    svg_width = max(0, ((positions - 1) * step_width) + (margin_lr * 2))

    pitch_accent = get_pitch_accent_class(patt)
    svg = f'<svg class="pitch {pitch_accent}" viewBox="0 0 {svg_width} 75">'

    chars = ""
    for pos, mor in enumerate(mora):
        x_center = margin_lr + (pos * step_width)
        chars += text(x_center - 11, mor)

    circles = ""
    paths = ""
    prev_center = (None, None)
    for pos, accent in enumerate(patt):
        x_center = margin_lr + (pos * step_width)
        if accent in ["H", "h", "1", "2"]:
            y_center = 5
        elif accent in ["L", "l", "0"]:
            y_center = 30
        circles += circle(x_center, y_center, pos >= len(mora))
        if pos > 0:
            if prev_center[1] == y_center:
                path_typ = "s"
            elif prev_center[1] < y_center:
                path_typ = "d"
            elif prev_center[1] > y_center:
                path_typ = "u"
            paths += path(prev_center[0], prev_center[1], path_typ, step_width)
        prev_center = (x_center, y_center)

    svg += chars
    svg += paths
    svg += circles
    svg += "</svg>"

    return svg


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 draw_pitch.py <word> <patt>")
        sys.exit()
    print(pitch_svg(sys.argv[1], sys.argv[2], silent=True))
