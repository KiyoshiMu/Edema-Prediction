import cv2
import os
from os.path import join
import shutil
import argparse

def split_one(img_p, mode=1):
    img = cv2.imread(img_p, mode)
    _, w = img.shape[:2]
    middle = round(w/2)
    return img[:, :middle], img[:, middle:]

def split_id(id_dir, dst):
    for folder, mode in zip(('masks', 'evaluation'), (0, 1)):
        last_dir = join(id_dir, folder)
        id_info = os.path.basename(id_dir)
        right = join(dst, f'{id_info}_right', folder)
        left = join(dst, f'{id_info}_left', folder)
        os.makedirs(right, exist_ok=True)
        os.makedirs(left, exist_ok=True)

        xlsx = 'personInfo.xlsx'
        info = join(id_dir, xlsx)
        shutil.copy(info, join(right, xlsx))
        shutil.copy(info, join(left, xlsx))

        for f in os.listdir(last_dir):
            img_p = join(last_dir, f)
            right_img, left_img = split_one(img_p, mode)
            cv2.imwrite(join(right, f), right_img)
            cv2.imwrite(join(left, f), left_img)

def batch_split(dir_p, dst):
    for id_n in os.listdir(dir_p):
        id_dir = join(dir_p, id_n)
        split_id(id_dir, dst)

def main(processed_dir, dst):
    # execute
    batch_split(os.path.join(processed_dir, 'Before'), join(dst, 'Before'))
    batch_split(os.path.join(processed_dir, 'After'), join(dst, 'After'))
    print("IMAGE ANALYSIS COMPLETED\nMERGE RUN")

# def batch_split(id_dir, dst):
#     print(dst)
#     for bundel in os.walk(id_dir):
#         if bundel[2]:
#             copy_dst = join(dst, bundel[0].split('Processed')[-1])
#             print(copy_dst)
#             copy_dst_right = join(copy_dst, 'right')
#             copy_dst_left = join(copy_dst, 'left')
#             os.makedirs(copy_dst_right, exist_ok=True)
#             os.makedirs(copy_dst_left, exist_ok=True)

#             mode = 0 if 'masks' in bundel[0] else 1
#             for fn in bundel[2]:
#                 if os.path.splitext(fn)[-1] == 'png':
#                     img_p = join(bundel[0], fn)
#                     split_one(img_p, copy_dst, mode=mode)
#                 elif os.path.splitext(fn)[-1] == 'xlsx':
#                     shutil.copy(join(bundel[0], fn), join(copy_dst_right, fn))
#                     shutil.copy(join(bundel[0], fn), join(copy_dst_left, fn))

if __name__ == "__main__":
    argparse = argparse.ArgumentParser(description='Split one set of evaluation and masks into right and left')
    argparse.add_argument('-i', required=True)
    argparse.add_argument('-o', required=True)
    commands = argparse.parse_args()
    main(commands.i, commands.o)