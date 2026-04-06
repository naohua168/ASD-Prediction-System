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

        clf.set_params(**param_distributions)

        # train a classification model with the selected features on the training dataset
        clf.fit(X_train, y_train)
        logging.warning("score is %f", clf.score(X_test,y_test))
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
        logging.warning("roc_auc is %f", roc_auc)

        tprs.append(interp(mean_fpr, fpr, tpr))
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
        partitions = np.array_split(index, kFold)
        au = []
        tp = []

        for cv in range(kFold):
            TRAIN = []
            for i in range(len(partitions)):
                if i != cv:
                    TRAIN.extend(partitions[i])

            TEST = partitions[cv]

            # divid train and test samples
            X_train = SubjectsData[TRAIN, :]
            y_train = SubjectsLabel[TRAIN]

            X_test = SubjectsData[TEST, :]
            y_test = SubjectsLabel[TEST]

            clf.set_params(**param_distributions)

            # train a classification model with the selected features on the training dataset
            clf.fit(X_train, y_train)
            #predict = clf.predict(X_test)
            # fpr, tpr, thresholds = roc_curve(y_test, predict)
            try:
                probas_ = clf.predict_proba(X_test)
                fpr, tpr, thresholds = roc_curve(y_test, probas_[:, 1])
            except Exception as e:
                logging.warning('Fail to draw roc with proba in nested.')
                probas_ = clf.decision_function(X_test)
                fpr, tpr, thresholds = roc_curve(y_test, probas_)
            tp.append(interp(mean_fpr, fpr, tpr))
            tp[-1][0] = 0.0
            roc_auc = auc(fpr, tpr)
            au.append(roc_auc)

        tprs.append(np.mean(tp, axis=0))
        aucs.append(au)
    return np.mean(tprs, axis=0),mean_fpr,aucs