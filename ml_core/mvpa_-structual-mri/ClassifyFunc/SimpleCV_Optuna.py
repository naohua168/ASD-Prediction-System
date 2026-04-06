import sys
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
import optuna
sys.path.append('/Utility')
from Utility.PerformanceMetrics import SenSpe, Metrics,  allMetrics
import logging

def CrossValidition_kFold(X_train,y_train,X_test,y_test,kFold,NormalizeFlag,NormalzeMode,clf,param_distributions,max_iter=10):
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

    optuna_search = optuna.integration.OptunaSearchCV(
        clf, param_distributions, cv=StratifiedKFold(n_splits=kFold,shuffle=True),n_trials=10, timeout=600, verbose=2,max_iter=max_iter,scoring='accuracy'
    )
    optuna_search.fit(X_train,y_train)
    trial = optuna_search.best_trial_
    bestparams=optuna_search.best_params_

    print('The best trial=%r:params_cliu=%r' % (trial, bestparams))
    logging.warning('The best trial=%r:params_cliu=%r' % ( trial, bestparams))

    clf.set_params(**bestparams)
    clf.fit(X_train,y_train)
    PredictLabel_test = clf.predict(X_test)
    PredictLabel_train = clf.predict(X_train)

    Accuracy_test = accuracy_score(y_test,PredictLabel_test)
    Sensitivity_test, Specifity_test = SenSpe(y_test, PredictLabel_test)
    Accuracy_train = accuracy_score(y_train,PredictLabel_train)
    Sensitivity_train, Specifity_train = SenSpe(y_train, PredictLabel_train)
    F1, Precision, Recall, Auc = Metrics(y_test, PredictLabel_test)
    # _, Permute_value = Permute_test(clf, X_train, y_train,n_permutation = 5000)
    metric = allMetrics(Accuracy_test=Accuracy_test, Sensitivity_test=Sensitivity_test, Specifity_test=Specifity_test, \
                        Accuracy_train=Accuracy_train, Sensitivity_train=Sensitivity_train, Specifity_train=Specifity_train,F1=F1,\
                        Precision=Precision, Recall=Recall, Auc=Auc, Permute_value=0.1,max_iter=max_iter)

    print('The metric=%r' % ( metric.metric))
    logging.warning('The metric=%r' % ( metric.metric))

    return metric
