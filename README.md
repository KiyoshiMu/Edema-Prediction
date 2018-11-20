# Edema-Prediction
## Goal
Predict the outcome of celebral edema patients from MRI
## Process
We used coronal T2-flair Digital Imaging and Communications in Medicine (DICOM) images, which are from 66 patients before and after their first therapy. All images are resized to 320 pixels in row and 320 pixels in column. The Spacings are adjusted by individual specific resizing ratio. For example, after resizing, an image with 640 pixels in row, 640 pixels in column and 0.359 * 0.359 in Spacing will become an image with 320 pixels in row, 320 pixels in column and 0.718 * 0.718 in Spacing.

The segmentation for all series of MRI images is completed by OpenCV via the combination of its bilateralFilter, threshold, getStructuringElement, morphologyEx and findContours algorithms. (The codes can be checked in Supplement Material) 

After automatic segmentation, manual proofreading in every image is done to correct mistakes. Finally, every image in every series has its specific binary mask in a 0.PNG file. The 1 in file means the pixel is in the area of interest i.e. cerebral edema, while the 0 in file is not (Figure 1).

After segmentation, the images and their correspondent masks are plugged into PyRadiomics, a flexible open-source platform capable of extracting a large panel of engineered features from medical images, under its exampleMR_5mm setting. 961 features are created, including features for Statistics, Shape, GLCM, GLRLM and GLSZM.

The effect of the therapy is defined by whether the volume of cerebral edema reduce to less than 75% of its previous volume that is before one course of treatment. If cerebral edema’s volume declines to such extent, the therapy is effective; if not, the therapy doesn’t work well.

Study has shown that 8 types of features, "ASM", "Contrast", "Correlation", "Homogeneity", "Entropy", "Variance", "Skewness", "Kurtosis", which might embrace important characters of radiomic images (Aggarwal and Agrawal, 2012). Besides, empirically, shape features like “Surface Area”, “Surface Volume Ratio” and original “Volume” might relate to the effect of the therapy. 

These 961 features were ranked via t-test measuring the linear relationship between patients’ therapy outcome and correspondent MRI image features. We selected features inside by condition that the feature belong to the 9 types above and is with p-value less than 0.1. If multiple features fit the condition but belong the same type, only the one with the least p-value is selected, since features in the same type are different in their filers and matrixes which only influence their emphasis but represent the same idiosyncrasy of images. Finally, 6 features, the wavelet-LHL_glcm_Contrast, wavelet-LHH_glcm_Correlation, wavelet-LHL_firstorder_Entropy, wavelet-LHL_glszm_GrayLevelVariance, wavelet-LHL_firstorder_Skewness and original_firstorder_Kurtosis, were selected.

Besides, our clinical features including physiological information like 'Glu', 'Chol', 'Gly', 'HDL' etc., were filtered in the same way. Their relationship with the therapy outcome was analysed by PCC. While the clinal feature with the less p-value among them has a p-value that equals to 0.162, during our testing, adding two features, BUN and PK actually improves the performance of our Logistic Regression model. Thus, three clinical features, BUN with p-value that equals to 0.218 and PK p-value that equals to 0.233 were selected (Table 1).

Selected radiomic features with their associated feature group, filter and description are summarize in Table 2. Together these features provide characters of one cerebral edema, like its smoothness, pattern diversity and other texture-like traits. 

Finally, the area under the receiver operating characteristics curves (AUCs) for primary Logistic Regression model is 0.569，0.714 and 0.767 for using selected clinical features only, using selected radiomic features only and using both selected clinical features and selected radiomic features, respectively.
