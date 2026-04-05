import numpy as np
import logging
from sklearn.metrics import roc_curve, auc,accuracy_score
from sklearn.model_selection import StratifiedKFold
import optuna
from scipy import interp

def computer_auc_simple(X_train,y_train,X_test,y_test,kFold,nIter,clf,param_distributions):
    tprs = []
    aucs = []
    mean_fpr = np.linspace(0, 1, 100)
    for i in range(nIter):
        logging.warning("starting iter %d",i)
        optuna_search = optuna.integration.OptunaSearchCV(
            clf, param_distributions, cv=StratifiedKFold(n_splits=kFold, shuffle=True), n_trials=10, timeout=600,
            verbose=2, max_iter=10, scoring='accuracy'
        )
        optuna_search.fit(X_train, y_train)
        trial = optuna_search.best_trial_
        bestparams = optuna_search.best_params_

        print('The best trial=%r:params_cliu=%r' % (trial, bestparams))
        logging.warning('The best trial=%r:params_cliu=%r' % (trial, bestparams))

        clf.set_params(**bestparams)

        # train a classification model with the selected features on the training dataset
        clf.fit(X_train, y_train)
        # predict = clf.predict(X_test)
        # fpr, tpr, thresholds = roc_curve(y_test, predict)
        try:
            probas_ = clf.predict_proba(X_test)
            fpr, tpr, thresholds = roc_curve(y_test, probas_[:, 1])
        except Exception as e:
            logging.warning('Fail to draw roc with proba in simple.')
            probas_ = clf.decision_function(X_test)
            fpr, tpr, thresholds = roc_curve(y_test, probas_)
        roc_auc = auc(fpr, tpr)

        tprs.append(interp(mean_fpr, fpr, tpr))
        tprs[-1][0] = 0.0
        aucs.append(roc_auc)
    return np.mean(tprs, axis=0),mean_fpr,aucs

def computer_auc_nested(SubjectsData,SubjectsLabel,kFold,nIter,clf,param_distributions):
    tprs = []
    aucs = []
    mean_fpr = np.linspace(0, 1, 100)
    for i in range(nIter):
        # the number of subjects
        SubjectQuantity = SubjectsData.shape[0]
        # permute the data and label
        index = np.arange(SubjectQuantity)
        np.random.shuffle(index)
        SubjectsData = SubjectsData[index]
        SubjectsLabel = SubjectsLabel[index]
        # generate the index of leave one out
        # partitions = np.array_split(index, kFold)
        au = []
        tp = []
        skf = StratifiedKFold(n_splits=kFold, shuffle=True)
        for TRAIN, TEST in skf.split(SubjectsData, SubjectsLabel):
            # divid train and test samples
            X_train = SubjectsData[TRAIN, :]
            y_train = SubjectsLabel[TRAIN]

            X_test = SubjectsData[TEST, :]
            y_test = SubjectsLabel[TEST]

            optuna_search = optuna.integration.OptunaSearchCV(
                clf, param_distributions, cv=StratifiedKFold(n_splits=kFold, shuffle=True), n_trials=10, timeout=600,
                verbose=2, max_iter=10, scoring='accuracy'
            )
            optuna_search.fit(X_train, y_train)
            trial = optuna_search.best_trial_
            bestparams = optuna_search.best_params_

            print('The best trial=%r:params_cliu=%r' % (trial, bestparams))
            logging.warning('The best trial=%r:params_cliu=%r' % (trial, bestparams))

            clf.set_params(**bestparams)

            # train a classification model with the selected features on the training dataset
            clf.fit(X_train, y_train)
            # predict = clf.predict(X_test)
            # fpr, tpr, thresholds = roc_curve(y_test, predict)
            try:
                probas_ = clf.predict_proba(X_test)
                fpr, tpr, thresholds = roc_curve(y_test, probas_[:, 1])
            except Exception as e:
                logging.warning('Fail to draw roc with proba in nested.')
                probas_ = clf.decision_function(X_test)
                fpr, tpr, thresholds = roc_curve(y_test, probas_)
            print("mean_fpr, fpr, tpr:",mean_fpr, fpr, tpr)
            print("interp(mean_fpr, fpr, tpr):", interp(mean_fpr, fpr, tpr))
            tp.append(interp(mean_fpr, fpr, tpr))

            tp[-1][0] = 0.0
            roc_auc = auc(fpr, tpr)
            au.append(roc_auc)

        tprs.append(np.mean(tp, axis=0))
        aucs.append(au)
    return np.mean(tprs, axis=0),mean_fpr,aucs