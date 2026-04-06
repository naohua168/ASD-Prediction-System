from sklearn.base import TransformerMixin,BaseEstimator
import numpy as np
from scipy.stats import ttest_ind
def TwoSampleTest(SubjectData,SubjectLabel):
    nClass = np.unique(SubjectLabel)
    Group1Data = SubjectData[np.where(SubjectLabel==nClass[0])[0],:]
    Group2Data = SubjectData[np.where(SubjectLabel==nClass[1])[0],:]
    T,P = ttest_ind(Group1Data,Group2Data,axis=0,equal_var=False,nan_policy='omit')
    return T,P

class TwoSampleTestSelection(BaseEstimator,TransformerMixin):
    def __init__(self,estimator,pVal):
        self.estimator = estimator
        self.pVal = pVal
    def fit(self,X,y=None):
        T,P=self.estimator(X,y)
        # P[np.isnan(P)]=0
        TtestMask = np.zeros_like(P)
        TtestMask[np.where(P<=self.pVal)]=1
        self.mask = TtestMask
        return self
    def transform(self,X,y=None):
        X = np.delete(X,np.where(self.mask==0)[0],axis=1)
        return X


class SelectFeatures(BaseEstimator,TransformerMixin):
    def __init__(self,estimator,mode,n_features_select=None):
        # self.idx = idx
        # n_features_select = int(n_features_select)
        self.estimator = estimator
        self.mode = mode
        self.n_features_select = n_features_select
        # self.selectIdx = idx[0:n_features_select]
    def fit(self,X,y=None):
        idx=self.estimator(X,y,self.mode)
        self.selectIdx = idx[0:self.n_features_select]
        return self
    def transform(self,X,y=None):
        return X[:,self.selectIdx].copy()


