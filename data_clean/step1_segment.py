import os
import numpy
import SimpleITK, pydicom
import matplotlib.pyplot as plt
import radiomics
import helper
import pandas as pd
import csv
import shutil
import sys

def multi_read(path, file_list=list(), n=0):
    if n == 0:
        file_list.clear()
    n = 1
    # collect all dicom files under one path
    for file in os.listdir(path):
        file_path = os.path.join(path,file)
        if os.path.isdir(file_path):
            multi_read(file_path, file_list, n)
        elif os.path.splitext(file_path)[1] == "" or os.path.splitext(file_path)[1] == ".dcm":
            file_list.append(file_path)
            
    return file_list

def readPerson(personPath):
    datePath = []
    for file in os.listdir(personPath):
        file_path = os.path.join(personPath,file)
        if os.path.isdir(file_path):
            datePath.append(file_path)
    return datePath

def readPersonList(pathAll):
    personList = []
    for file in os.listdir(pathAll):
        file_path = os.path.join(pathAll,file)
        if os.path.isdir(file_path):
            personList.append(file_path)
    return personList

def selcethelperFair(oneDatePath):
    selcetList = []
    dicom_files = multi_read(oneDatePath)
    for f in dicom_files:
        if "FLAIR" in pydicom.dcmread(f).SeriesDescription:
            selcetList.append(f)
    return selcetList


def collect_info(pathAll):
    personList = readPersonList(pathAll)
    for personPath in personList:
        dateForOne = readPerson(personPath)
        for oneDatePath in dateForOne:
            try:
                selcetList = selcethelperFair(oneDatePath)
                try:
                    personInfo = littleInfo(selcetList)
                    info = "ID{}Date{}".format(personInfo["PatientID"], personInfo["StudyDate"])
                    info_list.append(info)
                    
                except AttributeError:
                    errorInfo.append(oneDatePath)
                    print(oneDatePath + " Error in littleInfo")
            except IndexError:
                nohelperFair.append(oneDatePath)
                print(oneDatePath + " No helperFair")
            
def littleInfo(selcetList):
    info = pydicom.dcmread(selcetList[0])
    z = info.SliceThickness
    x,y = info.PixelSpacing
    return {"spacingInfo":tuple([float(i) for i in [x, y, z]]),
    "PatientID":"{}".format(info.PatientID),
    "StudyDate":"{}".format(info.StudyDate)}

def bigWork(pathAll):
    personList = readPersonList(pathAll)
    for personPath in personList:
        dateForOne = readPerson(personPath)
        for oneDatePath in dateForOne:
            try:
                selcetList = selcethelperFair(oneDatePath)
                try:
                    personInfo = littleInfo(selcetList)
                    info = "ID{}Date{}".format(personInfo["PatientID"], personInfo["StudyDate"])
                    selectPath = os.path.join(os.path.split(pathAll)[0],"Processing",info)
                    
                    try:
                        os.makedirs(selectPath)
                        saveInfo = pd.DataFrame.from_dict(personInfo, orient="index")
                        saveInfo.to_excel(os.path.join(selectPath, "personInfo.xlsx"))
                    except FileExistsError:
                        print("FileExists, please clean dst")

                    for file in selcetList:
                        shutil.copy(file, selectPath)
                        
                    try:
                        helper.tmasks(selectPath)
                    except TypeError:
                        noPixel.append(oneDatePath)
                        print(oneDatePath + "No pixel data found in this dataset")
                    
                except AttributeError:
                    errorInfo.append(oneDatePath)
                    print(oneDatePath + " Error in littleInfo")
            except IndexError:
                nohelperFair.append(oneDatePath)
                print(oneDatePath + " No helperFair")

def id2name(pathAll):
    id2n = {}
    for file in os.listdir(pathAll):
        id_list = []
        file_path = os.path.join(pathAll,file)
        if os.path.isdir(file_path):

            dateForOne = readPerson(file_path)
            for oneDatePath in dateForOne:
                try:
                    selcetList = selcethelperFair(oneDatePath)
                    try:
                        info = pydicom.dcmread(selcetList[0])
                        id_list.append(info.PatientID)                   

                    except AttributeError:
                        errorInfo.append(oneDatePath)
                        print(oneDatePath + " Error in littleInfo")
                except IndexError:
                    nohelperFair.append(oneDatePath)
                    print(oneDatePath + " No helperFair")
                    
        id2n["{}".format(file)] = id_list
    return id2n

def id2name_excel(all_path):
    id2n1 = id2name(all_path)
    id2nn = {}
    for key, val in id2n1.items():
        if len(val) != 0:
            id2nn[key] = set(val)

    id2name_dict = {}
    for key, val in id2nn.items():
        for oneid in val:
            id2name_dict[oneid] = key

    id2name_df = pd.DataFrame.from_dict(id2name_dict, orient="index")
    id2name_df.to_excel("id2name_plus.xlsx")

def info_output(all_path):
    errorDf = pd.DataFrame(errorInfo)
    nohelperFairDf = pd.DataFrame(nohelperFair)
    info_list_df = pd.DataFrame(info_list)

    errorDf.set_axis(["Path"], axis=1, inplace=True)
    nohelperFairDf.set_axis(["Path"], axis=1, inplace=True)
    info_list_df.set_axis(["Path"], axis=1, inplace=True)

    errorDf.to_excel(os.path.join(os.path.split(all_path)[0],"Process", "errorInfo.xlsx"))
    nohelperFairDf.to_excel(os.path.join(os.path.split(all_path)[0],"Process", "nohelperFair.xlsx"))
    info_list_df.to_excel(os.path.join(os.path.split(all_path)[0],"Process", "info_list.xlsx"))     

def main():        
    all_path = sys.argv[1]# image paths
    id2name_excel(all_path)    
    collect_info(all_path)
    info_output(all_path)
    bigWork(all_path)

if __name__ == "__main__":
    nohelperFair = []
    errorInfo = []
    info_list = []
    noPixel = []
    main()