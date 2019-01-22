import cv2
import pydicom
import dicom_numpy
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure, morphology
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import scipy.ndimage
from math import sqrt
from functools import reduce
import os
from os.path import dirname as par
import sys

"""See details from helper.py. Most of codes are the same."""

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

def reading(path):
    # read all dicom files from a path list
    list_of_dicom_files = multi_read(path)
    datasets = [(pydicom.read_file(f), f) for f in list_of_dicom_files]
    datasets.sort(key = lambda x: int(x[0].InstanceNumber))
    data = [x[0] for x in datasets]
    dataList = [x[1] for x in datasets]
    return data, dataList

def calibration(img):
    # create a CLAHE object (Arguments are optional).
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#     cl1 = clahe.apply(img)
    newImg = (img/cv2.minMaxLoc(img)[1]) * 255
    renewImg = newImg * (255/cv2.minMaxLoc(newImg)[1])
    
    temp = list(renewImg)
    tempImg = np.array(temp, dtype=np.uint8)
    resizeImg = cv2.resize(tempImg,(320,320))

    return resizeImg

def spacingInfo(path):
    ds, _ = reading(path)
    z = ds[0].SliceThickness
    x,y = ds[0].PixelSpacing
    return [float(i) for i in [x, y, z]],{"PatientID":ds[0].PatientID, "PatientName":ds[0].PatientName, "StudyDate":ds[0].StudyDate, "PatientBirthDate":ds[0].PatientBirthDate, "PatientWeight":ds[0].PatientWeight, "PatientSex":ds[0].PatientSex}

def middle(cnt):
    # find the center point of one contour
    M = cv2.moments(cnt)
    try:
        cx = int(M['m10']/M['m00'])
    except ZeroDivisionError:
        cx = 0
    try:
        cy = int(M['m01']/M['m00'])
    except ZeroDivisionError:
        cy = 0
    return cx, cy

def show(img, cnt=None):
    canvas = img.copy()
    plt.figure(dpi=200)
    try:
        cv2.drawContours(canvas, cnt, -1,  255,1)
    except TypeError:
        pass
    plt.imshow(canvas, cmap='gray')

def basicInfo(cnt):
    x, y = middle(cnt)
    extLeft = cnt[:, :, 0].min()
    extRight = cnt[:, :, 0].max()
    extTop = cnt[:, :, 1].min()
    extDown = cnt[:, :, 1].max()
    area = cv2.contourArea(cnt)
    return x, y, extTop, extLeft, extRight, extDown, area

def findInfoIndividual(img):
    # find the center of one brain by all slices
#     center = slices[int(len(slices)/2)].pixel_array
    _, threshed = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)

    _, cnts, _ = cv2.findContours(threshed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

    return basicInfo(cnt)

def equalizeGray(img, area): # based on a nice img
    areaRatio = area / 54285
    graySum = np.sum(np.ravel(img))
    imgTEq = np.clip((img * (4020000 / graySum) * areaRatio), 0, 255)
    imgEq = list(imgTEq)
    imgEq = np.array(imgEq, dtype=np.uint8)
    return imgEq

def findEdema(img, thre=100, erode=2, morphT=3, size=3, eq=True, morph=False):
    # find the contours of edemaon one T2 img
    x, y, extTop, extLeft, extRight, _, area = findInfoIndividual(img)
    y = 190
    if eq:
        imgEq = equalizeGray(img, area)
    else:
        imgEq = img.copy()
#     clahe = cv2.createCLAHE(clipLimit=1, tileGridSize=(10,10))
    blur = cv2.bilateralFilter(imgEq,5, 10, 10)
    cntRL = []
    yDown = y + 35 # the center of skull is almost on the lowest position of brain
                   # add this empirical number to move the center on the loweat line of brain exactly 
    for i in range(2):
        temp = []
        crop = [blur[:yDown, :x], blur[:yDown, x:]][i]

#         _, threshed = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
        _, threshed = cv2.threshold(crop, thre, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        morphed = cv2.morphologyEx(threshed, cv2.MORPH_ERODE, kernel, None, (-1,-1), erode)
        if morph:
            morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel, None, (-1,-1), morphT)
        _, cnts, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if i == 1: # after cropping the x will change, depending on left or right
            xComp, extLeftComp, extRightComp = 0, 0, extRight-x

        else:
            xComp, extLeftComp, extRightComp= x, extLeft, x
        for cnt in cnts: # filter
            x1, y1, extTop1, extLeft1, extRight1, extDown1, _ = basicInfo(cnt)
            if (cv2.contourArea(cnt) > 1800 and extTop1 > extTop +20) or (cv2.contourArea(cnt) > 80 and            distence(x1, y1, xComp, y) > 0 and shapeRight(cnt)            and extTop1 > extTop+10 and extDown1 < yDown-5 and extLeft1 > extLeftComp+20 and extRight1 < extRightComp-20):
                
                # some areas should be cleaned via the postion and shape # 
                #and extTop1 < extTop-5: and extLeft1 > extLeft+5 and extRight1 < extRight-5\
                 
                temp.append(cnt)
        cnts = temp
        
#         if len(cnts) > 0:
#             cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

        cntRL.append(cnts)

    return conbineRL(cntRL, x), cntRL, imgEq

def conbineRL(cntCMBrl, x):
    # combine right and left contour for one cropped image
    if cntCMBrl[1] == None and cntCMBrl[0] == None:
        new = None
    elif cntCMBrl[1] == None and cntCMBrl[0] != None:
        new = cntCMBrl[0]
    elif cntCMBrl[1] != None and cntCMBrl[0] == None:
        new = cntCMBrl[1]
    else:
        cntCMBrl[1] = [cnt+np.array([x, 0]) for cnt in cntCMBrl[1]]
        new = cntCMBrl[0] + cntCMBrl[1]

    return new

def cleanImg(img, cnts):
    # save only the contour-place of a image
    mask = np.zeros(img.shape[:2],np.uint8)
    cv2.drawContours(mask, cnts, -1, 255, -1)
    dst = cv2.bitwise_and(img, img, mask=mask)

    return dst

def creatMask(img, cnts, name, path, imgEq):
    # save only the contour-place of a image
    mask = np.zeros(img.shape[:2],np.uint8)
    cv2.drawContours(mask, cnts, -1, 1, -1)

    cv2.imwrite(os.path.join(path, "masks", '{}.png'.format(name)), mask)
    canvas = img.copy()
    cv2.drawContours(canvas, cnts, -1, 255, 1)
    cv2.imwrite(os.path.join(path, "origin", '{}.png'.format(name)), img)
    cv2.imwrite(os.path.join(path, "evaluation", '{}.png'.format(name)), imgEq)
    cv2.imwrite(os.path.join(path, "confirm", '{}.png'.format(name)), canvas)

def shapeRight(cnt):
#     peri = cv2.arcLength(cnt, True)
#     approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
    rect = cv2.minAreaRect(cnt)
    tRatio = max(rect[1]) / (min(rect[1])+0.00000001)
    return tRatio < 4

def distence(x1, y1, x2, y2):
    return sqrt((x1-x2)**2 + (y1-y2)**2)

def maskOne(path, thre=100, erode=2, size=3, morph=True, morphT=3):
    nameFull = os.path.basename(path)
    imgRaw = cv2.imread(os.path.join(par(par(path)), "origin", nameFull))
    try:
        pathi = par(path)
        os.mkdir(os.path.join(pathi, "masks"))
        os.mkdir(os.path.join(pathi, "origin"))
        os.mkdir(os.path.join(pathi, "evaluation"))
        os.mkdir(os.path.join(pathi, "confirm"))
    except FileExistsError:
        print("File Exists")
    img = cv2.cvtColor(imgRaw, cv2.COLOR_BGR2GRAY)
    name = nameFull.split(".")[0]
    cnt, _, imgEq = findEdema(img, thre=thre, erode=erode, size=size, morph=morph, morphT=morphT)
    show(img, cnt)
    creatMask(img, cnt, name, pathi, imgEq)

if  __name__ == "__main__":
    print("thre=95, erode=1, size=1, morph=True, morphT=0")
    tpath = sys.argv[1]
    maskOne(tpath, thre=95, erode=1, size=1, morph=True, morphT=0)

# for i in range(19, 26, 2):
#     name = ("%03i" % i)
#     tpath = .\{}.png".format(name)
#     maskOne(tpath, thre=140, erode=1, size=1, morph=True, morphT=0)