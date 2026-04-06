import sys
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
import optuna
sys.path.append('/Utility')
from Utility.PerformanceMetrics import SenSpe, Metrics, Permute_test, allMetrics
import logging
import numpy as np
import itertools
from sklearn.model_selection import StratifiedKFold,cross_val_score

def CrossValidition_kFold(X_train,y_train,X_test,y_test,kFold,NormalizeFlag,NormalzeMode,clf,param_distributions):
    # # normalization
    # if NormalizeFlag == True:
    #     if NormalzeMode == 'MinMaxScaler':
    #         normalize = MinMaxScaler()
    #     elif NormalzeMode == 'StandardScaler':
    #         normalize = StandardScaler()
    #     elif NormalzeMode == 'Normalizer':
    #         normalize = Normalizer()
    #     X_train = normalize.fit_transform(X_train)
    #     X_test = normalize.transform(X_test)

    acc = []
    paras_value = [] #保存没有key的组合结果
    paras=[] #保存带key的传给clf的参数列表
    cv1 = StratifiedKFold(n_splits=5, shuffle=False)

    for s in itertools.product(*param_distributions.values()):
        paras_value.append(s)
    for p in paras_value:
        para_tmp = {}
        i = 0
        for key in param_distributions.keys():
            para_tmp[key] = p[i]
            i = i + 1
        paras.append(para_tmp)
        print(para_tmp)
        clf.set_params(**para_tmp)
        score = cross_val_score(clf, X_train, y_train, cv=cv1, scoring='accuracy', n_jobs=-1)
        acc.append(np.mean(score))

    a = np.argwhere(acc == np.max(acc))
    bestpara = paras[a[-1][0]]
    clf.set_params(**bestpara)
    print('The %d fold!\t best params=%r' % ((cv + 1), bestpara))
    logging.warning('The %d fold!\t best params=%r' % ((cv + 1), bestpara))

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

    print('The metric=%r' % ( metric.metric))
    logging.warning('The  metric=%r' % ( metric.metric))

    return metric
