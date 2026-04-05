import numpy as np
import sys
import scipy.io as sio
import logging
from sklearn.metrics import roc_curve, auc,accuracy_score
sys.path.append('/Utility')
from Utility.PerformanceMetrics import SenSpe
def DisplaySaveResults_LOOCV(CvIdx,TrueLabels,PredictLabels,ResultantFolder):
    # show results
    Group1TrueLabels = TrueLabels[np.where(TrueLabels==-1)]
    Group2TrueLabels = TrueLabels[np.where(TrueLabels==1)]

    Group1PredictLabels = PredictLabels[np.where(TrueLabels==-1)]
    Group2PredictLabels = PredictLabels[np.where(TrueLabels==1)]

    Group1CVIdx = CvIdx[np.where(TrueLabels==-1)[0]]
    Group2CVIdx = CvIdx[np.where(TrueLabels==1)[0]]-len(np.where(TrueLabels==1)[0])

    Group1WrongSujbects = np.where(Group1PredictLabels!=Group1TrueLabels)
    Group2WrongSujbects = np.where(Group2PredictLabels != Group2TrueLabels)

    print('group1:%d out of %d subjects are wrong '%(np.array(Group1WrongSujbects).shape[1],len(Group1CVIdx)),Group1CVIdx[Group1WrongSujbects])
    print('group2:%d out of %d subjects are wrong ' % (np.array(Group2WrongSujbects).shape[1],len(Group2CVIdx)),Group2CVIdx[Group2WrongSujbects])
    logging.debug('group1:%d out of %d subjects are wrong ;%r'%(np.array(Group1WrongSujbects).shape[1],len(Group1CVIdx),Group1CVIdx[Group1WrongSujbects]))
    logging.debug('group2:%d out of %d subjects are wrong ;%r' % (np.array(Group2WrongSujbects).shape[1],len(Group2CVIdx),Group2CVIdx[Group2WrongSujbects]))

    Accuracies = accuracy_score(TrueLabels,PredictLabels)
    print('Average accuracy=',np.mean(Accuracies))
    Sensitivity, Specifity = SenSpe(TrueLabels,PredictLabels)
    print('Sensitivity = %f \t Specifity = %f'%(Sensitivity,Specifity))
    logging.debug('Average accuracy=%f \t Sensitivity = %f \t Specifity = %f'%(np.mean(Accuracies),Sensitivity,Specifity))
    # save results
    ResultantFile = ResultantFolder+'results.mat'
    ResultsLOOCV = {'Accuracies': Accuracies, 'TrueLabels':TrueLabels,'PredictLabels': PredictLabels,'AverageAccuracy':np.mean(Accuracies),'Sensitivity':Sensitivity,'Specifity':Specifity}
    sio.savemat(ResultantFile,ResultsLOOCV)

