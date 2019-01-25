import os, sys, shutil, pydicom, re
from collections import defaultdict

def move_file(dir_p, dst_p):
    fps = [os.path.join(part[0], f) for part in os.walk(dir_p) 
    for f in part[2] if f.split('.')[-1] == 'dcm']
    
    for ori in fps:
        f_n = os.path.basename(ori)
        try:
            if "FLAIR" in pydicom.dcmread(ori).SeriesDescription:
                fin = os.path.join(dst_p, f_n)
                shutil.copy(ori, fin)
        except:
            print(f_n)

def main(refs: list, begs: str, dst: str) -> None:
    id_set = set()
    rec = defaultdict(list)
    out_put = []
    out_check = set()
    near_pool = dict()
    id_data = set()

    for fn in refs:
        id_num, date_ref = fn.split('Date')
        id_set.add(id_num)
        near_pool[date_ref[:-1]] = date_ref
        id_data.add(fn)
    
    for beg in begs:
        for fn in os.listdir(beg):
            id_num = fn.split(' ')[-1]
            if id_num in id_set:
                stack = [os.path.join(beg, fn)]
                while stack:
                    cur = stack.pop()
                    for f in os.listdir(cur):
                        f_p = os.path.join(cur, f)
                        if os.path.isdir(f_p):
                            stack.append(f_p)
                            rec[id_num].append(f_p)
    
    for id_num, dates in rec.items():
        for date_raw in dates:
            date = os.path.split(date_raw)[-1]
            check = near_pool.get(date[:-1])
            if check:
                date = check
                full_name = id_num + 'Date' + date
                out_put.append((date_raw, full_name))
                d_p = os.path.join(dst, full_name)
                os.makedirs(d_p, exist_ok=True)
                move_file(date_raw, d_p)
                out_check.add(full_name)
    print(len(out_put))
    print(id_data - out_check)


def helper(group: list, beg_p: str, dst: str) -> None :
    refs = dict([(name.split('Date')[-1], name) for name in group])
    for f_n in os.listdir(beg_p):
        date = f_n.split('Date')[-1]
        if date in refs.keys():
            dst_p = os.path.join(dst, refs[date])
            os.makedirs(dst_p, exist_ok=True)
            move_file(os.path.join(beg_p, f_n), dst_p)

if __name__ == "__main__":
    mode = sys.argv[1]
    ref = sys.argv[2]
    if 'base' in mode:
        begs = (sys.argv[3], sys.argv[4])
        dst = sys.argv[5]
        main(os.listdir(ref), begs, dst)

    elif 'knowbeg' in mode:
        beg_p = sys.argv[3]
        dst = sys.argv[4]
        helper(re.findall(r'\w+', ref), beg_p, dst)

    elif 'knowref' in mode:
        begs = (sys.argv[3], sys.argv[4])
        dst = sys.argv[5]
        main(re.findall(r'\w+', ref), begs, dst)
    
    elif 'plus' in mode:
        ref_fs = set(os.listdir(ref))
        cur_fs = set(os.listdir(dst))
        begs = (sys.argv[3], sys.argv[4])
        dst = sys.argv[5]
        main(list(ref_fs-cur_fs), begs, dst)