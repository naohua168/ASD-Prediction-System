import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler,StandardScaler,Normalizer
import sys
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC,LinearSVC
import scipy.io as sio
from joblib import Parallel, delayed
from sklearn.model_selection import StratifiedKFold,cross_val_score
import datetime
from sklearn.metrics import accuracy_score

from hyperopt import tpe,fmin,hp,space_eval,Trials
from functools import partial
import optuna

sys.path.append('/Utility')
from Utility.PrepareData import rankTtest
from Utility.PerformanceMetrics import SenSpe, Metrics, allMetrics
import logging
from Utility.AnalyzeResults import DisplaySaveResults_LOOCV


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


    skf = StratifiedKFold(n_splits=kFold,shuffle=True)
    trainIdx = []
    testIdx = []
    for train, test in skf.split(SubjectsData,SubjectsLabel):
        trainIdx.append(train)
        testIdx.append(test)
    print('******Nested %d Fold Optuna CrossValidation Beginning******' % (kFold))

    logging.warning('******Nested %d Fold Optuna CrossValidation Beginning******' % (kFold))
    Parallel_Quantity = 2
    # start = datetime.datetime.now()
    results = Parallel(n_jobs=Parallel_Quantity, backend="threading")(
        delayed(NestedCV_kFold_Sub_Parallel)(SubjectsData, SubjectsLabel, trainIdx,testIdx, cv, NormalizeFlag,NormalzeMode,clf,param_distributions) for cv in
        range(0,kFold))
    CvIdx = np.array([item[0] for item in results])
    Metrics = np.array([item[1] for item in results])

    Result = Metrics[0].mergeMetricList(Metrics)
    ResultantFile = ResultantFolder + 'Accuracies_' + str(iter) + 'iter.mat'
    sio.savemat(ResultantFile, Result.metric)
    avgMetric = Result.getAverageMetric()
    print('Average Metric= %r ' % avgMetric.metric)
    logging.warning('Average Metric= %r ' % avgMetric.metric)

    print('******Nested %d Fold Optuna CrossValidation End******' % (kFold))
    logging.warning('******Nested %d Fold Optuna CrossValidation End******' % (kFold))
    return Result

def NestedCV_kFold_Sub_Parallel(SubjectsData,SubjectsLabel,trainIdx,testIdx,cv,NormalizeFlag,NormalzeMode,clf_in,tuned_parameters):
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
    # if NormalizeFlag == True:
    #     if NormalzeMode == 'MinMaxScaler':
    #         normalize = MinMaxScaler()
    #     elif NormalzeMode == 'StandardScaler':
    #         normalize = StandardScaler()
    #     elif NormalzeMode == 'Normalizer':
    #         normalize = Normalizer()
    #     X_train = normalize.fit_transform(X_train)
    #     X_test = normalize.transform(X_test)

    optuna_search = optuna.integration.OptunaSearchCV(
        clf, tuned_parameters, cv=StratifiedKFold(n_splits=5,shuffle=True),n_trials=10, timeout=600, verbose=2,max_iter=10,scoring='accuracy'
    )
    optuna_search.fit(X_train,y_train)
    trial = optuna_search.best_trial_
    bestparams=optuna_search.best_params_

    print('The %d fold!\t best trial=%r:best params=%r' % ((cv + 1), trial, bestparams))
    logging.warning('The %d fold!\t best trial=%r:best params=%r' % ((cv + 1), trial, bestparams))
    clf.set_params(**bestparams)
    clf.fit(X_train,y_train)
    # print("#######fold %d coef:%r"%(cv,clf.named_steps['classifier'].coef_))
    # logging.warning("#######fold %d coef:%r" % (cv, clf.named_steps['classifier'].coef_))
    # np.save("svm_%d.npy"%cv, clf.named_steps['classifier'].coef_)

    PredictLabel_test = clf.predict(X_test)
    PredictLabel_train = clf.predict(X_train)

    Accuracy_test = accuracy_score(y_test,PredictLabel_test)
    Sensitivity_test, Specifity_test = SenSpe(y_test, PredictLabel_test)
    Accuracy_train = accuracy_score(y_train,PredictLabel_train)
    Sensitivity_train, Specifity_train = SenSpe(y_train, PredictLabel_train)
    F1, Precision, Recall, Auc = Metrics(y_test, PredictLabel_test)
    # _, Permute_value = Permute_test(clf, X_train, y_train,n_permutation = 3)
    metric = allMetrics(Accuracy_test=Accuracy_test, Sensitivity_test=Sensitivity_test, Specifity_test=Specifity_test, \
                        Accuracy_train=Accuracy_train, Sensitivity_train=Sensitivity_train, Specifity_train=Specifity_train,F1=F1,\
                        Precision=Precision, Recall=Recall, Auc=Auc, Permute_value=0.1)

    print('The %d fold!\t metric=%r' % ((cv + 1), metric.metric))
    logging.warning('The %d fold!\t metric=%r' % ((cv + 1), metric.metric))

    return cv + 1, metric
