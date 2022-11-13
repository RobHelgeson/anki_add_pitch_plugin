""" Utility functions.
"""

import re
from aqt import mw
from aqt.utils import Qt, QDialog, QVBoxLayout, QLabel, QListWidget,\
                      QDialogButtonBox
from anki.utils import stripHTML
from .draw_pitch import pitch_svg


def customChooseList(msg, choices, startrow=0):
    """ Copy of https://github.com/ankitects/anki/blob/main/
            qt/aqt/utils.py but with a cancel button added.

    """

    parent = mw.app.activeWindow()
    d = QDialog(parent)
    d.setWindowModality(Qt.WindowModal)
    l = QVBoxLayout()
    d.setLayout(l)
    t = QLabel(msg)
    l.addWidget(t)
    c = QListWidget()
    c.addItems(choices)
    c.setCurrentRow(startrow)
    l.addWidget(c)
    buts = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
    bb = QDialogButtonBox(buts)
    l.addWidget(bb)
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    l.addWidget(bb)
    ret = d.exec_()  # 1 if Ok, 0 if Cancel or window closed
    if ret == 0:
        return None  # can't be False b/c False == 0
    return c.currentRow()


def select_deck_id(msg):
    """ UI dialog that prints <msg> as a prompt to
        the user shows a list of all decks in the
        collection.
        Returns the ID of the selected deck or None
        if dialog is cancelled.
    """

    decks = mw.col.decks.all()
    choices = [d['name'] for d in decks]
    choice_idx = customChooseList(msg, choices)
    if choice_idx is None:
        return None
    return decks[choice_idx]['id']


def select_note_type_id(note_type_ids):
    """ UI dialog that prompts the user to select a
        note type.
        Returns the ID of the selected name type or
        None if dialog is cancelled.
    """

    note_types = mw.col.models.all()
    choices = [
        {'id': nt['id'], 'name': nt['name']}
        for nt in note_types
        if nt['id'] in note_type_ids
    ]
    choice_idx = customChooseList(
        'Select a note type.',
        [c['name'] for c in choices]
        )
    if choice_idx is None:
        return None
    return choices[choice_idx]['id']


def get_accent_dict(path):
    acc_dict = {}
    with open(path, encoding='utf8') as f:
        for line in f:
            orths_txt, hira, hz, accs_txt, patts_txt = line.strip().split(
                '\u241e'
            )
            orth_txts = orths_txt.split('\u241f')
            if clean_orth(orth_txts[0]) != orth_txts[0]:
                orth_txts = [clean_orth(orth_txts[0])] + orth_txts
            patts = patts_txt.split(',')
            patt_common = patts[0]  # TODO: extend to support variants?
            if is_katakana(orth_txts[0]):
                hira = hira_to_kata(hira)
            for orth in orth_txts:
                if orth not in acc_dict:
                    acc_dict[orth] = []
                new = True
                for patt in acc_dict[orth]:
                    if patt[0] == hira and patt[1] == patt_common:
                        new = False
                        break
                if new:
                    acc_dict[orth].append((hira, patt_common))
    return acc_dict


def get_user_accent_dict(path):
    acc_dict = {}
    with open(path, encoding='utf8') as f:
        for line in f:
            orth, hira, patt = line.strip().split('\t')
            if orth in acc_dict:
                acc_dict[orth].append((hira, patt))
            else:
                acc_dict[orth] = [(hira, patt)]
    return acc_dict


def get_note_type_ids(deck_id):
    """ Return a list of the IDs of note types used
        in a deck.
    """

    card_ids = mw.col.decks.cids(deck_id)
    note_type_ids = set(
        [mw.col.get_card(cid).note_type()['id'] for cid in card_ids]
    )
    return list(note_type_ids)


def get_note_ids(deck_id, note_type_id):
    """ Return a list of the IDs of notes, given a
        deck ID and note type ID.
    """

    note_ids = []
    deck_card_ids = mw.col.decks.cids(deck_id)
    for cid in deck_card_ids:
        c = mw.col.get_card(cid)
        if c.note_type()['id'] == note_type_id and c.nid not in note_ids:
            note_ids.append(c.nid)
    return note_ids


def select_note_fields_add(note_type_id):
    """ For a given note type, prompt the user to select which field
        - contain the Japanese expression
        - contain the reading
        - the pitch accent should be shown in
        and return the respective indices of those fields in the note
        type’s list of fields.
    """

    choices = [nt['name'] for nt in mw.col.models.get(note_type_id)['flds']]
    expr_idx = customChooseList(
        'Which field contains the Japanese expression?', choices
        )
    if expr_idx is None:
        return None, None, None
    reading_idx = customChooseList(
        'Which field contains the reading?', choices
        )
    if reading_idx is None:
        return None, None, None
    output_idx = customChooseList(
        'Which field should the pitch accent be shown in?', choices
        )
    if output_idx is None:
        return None, None, None
    return expr_idx, reading_idx, output_idx


def select_note_fields_del(note_type_id):
    """ For a given note type, prompt the user to select which field
        the pitch accent should be removed from, and return the respective
        index of this field in the note type’s list of fields.
    """
    choices = [nt['name'] for nt in mw.col.models.get(note_type_id)['flds']]
    del_idx = customChooseList(
        'Which field should the pitch accent be removed from?', choices
        )
    return del_idx


def clean(s):
    # remove HTML
    s = stripHTML(s)
    # remove everyhing in brackets
    s = re.sub(r'[\[\(\{][^\]\)\}]*[\]\)\}]', '', s)
    return s.strip()


def get_acc_patt(expr_field, reading_field, dicts):
    def select_best_patt(reading_field, patts):
        best_pos = 9001
        best = patts[0]  # default
        for patt in patts:
            hira, p = patt
            try:
                pos = reading_field.index(hira)
                if pos < best_pos:
                    best = patt
                    best_pos = pos
            except ValueError:
                continue
        return best
    expr_field = clean(expr_field)
    reading_field = clean(reading_field)
    if len(expr_field) == 0:
        return False
    for dic in dicts:
        patts = dic.get(expr_field, False)
        if patts:
            return select_best_patt(reading_field, patts)
        guess = expr_field.split(' ')[0]
        patts = dic.get(guess, False)
        if patts:
            return select_best_patt(reading_field, patts)
        guess = re.sub('[<&]', ' ', expr_field).split(' ')[0]
        patts = dic.get(guess, False)
        if patts:
            return select_best_patt(reading_field, patts)
    return False


def add_pitch(acc_dict, note_ids, expr_idx, reading_idx, output_idx):
    """ Add pitch accent illustration to notes.

        Returns stats on how it went.
    """

    not_found_list = []
    num_updated = 0
    num_already_done = 0
    num_svg_fail = 0
    for nid in note_ids:
        note = mw.col.get_note(nid)
        expr_fld = note.keys()[expr_idx]
        reading_fld = note.keys()[reading_idx]
        output_fld = note.keys()[output_idx]
        if ('<!-- accent_start -->' in note[output_fld] or
                '<!-- user_accent_start -->' in note[output_fld]):
            # already has a pitch accent illustration
            num_already_done += 1
            continue
        expr_field = note[expr_fld].strip()
        reading_field = note[reading_fld].strip()
        patt = get_acc_patt(expr_field, reading_field, [acc_dict])
        if not patt:
            not_found_list.append([nid, expr_field])
            continue
        hira, LlHh_patt = patt
        LH_patt = re.sub(r'[lh]', '', LlHh_patt)
        svg = pitch_svg(hira, LH_patt)
        if not svg:
            num_svg_fail += 1
            continue
        if len(note[output_fld]) > 0:
            separator = '<br><hr><br>'
        else:
            separator = ''
        note[output_fld] = (
            '{}<!-- accent_start -->{}{}<!-- accent_end -->'
            ).format(note[output_fld], separator, svg)  # add svg
        mw.col.update_note(note)
        num_updated += 1
    return not_found_list, num_updated, num_already_done, num_svg_fail


def remove_pitch(note_ids, del_idx, user_set=False):
    """ Remove pitch accent illustrations from a specified field.

        Returns stats on how that went.
    """

    if user_set:
        tag_prefix = 'user_'
    else:
        tag_prefix = ''
    acc_patt = re.compile(
        r'<!-- {}accent_start -->.+<!-- {}accent_end -->'.format(
            tag_prefix, tag_prefix
        ),
        re.S
    )
    num_updated = 0
    num_already_done = 0
    for nid in note_ids:
        note = mw.col.get_note(nid)
        del_fld = note.keys()[del_idx]
        if ' {}accent_start'.format(tag_prefix) not in note[del_fld]:
            # has no pitch accent image
            num_already_done += 1
            continue
        note[del_fld] = re.sub(acc_patt, '', note[del_fld])
        mw.col.update_note(note)
        num_updated += 1
    return num_already_done, num_updated


def hira_to_kata(s):
    return ''.join(
        [chr(ord(ch) + 96) if ('ぁ' <= ch <= 'ゔ') else ch for ch in s]
        )


def is_katakana(s):
    num_ktkn = 0
    for ch in s:
        if ch == 'ー' or ('ァ' <= ch <= 'ヴ'):
            num_ktkn += 1
    return num_ktkn / max(1, len(s)) > .5


def clean_orth(orth):
    orth = re.sub('[()△×･〈〉{}]', '', orth)  #
    orth = orth.replace('…', '〜')  # change depending on what you use
    return orth
