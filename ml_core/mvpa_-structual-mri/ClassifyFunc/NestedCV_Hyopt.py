import numpy as np
import os
from multiprocessing import Pool
from scipy.stats import ttest_ind
from sklearn.preprocessing import MinMaxScaler,StandardScaler,Normalizer
import sys
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV,RandomizedSearchCV
from sklearn.svm import SVC,LinearSVC
import scipy.io as sio
from joblib import Parallel, delayed
from sklearn.model_selection import StratifiedKFold,cross_val_score
import datetime
from sklearn.metrics import accuracy_score

from hyperopt import tpe,fmin,hp,space_eval,Trials,anneal
from functools import partial
import logging
sys.path.append('/Utility')
from Utility.PrepareData import rankTtest
from Utility.PerformanceMetrics import SenSpe,Metrics,Permute_test,allMetrics
from Utility.AnalyzeResults import DisplaySaveResults_LOOCV

def PCASVM_LOOCV(SubjectsData,SubjectsLabel,ResultantFolder):
    if not os.path.exists(ResultantFolder):
        os.makedirs(ResultantFolder)
    # the number of subjects
    SubjectQuantity = SubjectsData.shape[0]
    # generate the index of leave one out
    partitions = np.array_split(range(0, SubjectQuantity), SubjectQuantity)

    Parallel_Quantity = 2
    # start = datetime.datetime.now()
    results = Parallel(n_jobs=Parallel_Quantity, backend="threading")(
        delayed(PCASVM_LOOCV_Sub_Parallel)(SubjectsData, SubjectsLabel, partitions, cv,ResultantFolder) for cv in
        range(0,SubjectQuantity))
    # end = datetime.datetime.now()
    # runtime = end-start
    # print(runtime)
    CvIdx = np.array([item[0] for item in results])
    Accuracies = np.array([item[1] for item in results])
    TrueLabels = np.array([item[2] for item in results])
    PredictLabels = np.array([item[3] for item in results])

    ResultLOOCV = {'Accuracies':Accuracies}
    ResultantFile = ResultantFolder + 'Accuracies_LOOCV.mat'
    sio.savemat(ResultantFile,ResultLOOCV)

    # show and save results
    DisplaySaveResults_LOOCV(CvIdx, TrueLabels, PredictLabels,ResultantFolder)


    return Accuracies,PredictLabels


def PCASVM_LOOCV_Sub_Parallel(SubjectsData,SubjectsLabel,partitions,cv,ResultantFolder):

    partition = partitions[cv]
    # the sample index for train and test
    TRAIN = np.delete(partitions, partition)
    TEST = partition

    # divid train and test samples
    X_train = SubjectsData[TRAIN, :]
    y_train = SubjectsLabel[TRAIN]

    X_test = SubjectsData[TEST, :]
    y_test = SubjectsLabel[TEST]

    normalize = MinMaxScaler()
    pca = PCA(n_components=0.8)
    svc = LinearSVC(C=1,class_weight='balanced')

    pipeline = Pipeline(
        [('normalize',normalize),('reduce_dim', pca),('clf', svc)
         ])
    # pipeline = Pipeline(
    #     [('normalize',normalize),
    #      ('featureselection',pca)
    #      ('clf',svc)
    #     ])
    pipeline.fit(X_train,y_train)
    PredictLabel = pipeline.predict(X_test)
    Accuracy = accuracy_score(y_test,PredictLabel)
    print('The %d iteration!\t Accuracy=%d [Predict:%d/True:%d]' % ((cv+1),Accuracy,PredictLabel,y_test))# for LOOCV
    logging.warning('The %d iteration!\t Accuracy=%d [Predict:%d/True:%d]' % (
    (cv + 1), Accuracy, PredictLabel, y_test))  # for LOOCV

    LogFile = ResultantFolder+'worklog.txt'

    # with open(LogFile,'a') as file:
    #     for i in
    return cv+1,Accuracy,y_test,PredictLabel


def NestedCV_kFold(SubjectsData,SubjectsLabel,ResultantFolder,kFold,NormalizeFlag,NormalzeMode,clf,param_distributions, iter):
    if not os.path.exists(ResultantFolder):
        os.makedirs(ResultantFolder)
    # the number of subjects
    SubjectQuantity = SubjectsData.shape[0]
    # permute the data and label
    index = np.arange(SubjectQuantity)
    np.random.shuffle(index)
    SubjectsData = SubjectsData[index]
    SubjectsLabel = SubjectsLabel[index]

    skf = StratifiedKFold(n_splits=kFold, shuffle=True)
    trainIdx = []
    testIdx = []
    for train, test in skf.split(SubjectsData, SubjectsLabel):
        trainIdx.append(train)
        testIdx.append(test)
    print('******Nested %d Fold Hyopt CrossValidation Beginning******'%(kFold))
    logging.warning('******Nested %d Fold Hyopt CrossValidation Beginning******' % (kFold))
    Parallel_Quantity = 2
    # start = datetime.datetime.now()
    results = Parallel(n_jobs=Parallel_Quantity, backend="threading")(
        delayed(PCASVM_kFold_Sub_Parallel)(SubjectsData, SubjectsLabel, trainIdx,testIdx, cv, NormalizeFlag,NormalzeMode,clf,param_distributions) for cv in
        range(0,kFold))
    CvIdx = np.array([item[0] for item in results])
    Metrics = np.array([item[1] for item in results])

    Result = Metrics[0].mergeMetricList(Metrics)
    ResultantFile = ResultantFolder + 'Accuracies_' + str(iter) + 'iter.mat'
    sio.savemat(ResultantFile, Result.metric)
    avgMetric = Result.getAverageMetric()
    print('Average Metric= %r ' % avgMetric.metric)
    logging.warning('Average Metric= %r ' % avgMetric.metric)

    print('******Nested %d Fold Hyopt CrossValidation End******' % (kFold))
    logging.warning('******Nested %d Fold Hyopt CrossValidation End******' % (kFold))
    return Result

def PCASVM_kFold_Sub_Parallel(SubjectsData,SubjectsLabel,trainIdx,testIdx,cv,NormalizeFlag,NormalzeMode,clf_in,tuned_parameters):
    import copy
    clf = copy.deepcopy(clf_in)
    TRAIN = trainIdx[cv]
    TEST = testIdx[cv]

    # divid train and test samples
    X_train = SubjectsData[TRAIN, :]
    y_train = SubjectsLabel[TRAIN]

    X_test = SubjectsData[TEST, :]
    y_test = SubjectsLabel[TEST]


    # normalization
    # if NormalizeFlag==True:
    #     if NormalzeMode == 'MinMaxScaler':
    #         normalize = MinMaxScaler()
    #     elif NormalzeMode == 'StandardScaler':
    #         normalize = StandardScaler()
    #     elif NormalzeMode == 'Normalizer':
    #         normalize = Normalizer()
    #     X_train = normalize.fit_transform(X_train)
    #     X_test = normalize.transform(X_test)

    trials =Trials()
    best = fmin(partial(HyoptCV,X=X_train,y=y_train,clf=clf),space=tuned_parameters,algo=tpe.suggest,max_evals=1,trials=trials)#anneal.suggest  tpe.suggest
    best_params = space_eval(tuned_parameters, best)
    print('The %d fold!\tbest_params:%r'%((cv+1),best_params))
    logging.warning('The %d fold!\tbest_params:%r'%((cv+1),best_params))

    clf.set_params(**best_params)
    clf.fit(X_train,y_train)
    PredictLabel_test = clf.predict(X_test)
    PredictLabel_train = clf.predict(X_train)

    Accuracy_test = accuracy_score(y_test,PredictLabel_test)
    Sensitivity_test, Specifity_test = SenSpe(y_test, PredictLabel_test)
    Accuracy_train = accuracy_score(y_train,PredictLabel_train)
    Sensitivity_train, Specifity_train = SenSpe(y_train, PredictLabel_train)
    F1, Precision, Recall, Auc = Metrics(y_test, PredictLabel_test)
    _, Permute_value = Permute_test(clf, X_train, y_train)
    metric = allMetrics(Accuracy_test=Accuracy_test, Sensitivity_test=Sensitivity_test, Specifity_test=Specifity_test, \
                        Accuracy_train=Accuracy_train, Sensitivity_train=Sensitivity_train, Specifity_train=Specifity_train,F1=F1,\
                        Precision=Precision, Recall=Recall, Auc=Auc, Permute_value=Permute_value)

    print('The %d fold!\t metric=%r' % ((cv + 1), metric.metric))
    logging.warning('The %d fold!\t metric=%r' % ((cv + 1), metric.metric))

    return cv + 1, metric

def HyoptCV(params,X,y,clf):
    clf.set_params(**params)
    cv = StratifiedKFold(n_splits=5, shuffle=True)
    score = cross_val_score(clf,X,y,cv=cv,scoring='accuracy',n_jobs=-1)
    return 1-score.mean()