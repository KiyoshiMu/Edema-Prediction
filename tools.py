import os
from shutil import copy
from os.path import join, basename, splitext
import SimpleITK, pydicom
import pickle
from collections import defaultdict
import sys

def load_pickle(pkl_path) -> dict:
    with open(pkl_path, 'rb') as temp:
        container = pickle.load(temp)
    return container

def save_dict(container:dict, name, dst) -> None:
    os.makedirs(dst, exist_ok=True)
    with open(join(dst, name+'.pkl'), 'wb+') as saver:
        pickle.dump(container, saver, pickle.HIGHEST_PROTOCOL)

def multi_read(dir_p:str, func=None) -> str:
    def base_read(dir_p):
        for item in os.walk(dir_p):
            if item[2]:
                for fn in item[2]:
                    yield join(item[0], fn)
    return filter(func, base_read(dir_p))

def get_name(p):
    return splitext(basename(p))[0]

def read_info(dcm_p:str):
    info = pydicom.dcmread(dcm_p)
    try:
        z = info.SliceThickness
        x,y = info.PixelSpacin
        return {"spacingInfo":tuple([float(i) for i in [x, y, z]]),
        "PatientID":str(info.PatientID),
        "StudyDate":str(info.StudyDate)}
    except AttributeError:
        print(f'{get_name(dcm_p)}')

def arrange(dir_p:str, dst, func=lambda x:x[-4:]=='.dcm') -> None:
    record = defaultdict(list)
    for dcm_p in filter(func, multi_read(dir_p)):
        arrange_info = read_info(dcm_p)
        if isinstance(arrange_info, dict):
            dir_name = f"{arrange_info['PatientID']}_{arrange_info['StudyDate']}"
            dst_dir = join(dst, dir_name)
            record[dst_dir].append(dcm_p)
            if len(record[dst_dir]) == 1:
                save_dict(arrange_info, dir_name, dst_dir)

    for dst_dir, dcm_ps in record:
        for dcm_p in dcm_ps:
            fn = basename(dcm_p)
            copy(dcm_p, join(dst_dir, fn))

def show_progress(cur_done: int, total: int, status='', bar_length=60):
    """Show the progress on the terminal.
    cur_done: the number of finished work;
    totoal: the number of overall work;
    status: trivial words, str;
    bar_length: the length of bar showing on the screen, int."""
    percent = cur_done / total
    done = int(percent * bar_length)
    show = '=' * done + '/' * (bar_length - done)
    sys.stdout.write('[{}] {:.2f}% {}'.format(show, percent*100, status))
    sys.stdout.flush()


            

        

