import os
from shutil import copy
from os.path import join, basename, splitext
import SimpleITK, pydicom
import pickle
from collections import defaultdict
import sys
import pandas as pd
from tabulate import tabulate

def load_pickle(pkl_path) -> dict:
    with open(pkl_path, 'rb') as temp:
        container = pickle.load(temp)
    return container

def save_pickle(container, name, dst) -> None:
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
                save_pickle(arrange_info, dir_name, dst_dir)

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
    
def feature_rough_sel(data):
    bio_info = ("ASM", "Contrast", "Correlation", "Homogeneity", "Entropy", "Variance", "Skewness", "Kurtosis")
    selected_feature = list(filter_df(data, bio_info))
    return selected_feature

def clean_df(data, selected_feature=None, key='original_shape_VoxelVolume'):
    data = data.sort_index()
    # here the date is also sorted
    # from the paper [\cite] the following features may have biological meanings
    if not selected_feature:
        selected_feature = feature_rough_sel(data)
    sel_data = data.loc[:, selected_feature]
    sel_data['id'], _ = zip(*[v.split('Date') for v in sel_data.index.tolist()])

    before_data = sel_data.iloc[::2, :]
    after_data = sel_data.iloc[1::2, :]

    v_before = data.loc[before_data.index, key]
    v_after = data.loc[after_data.index, key]
    y = y_creator(v_before, v_after, before_data['id'])
    x = before_data.set_index('id')
    print(f'{x.shape[0]} samples, {x.shape[1]} features')
    return x, y

def y_creator(v_before, v_after, idxs):
    ratio = v_after.values / v_before.values
    y_change = ratio -1
    y = pd.DataFrame({'volume before':v_before.values, 'volume after':v_after.values, 'effectiveness':y_change<-0.25},
            index = idxs)
    return y

def filter_df(data, sel_info):
    # select realted columns
    func_filter = lambda x : any([info == x.split('_')[-1] for info in sel_info])
    columns = filter(func_filter, data.columns.tolist())
    return columns  

def markdown_tabel(content, dst):
    with open(os.path.join(dst, 'mark_down.txt'),'a') as md:
        md.write(tabulate(content, tablefmt="pipe", headers="keys"))
        md.write('\n')