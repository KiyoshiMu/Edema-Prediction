import sys
import os
import numpy
import SimpleITK, pydicom
import matplotlib.pyplot as plt
import logging, radiomics
import pandas as pd
import csv
import shutil

"""Read images and masks from processing directory after check"""
def rearrange(pathRead, destination):
    for idDate in os.listdir(pathRead):
        directory = os.path.join(pathRead, idDate)
        if os.path.isdir(directory):
            subBase = os.path.join(directory, "confirm")

            for i in range(2):
                types = ["evaluation", "masks"][i]
                path = os.path.join(directory, types)
                home = os.path.join(destination, idDate, types)
                os.makedirs(home)
                for stuff in os.listdir(path):
                    if stuff.endswith(".png"):
                        shutil.copy(os.path.join(path, stuff), home)

                subPath = os.path.join(subBase, types)
                if os.path.isdir(subPath):
                    for importance in os.listdir(subPath):
                        if importance.endswith(".png"):
                            shutil.copy(os.path.join(subPath, importance), home)

            for thing in os.listdir(directory):
                if thing.endswith(".xlsx"):
                    shutil.copy(os.path.join(directory, thing), os.path.join(destination, idDate))

def readPng(path):
    file_list = []
    for file in os.listdir(path):
        file_path = os.path.join(path,file)
        if os.path.splitext(file_path)[1] == ".png":
            file_list.append(file_path)
            
    return file_list

def output(pathRead):
    params = para_p # r"C:\Users\myq88\pyradiomics\examples\exampleSettings\exampleMR_5mm.yaml"
    extractor = radiomics.featureextractor.RadiomicsFeaturesExtractor(params)
    outPath = os.path.join(r"F:", "Output")
    os.makedirs(outPath)
    
    for idDate in os.listdir(pathRead):
        directory = os.path.join(pathRead, idDate)
        if os.path.isdir(directory):
            
            personInfo = {}
            infoJunk = pd.read_excel(os.path.join(directory, "personInfo.xlsx"))
            spacingInfo = [float(info) for info in list(infoJunk.iloc[0]) if not pd.isna(info)]
            for i in range(1, len(infoJunk.index)):
                content = [str(info) for info in list(infoJunk.iloc[i]) if not pd.isna(info)]
                personInfo[infoJunk.index[i]] = "".join(content)
            
            pMasks = os.path.join(directory, "masks")
            pOrigin = os.path.join(directory, "evaluation")
            origin = SimpleITK.ReadImage(readPng(pOrigin))
            masks = SimpleITK.ReadImage(readPng(pMasks))
            
            origin.SetSpacing(spacingInfo)
            masks.SetSpacing(spacingInfo)
            origin.SetOrigin(spacingInfo)
            masks.SetOrigin(spacingInfo)
            
            result = extractor.execute(origin, masks)
            
            keys, values = [], []

            for key, value in personInfo.items():
                keys.append(key)
                values.append(value)  

            for key, value in result.items():
                keys.append(key)
                values.append(value)
            
            with open(os.path.join(outPath, "{}.csv".format(idDate)), "w", encoding='utf8') as outfile:
                csvwriter = csv.writer(outfile)
                csvwriter.writerow(keys)
                csvwriter.writerow(values)

def mergeall(entrance): 
    allData = os.listdir(entrance)

    dfAll = [pd.read_csv(os.path.join(entrance, file)) for file in allData]

    dfConcat = pd.concat(dfAll, sort=True)

    newIndex = [word.split(".")[0] for word in allData]

    dfConcat.set_axis(newIndex, axis=0, inplace=True)

    dfConcat.to_excel(os.path.join(entrance,"allInfo.xlsx"))

def main():
    pathRead = sys.argv[1]
    destination = sys.argv[2]
    entrance = sys.argv[3]
    readyPath = destination
    # prepare
    rearrange(pathRead, destination)
    # execute
    output(readyPath)
    # combine data
    mergeall(entrance)

if __name__ == "__main__":
    para_p = sys.argv[4]
    print("pathRead = {}, destination = {}, entrance = {}, paramaters = {}\
    ".format(sys.argv[1], sys.argv[2], sys.argv[3], para_p))
    main()
