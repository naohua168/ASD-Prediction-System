import os
import random as rd

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind


def load3DData(dataDir, sortBegin, sortEnd):
    # *******************************************************
    # input:
    # load neuroimaging data
    # dataDir : the data directory
    # locate the number in file name to sort files
    # sortBegin : the begin location of the number
    # sortEnd : the end location of the number
    # output:
    # data : the data with the shape of [M,N,K,L]
    # [M,N,K] - the 3D of structual MRI
    # L - the number of data
    # *******************************************************

    # list files and sort them
    fileList = []
    for file in os.listdir(dataDir):
        if file.endswith('.nii'):
            fileList.append(file)
    fileList.sort(key=lambda x: int(x[sortBegin:sortEnd]))

    # load 3D data
    img = nib.load(dataDir + '/' + fileList[0])
    imgData = img.get_data()
    print(np.shape(imgData))
    data = np.zeros([imgData.shape[0], imgData.shape[1], imgData.shape[2], len(fileList)])
    data[:, :, :, 0] = imgData
    for i in range(1, len(fileList)):
        img = nib.load(dataDir + '/' + fileList[i])
        imgData = img.get_data()
        data[:, :, :, i] = imgData
    return data


def load2DData(DataDir, Mask, suffer=0, load=0, sortBegin=None, sortEnd=None):
    # *******************************************************
    # input:
    # load neuroimaging data
    # dataDir : the data directory
    # locate the number in file name to sort files
    # sortBegin : the begin location of the number
    # sortEnd : the end location of the number
    # output:
    # data : the data with the shape of [L,M*N*K]
    # [L] - the 3D of structual MRI
    # M*N*K - the number of data
    # *******************************************************

    # list files and sort them
    FileList = []
    for file in os.listdir(DataDir):
        if file.endswith('.nii'):
            # print(file)
            FileList.append(DataDir + '/' + file)
    if (sortBegin != None and sortEnd != None):
        FileList.sort(key=lambda x: x[:-4])
    # else:
    #     FileList.sort(key=lambda x: int(x[sortBegin:sortEnd]))

    return loadFileList2DData(FileList, Mask, suffer, load), FileList


# suffer=0 不打乱，=2打乱X
# load=0，表示根据mask模板加载全部数据
# load=1表示mask为脑区模板，根据脑区模板返回每个脑区的中值
# load=2表示mask为脑区模板，根据脑区模板返回每个脑区的均值
def loadFileList2DData(FileList, Mask, suffer=0, load=0):
    # load 2D data
    if (load == 0):
        FeatureQuantity = np.sum(Mask != 0)
        Data = np.zeros([len(FileList), FeatureQuantity])
        for i in range(0, len(FileList)):
            Img = nib.load(FileList[i])
            ImgData = Img.get_data()
            Data[i, :] = np.transpose(ImgData[np.where(Mask != 0)])
    elif (load == 1):
        FeatureQuantity = int(np.max(Mask))
        Data = np.zeros([len(FileList), FeatureQuantity])
        for i in range(0, len(FileList)):
            Img = nib.load(FileList[i])
            ImgData = Img.get_data()
            for j in range(1, FeatureQuantity + 1):
                Data[i, j - 1] = np.median(ImgData[np.where(Mask == j)])
    if (suffer == 2):
        for index in range(FeatureQuantity):
            # x = random.randint(0,FeatureQuantity-1)
            rd.shuffle(Data[:, index])
    return Data


def loadMask(maskDir):
    # *******************************************************
    # input:
    # load neuroimaging mask
    # maskDir : the mask directory
    # output:
    # the mask data
    # *******************************************************
    maskImg = nib.load(maskDir)
    return maskImg.get_data()


def rankTtest(SubjectData, SubjectLabel, Pval):
    # *******************************************************
    # input:
    # SubjectData
    # SubjectLabel
    # Pval: the threshold of p value
    # output:
    # the ttest mask
    # *******************************************************
    Group1Data = SubjectData[np.where(SubjectLabel == -1)[0], :]
    Group2Data = SubjectData[np.where(SubjectLabel == 1)[0], :]

    T, P = ttest_ind(Group1Data, Group2Data, axis=0, equal_var=False, nan_policy='omit')
    P[np.isnan(P)] = 0
    TtestMask = np.zeros_like(P)
    TtestMask[np.where(P <= Pval)] = 1
    # print(np.sum(TtestMask))
    return TtestMask


def LoadMultiData(dataDirs, GroupName, GreyMask, suffer=0, load=0):
    Group1DataList = []
    Group2DataList = []
    SubjectsDataList = []
    SubjectsLabelList = []
    Filelist1 = []
    Filelist2 = []
    for dataDir in dataDirs:
        Group1Dir = dataDir + GroupName[0]
        Group2Dir = dataDir + GroupName[1]
        Group1Data, Flist1 = load2DData(Group1Dir, GreyMask, suffer, load, sortBegin=8, sortEnd=9)
        Group2Data, Flist2 = load2DData(Group2Dir, GreyMask, suffer, load, sortBegin=10, sortEnd=12)
        SubjectsData = np.concatenate((Group1Data, Group2Data), axis=0)

        Group1Label = np.ones([Group1Data.shape[0]])
        Group2Label = np.zeros([Group2Data.shape[0]])
        SubjectsLabel = np.concatenate((Group1Label, Group2Label), axis=0)

        Group1DataList.append(Group1Data)
        Group2DataList.append(Group2Data)
        SubjectsDataList.append(SubjectsData)
        SubjectsLabelList.append(SubjectsLabel)
        Filelist1 = Filelist1 + Flist1
        Filelist2 = Filelist2 + Flist2

    return Group1DataList, Group2DataList, SubjectsDataList, SubjectsLabelList, Filelist1, Filelist2


def ConcateSitesData(SubjectsDataLists, SubjectsLabelLists, Group1DataList, Group2DataList):
    SubjectsData = SubjectsDataLists[0]
    SubjectsLabel = SubjectsLabelLists[0]
    Group1Data = Group1DataList[0]
    Group2Data = Group2DataList[0]
    length = len(SubjectsDataLists)
    for i in range(1, length):
        SubjectsData = np.concatenate((SubjectsData, SubjectsDataLists[i]), axis=0)
        SubjectsLabel = np.concatenate((SubjectsLabel, SubjectsLabelLists[i]), axis=0)
        Group1Data = np.concatenate((Group1Data, Group1DataList[i]), axis=0)
        Group2Data = np.concatenate((Group2Data, Group2DataList[i]), axis=0)
    return Group1Data, Group2Data, SubjectsData, SubjectsLabel


######interface for load multi site 2D data ######
def LoadMultiSiteDataByMask(GreyMaskDir, DataDir, GroupName, suffer=0, load=0):
    GreyMask = loadMask(GreyMaskDir)
    Group1DataList, Group2DataList, SubjectsDataList, SubjectsLabelList, Filelist1, Filelist2 = LoadMultiData(DataDir,
                                                                                                              GroupName,
                                                                                                              GreyMask,
                                                                                                              suffer,
                                                                                                              load)
    Group1Data, Group2Data, SubjectsData, SubjectsLabel = ConcateSitesData(SubjectsDataList, SubjectsLabelList,
                                                                           Group1DataList, Group2DataList)
    return Group1Data, Group2Data, SubjectsData, SubjectsLabel, Filelist1, Filelist2


###################for fold multi site functions  begin#######
def getSiteFileList(siteList, GroupName):
    FileList = []
    for DataDir in siteList:
        for grp in GroupName:
            Data_path = r"%s/%s/" % (DataDir, grp)
            for file in os.listdir(Data_path):
                if file.endswith('.nii'):
                    FileList.append(Data_path + file)
    return FileList


def getFileListInFold(DataDirList, GroupName, fold=5, random_state=2020):
    FileListFold = []
    for i in range(fold):
        FileListFold.append([])
    for DataDir in DataDirList:
        FileList_site = {}
        for grp in GroupName:
            Data_path = r"%s/%s/" % (DataDir, grp)
            print(Data_path)
            FileList = []
            for file in os.listdir(Data_path):
                if file.endswith('.nii'):
                    FileList.append(Data_path + file)
            FileList_site[grp] = FileList
        SubjectsData = np.concatenate((FileList_site[GroupName[0]], FileList_site[GroupName[1]]), axis=0)
        Group1Label = np.ones([len(FileList_site[GroupName[0]])])
        Group2Label = np.zeros([len(FileList_site[GroupName[1]])])
        SubjectsLabel = np.concatenate((Group1Label, Group2Label), axis=0)

        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=fold, random_state=random_state, shuffle=True)
        i = 0
        for train_index, test_index in skf.split(SubjectsData, SubjectsLabel):
            # 将分好的这个site放入折里
            X_test = SubjectsData[test_index]
            FileListFold[i].extend(X_test)
            i += 1
    return FileListFold


def getLabelByList(FileList, GroupName):
    LabelList = []
    for i in range(0, len(FileList)):
        if GroupName[0] in FileList[i]:
            LabelList.append(1)
        if GroupName[1] in FileList[i]:
            LabelList.append(0)
    return LabelList


def LoadFileListData(GreyMaskDir, FileList, GroupName):
    GreyMask = loadMask(GreyMaskDir)
    SubjectsDataList = loadFileList2DData(FileList, GreyMask)
    SubjectsLabelList = getLabelByList(FileList, GroupName)
    return SubjectsDataList, SubjectsLabelList


###################for fold multi site functions  end  LoadFileListData for interface#######

##################de center  https://github.com/Warvito/neurocombat_sklearn#######################33
# def DecenterCombatModelNested(data,covars,col):
#     from neurocombat_sklearn import CombatModel
#     from sklearn.model_selection import train_test_split
#     model = CombatModel()
#     args=[]
#     for i in range(len(col)):
#         args.append(covars[col[i]])
#     model.fit(data, *args)
#     data_combat = model.transform(data, *args)
#     return  data_combat

def DecenterCombatModelSimple(data_train, data_test, covars_train, covars_test, col):
    from neurocombat_sklearn import CombatModel
    args_train = []
    args_test = []
    for i in range(len(col)):
        args_train.append(covars_train[col[i]])
        args_test.append(covars_test[col[i]])

    # Creating model
    model = CombatModel()

    # Fitting the model and transforming the training set
    X_train_harmonized = model.fit_transform(data_train,
                                             *args_train)

    # Harmonize test set using training set fitted parameters
    X_test_harmonized = model.transform(data_test,
                                        *args_test)

    return X_train_harmonized, X_test_harmonized


################https://github.com/Jfortin1/neuroCombat/tree/ac82a067412078680973ddf72bd634d51deae735
def DecenterCombatModelNested(data, covars, cols):
    from neuroCombat import neuroCombat
    data = np.transpose(data)
    # To specify names of the variables that are categorical:
    categorical_cols = ['type']

    # To specify the name of the variable that encodes for the scanner/batch covariate:
    batch_col = 'batch'
    data_combat = data
    for batch_col in cols:
        # Harmonization step:
        data_combat = neuroCombat(dat=data_combat,
                                  covars=covars,
                                  batch_col=batch_col,
                                  categorical_cols=categorical_cols)["data"]

    return data_combat.np.transpose(data_combat)


def subDecenterRegress(nifti_list_train, nifti_list_test, nifti_list_train_nc, covars_train, covars_test,
                       covars_train_nc, GreyMaskDir, to_save_data=False):
    list_train = list(nifti_list_train["PATH"])
    list_test = list(nifti_list_test["PATH"])
    list_train_nc = list(nifti_list_train_nc["PATH"])
    GreyMask = loadMask(GreyMaskDir)
    SubjectsDataList_train = loadFileList2DData(list_train, GreyMask)
    SubjectsDataList_train_nc = loadFileList2DData(list_train_nc, GreyMask)
    SubjectsDataList_test = loadFileList2DData(list_test, GreyMask)
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(covars_train_nc.values, SubjectsDataList_train_nc)
    Predict_train = model.predict(covars_train.values)
    Predict_test = model.predict(covars_test.values)
    Data_train = SubjectsDataList_train - Predict_train
    Data_test = SubjectsDataList_test - Predict_test
    return Data_train, Data_test


def subDecenterCombat(nifti_list_train, nifti_list_test, nifti_list_train_nc, covars_train, covars_test,
                      covars_train_nc, GreyMaskDir, to_save_data=False):
    from neuroHarmonize.harmonizationNIFTI import createMaskNIFTI
    import neuroHarmonize as nh
    from neuroHarmonize.harmonizationNIFTI import applyModelNIFTIs
    from neuroHarmonize.harmonizationNIFTI import flattenNIFTIs

    nifti_avg, nifti_mask, affine = createMaskNIFTI(nifti_list_train_nc, threshold=0)

    nifti_array = flattenNIFTIs(nifti_list_train_nc, 'thresholded_mask.nii.gz')

    my_model, nifti_array_adj = nh.harmonizationLearn(nifti_array, covars_train_nc)
    # nh.saveHarmonizationModel(my_model, 'MY_MODEL')
    #
    # # load pre-trained model
    # my_model = nh.loadHarmonizationModel('MY_MODEL')
    data_train = applyModelNIFTIs(covars_train, my_model, nifti_list_train, 'thresholded_mask.nii.gz', to_save_data)
    data_test = applyModelNIFTIs(covars_test, my_model, nifti_list_test, 'thresholded_mask.nii.gz', to_save_data)
    Mask = loadMask(GreyMaskDir)

    FeatureQuantity = np.sum(Mask != 0)
    Data_train = np.zeros([len(nifti_list_train), FeatureQuantity])
    for i in range(0, len(nifti_list_train)):
        datai = data_train[:, :, :, i]
        Data_train[i, :] = np.transpose(datai[np.where(Mask != 0)])

    Data_test = np.zeros([len(nifti_list_test), FeatureQuantity])
    for i in range(0, len(nifti_list_test)):
        datai = data_test[:, :, :, i]
        Data_test[i, :] = np.transpose(datai[np.where(Mask != 0)])

    return Data_train, Data_test


def getNormalTrain(nifti_list_train, covars_train, nc_type=2):
    nifti_list_train_nc = nifti_list_train[covars_train["type"] == nc_type]
    nifti_list_train_nc = nifti_list_train_nc.reset_index(drop=True)
    covars_train_nc = covars_train[covars_train["type"] == nc_type]
    covars_train_nc = covars_train_nc.reset_index(drop=True)
    return nifti_list_train_nc, covars_train_nc


def Decenter_select_covars(nifti_list_train, nifti_list_test, covars_train, covars_test, cols, GreyMaskDir,
                           to_save_data=False):
    df_covars_train = pd.DataFrame()
    df_covars_test = pd.DataFrame()
    df_covars_train_nc = pd.DataFrame()
    nifti_list_train_nc, covars_train_nc = getNormalTrain(nifti_list_train, covars_train)
    for col in cols:
        df_covars_train[col] = covars_train[col]
        df_covars_test[col] = covars_test[col]
        df_covars_train_nc[col] = covars_train_nc[col]

    return nifti_list_train_nc, df_covars_train, df_covars_test, df_covars_train_nc


def DecenterFileListToDataByCombat(nifti_list_train, nifti_list_test, covars_train, covars_test, cols, GreyMaskDir,
                                   to_save_data=False):
    nifti_list_train_nc, df_covars_train, df_covars_test, df_covars_train_nc = \
        Decenter_select_covars(nifti_list_train, nifti_list_test, covars_train, covars_test, cols, GreyMaskDir,
                               to_save_data)
    return subDecenterCombat(nifti_list_train, nifti_list_test, nifti_list_train_nc, df_covars_train, df_covars_test,
                             df_covars_train_nc, GreyMaskDir, to_save_data)


def DecenterFileListToDataByRegress(nifti_list_train, nifti_list_test, covars_train, covars_test, cols, GreyMaskDir,
                                    to_save_data=False):
    nifti_list_train_nc, df_covars_train, df_covars_test, df_covars_train_nc = \
        Decenter_select_covars(nifti_list_train, nifti_list_test, covars_train, covars_test, cols, GreyMaskDir,
                               to_save_data)
    return subDecenterRegress(nifti_list_train, nifti_list_test, nifti_list_train_nc, df_covars_train, df_covars_test,
                              df_covars_train_nc, GreyMaskDir, to_save_data)
