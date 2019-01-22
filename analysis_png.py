import sys
import os
import numpy
import SimpleITK, pydicom
import matplotlib.pyplot as plt
import radiomics
import pandas as pd
import csv
import argparse
from tools import show_progress

def readPng(dir_p):
    file_list = [os.path.join(dir_p, fn) for fn in os.listdir(dir_p) if fn[-4:] == '.png']
    return file_list

def prepare(directory):
    personInfo = {}
    infoJunk = pd.read_excel(os.path.join(directory, "personInfo.xlsx"))
    spacingInfo = [float(info) for info in list(infoJunk.iloc[0]) if not pd.isna(info)]
    for i in range(1, len(infoJunk.index)):
        content = [str(info) for info in list(infoJunk.iloc[i]) if not pd.isna(info)]
        personInfo[infoJunk.index[i]] = "".join(content)
    
    origin = SimpleITK.ReadImage(readPng(os.path.join(directory, "masks")))
    masks = SimpleITK.ReadImage(readPng(os.path.join(directory, "evaluation")))
    
    origin.SetSpacing(spacingInfo)
    masks.SetSpacing(spacingInfo)
    origin.SetOrigin(spacingInfo)
    masks.SetOrigin(spacingInfo)

    return origin, masks, personInfo

def output(extractor, directory, outPath):
    if os.path.isdir(directory):
        origin, masks, personInfo = prepare(directory)
        result = extractor.execute(origin, masks)
        
        keys, values = [], []
        for key, value in personInfo.items():
            keys.append(key)
            values.append(value)
        for key, value in result.items():
            keys.append(key)
            values.append(value)
        idDate = os.path.basename(directory)
        with open(os.path.join(outPath, f"{idDate}.csv"), "w", encoding='utf8') as outfile:
            csvwriter = csv.writer(outfile)
            csvwriter.writerow(keys)
            csvwriter.writerow(values)

def batch_out(processed_dir, dst):
    params = 'MR_5mm.yaml'
    extractor = radiomics.featureextractor.RadiomicsFeaturesExtractor(params)
    outPath = os.path.join(dst, "output")
    os.makedirs(outPath, exist_ok=True)
    work_load = os.listdir(processed_dir)
    for count_done, idDate in enumerate(work_load, 1):
        directory = os.path.join(processed_dir, idDate)
        output(extractor, directory, outPath)
        show_progress(count_done, len(work_load), "RUNNING")

def mergeall(dst):
    entrance = os.path.join(dst, 'output')
    allData = [fn for fn in os.listdir(entrance) if fn[-4:]=='.csv']
    dfAll = [pd.read_csv(os.path.join(entrance, fn)) for fn in allData]
    dfConcat = pd.concat(dfAll, sort=True)
    newIndex = [word.split(".")[0] for word in allData]
    dfConcat.set_axis(newIndex, axis=0, inplace=True)
    dfConcat.to_excel(os.path.join(dst,"allInfo.xlsx"))

def main(processed_dir, dst):
    # execute
    batch_out(os.path.join(processed_dir, 'Before'), dst)
    batch_out(os.path.join(processed_dir, 'After'), dst)
    print("IMAGE ANALYSIS COMPLETED\nMERGE RUN")
    # combine data
    mergeall(dst)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analysis processed images via pyRadiomics')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    command = parser.parse_args()
    main(command.input, command.output)