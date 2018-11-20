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

"""The script is used to segment interests from .idcom files or other forms of MRI files. 
Mooyewtsing 2018"""

def multi_read(path, file_list=list(), n=0):
    """Read files from possible directories. The architecture of directory is not certain in this project. Thus,
    I have to use a recursive way to seek files. However, I think there are other better ways.
    path (str): the parental path of one case."""
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
    """Read all dicom files from a path list. By following their instance number, 
    we can make sure the order of slides is correct.
    path (str): the parental path of one case."""
    list_of_dicom_files = multi_read(path)
    datasets = [(pydicom.read_file(f), f) for f in list_of_dicom_files]
    datasets.sort(key = lambda x: int(x[0].InstanceNumber))
    data = [x[0] for x in datasets]
    dataList = [x[1] for x in datasets]
    return data, dataList

def calibration(img):
    """Normalise the images, i.e. the brightest point (the largest value of pixles) is set as 255, 
    and the size is set as 320*320.
    img (np.array): one input image."""
    newImg = (img/cv2.minMaxLoc(img)[1]) * 255
    renewImg = newImg * (255/cv2.minMaxLoc(newImg)[1])
    temp = list(renewImg)
    tempImg = np.array(temp, dtype=np.uint8)
    resizeImg = cv2.resize(tempImg,(320,320))

    return resizeImg

def spacingInfo(path):
    """Get information about the space and so on from one case.
    path (str): a path points to a directory belonging to one case."""
    ds, _ = reading(path)
    z = ds[0].SliceThickness
    x,y = ds[0].PixelSpacing
    return [float(i) for i in [x, y, z]],{"PatientID":ds[0].PatientID, "PatientName":ds[0].PatientName, "StudyDate":ds[0].StudyDate, "PatientBirthDate":ds[0].PatientBirthDate, "PatientWeight":ds[0].PatientWeight, "PatientSex":ds[0].PatientSex}

def middle(cnt):
    """Find the center point of one contour
    cnt (np.array): the contour output by openCV."""
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
    """Only for check during coding. It's useless, now."""
    canvas = img.copy()
    plt.figure(dpi=200)
    try:
        cv2.drawContours(canvas, cnt, -1,  255,1)
    except TypeError:
        pass
    plt.imshow(canvas, cmap='gray')

def basicInfo(cnt):
    """Get the orientation information of a brain or other contours."""
    x, y = middle(cnt)
    extLeft = cnt[:, :, 0].min()
    extRight = cnt[:, :, 0].max()
    extTop = cnt[:, :, 1].min()
    extDown = cnt[:, :, 1].max()
    area = cv2.contourArea(cnt)
    return x, y, extTop, extLeft, extRight, extDown, area


def findInfoIndividual(img):
    """Find the center of one brain by a specific img."""
    # center = slices[int(len(slices)/2)].pixel_array
    _, threshed = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(30,30))
    # morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel, None, (-1,-1), 6)

    _, cnts, _ = cv2.findContours(threshed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

    return basicInfo(cnt)

def equalizeGray(img, area): # based on a nice img
    areaRatio = area / 54285
    graySum = np.sum(np.ravel(img))
    imgTEq = np.clip((img * (4030000 / graySum) * areaRatio), 0, 255)
    imgEq = list(imgTEq)
    imgEq = np.array(imgEq, dtype=np.uint8)
    return imgEq

def findEdema(img):
    """find the contours of edemaon one T2 img"""
    x, y, extTop, extLeft, extRight, _, area = findInfoIndividual(img)
    imgEq = equalizeGray(img, area)
#     clahe = cv2.createCLAHE(clipLimit=1, tileGridSize=(10,10))
    blur = cv2.bilateralFilter(imgEq,5, 10, 10)
    cntRL = []
    yDown = y + 35 # the center of skull is almost on the lowest position of brain
                   # add this empirical number to move the center on the loweat line of brain exactly 
    for i in range(2):
        temp = []
        crop = [blur[:yDown, :x], blur[:yDown, x:]][i]

#         _, threshed = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
        _, threshed = cv2.threshold(crop, 100, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morphed = cv2.morphologyEx(threshed, cv2.MORPH_ERODE, kernel, None, (-1,-1), 2)
        _, cnts, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if i == 1: # after cropping the x will change, depending on left or right
            xComp, extLeftComp, extRightComp = 0, -16, extRight-x

        else:
            xComp, extLeftComp, extRightComp= x, extLeft, x + 16
        for cnt in cnts: # filter
            x1, y1, extTop1, extLeft1, extRight1, extDown1, _ = basicInfo(cnt)
            if cv2.contourArea(cnt) > 2000 or (cv2.contourArea(cnt) > 80 and            distence(x1, y1, xComp, y) > 40 and shapeRight(cnt)            and extTop1 > extTop+5 and extDown1 < yDown-5 and extLeft1 > extLeftComp+15 and extRight1 < extRightComp-15):
                
                # some areas should be cleaned via the postion and shape
                #and extTop1 < extTop-5: and extLeft1 > extLeft+5 and extRight1 < extRight-5\
                 
                temp.append(cnt)
        cnts = temp
        
#         if len(cnts) > 0:
#             cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]
        cntRL.append(cnts)
    return conbineRL(cntRL, x), cntRL, imgEq

def conbineRL(cntCMBrl, x):
    """combine right and left contour for one cropped image"""
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
    """save only the contour-place of a image"""
    mask = np.zeros(img.shape[:2],np.uint8)
    cv2.drawContours(mask, cnts, -1, 255, -1)
    dst = cv2.bitwise_and(img, img, mask=mask)

    return dst

def creatMask(img, cnts, name, path, imgEq):
    """save only the contour-place of a image"""
    mask = np.zeros(img.shape[:2],np.uint8)
    cv2.drawContours(mask, cnts, -1, 1, -1)

    cv2.imwrite(os.path.join(path, "masks", '{}.png'.format(name)), mask)
    canvas = img.copy()
    cv2.drawContours(canvas, cnts, -1, 255, 1)
    cv2.imwrite(os.path.join(path, "origin", '{}.png'.format(name)), img)
    cv2.imwrite(os.path.join(path, "evaluation", '{}.png'.format(name)), imgEq)
    cv2.imwrite(os.path.join(path, "confirm", '{}.png'.format(name)), canvas)

def tmasks(path):
    ds, _ = reading(path)
    try:
        os.mkdir(os.path.join(path, "masks"))
        os.mkdir(os.path.join(path, "origin"))
        os.mkdir(os.path.join(path, "evaluation"))
        os.mkdir(os.path.join(path, "confirm"))
    except FileExistsError:
        print("FileExists")
    for i in range(len(ds)):
        item = ds[i]
        imgRaw = item.pixel_array
        img = calibration(imgRaw)
        name = ("%03i" % i)
        cnt, _, imgEq = findEdema(img)
        creatMask(img, cnt, name, path, imgEq)

def shapeRight(cnt):
#     peri = cv2.arcLength(cnt, True)
#     approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
    rect = cv2.minAreaRect(cnt)
    tRatio = max(rect[1]) / (min(rect[1])+0.00000001)
    return tRatio < 4

def distence(x1, y1, x2, y2):
    return sqrt((x1-x2)**2 + (y1-y2)**2)

def cleanEdema(slices):
    """collect only CMBs from all slices
    slices (list): a list of slices."""
    images = []
    for item in slices:
        img = item.pixel_array
        cnt, _, _ = findEdema(img)
        cimg = cleanImg(img, cnt)
        images.append(cimg)
        
    images = np.stack(images)
    images = images.astype(np.int16)
    
#     print(volume(modelSlices, x, y),"unit:mm^3")
    return np.array(images, dtype=np.int16)


"""The following parts are useless, now. They are used for creating the 3D models."""
def resample(images, slices, new_spacing=[1,1,1]):
    # Determine current pixel spacing
    spacing = [slices[0].SliceThickness]
    spacing.extend(slices[0].PixelSpacing)
    spacing = np.array(spacing, dtype=np.float32)

    resize_factor = spacing / new_spacing
    new_real_shape = images.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / images.shape
    new_spacing = spacing / real_resize_factor#??
    
    images = scipy.ndimage.interpolation.zoom(images, real_resize_factor, mode='nearest')
    
    return images

def plot_3d(sample, name="test"):
    p = sample.transpose(2,1,0)
    verts, faces, normals, _ = measure.marching_cubes_lewiner(p)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    # Fancy indexing: `verts[faces]` to generate a collection of triangles
    mesh = Poly3DCollection(verts[faces], alpha=0.70)
    face_color = [0.45, 0.45, 0.75]
    mesh.set_facecolor(face_color)
    ax.add_collection3d(mesh)

    ax.set_xlim(0, p.shape[0])
    ax.set_ylim(0, p.shape[1])
    ax.set_zlim(0, p.shape[2])

    plt.show()
    save(verts, normals, faces, name)

def save(verts, normals, faces, name="test"):
    faces += 1
    thefile = open('{}.obj'.format(name), 'w')
    for item in verts:
      thefile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))

    for item in normals:
      thefile.write("vn {0} {1} {2}\n".format(item[0],item[1],item[2]))

    for item in faces:
      thefile.write("f {0}//{0} {1}//{1} {2}//{2}\n".format(item[0],item[1],item[2]))  

    thefile.close()