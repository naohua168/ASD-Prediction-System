import sys
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
import optuna
sys.path.append('/Utility')
from Utility.PerformanceMetrics import SenSpe, Metrics, Permute_test, allMetrics
import logging
from hyperopt import tpe,fmin,hp,space_eval,Trials
from functools import partial
from sklearn.metrics import accuracy_score
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

    trials =Trials()
    best = fmin(partial(HyoptCV,X=X_train,y=y_train,clf=clf),space=param_distributions,algo=tpe.suggest,max_evals=1,trials=trials)#anneal.suggest  tpe.suggest
    best_params = space_eval(param_distributions, best)
    print('The best_params:%r'%(best_params))
    logging.warning('The best_params:%r'%(best_params))

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

    print('The metric=%r' % ( metric.metric))
    logging.warning('The metric=%r' % ( metric.metric))

    return metric

def HyoptCV(params,X,y,clf):
    clf.set_params(**params)
    cv = StratifiedKFold(n_splits=5, shuffle=True)
    score = cross_val_score(clf,X,y,cv=cv,scoring='accuracy',n_jobs=-1)
    return 1-score.mean()