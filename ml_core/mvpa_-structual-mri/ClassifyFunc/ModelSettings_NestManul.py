from sklearn.feature_selection import RFE,SelectKBest,chi2,f_classif,mutual_info_classif,f_regression,mutual_info_regression,SelectPercentile,SelectFdr,SelectFpr,SelectFwe,GenericUnivariateSelect
import numpy as np

class TunedParaRang:
    def __init__(self, totalFeatures, sampleNum):
        self.totalFeatures = totalFeatures
        self.sampleNum = sampleNum
        self.neibers = 0.25
        self.max_depth = 0.3
        self.minFeatures=300
        ##for SVM
        self.svm_C = [0.01, 0.1]
        ### for PCA
        self.pca_n_components = np.arange(0.8, 1, 0.1)
        ####for lightGBM
        self.gbm_max_depth = range(3, int(self.sampleNum*self.max_depth))
        self.gbm_learning_rate = np.arange(0.01, 0.15, 0.05)
        self.gbm_lambda_l1 = np.arange(0.4, 1, 0.5)
        self.gbm_lambda_l2 = np.arange(0.4, 1, 0.5)
        self.gbm_num_leaves = [2, 256]
        self.gbm_feature_fraction = np.arange(0.4, 1, 0.5)
        self.gbm_bagging_fraction = np.arange(0.4, 1, 0.5)
        self.gbm_cat_smooth = [1, 35]

        ###### for random forest
        self.rf_n_estimators = [5, 10, 20, 30]
        self.rf_max_depth = [5, 10, int(self.sampleNum*self.max_depth)]

        #########for stablity
        self.stable_threshold = np.arange(0.5, 1, 0.1)

        ######mrmr
        self.mrmr_n_features_select=[self.minFeatures,int(self.totalFeatures)]

        ######relief
        self.relief_n_features_select=[self.minFeatures,int(self.totalFeatures)]

        #####for SelectKBest
        self.skbest_k=[10,int(self.totalFeatures/2)]
        self.skbest_scoreFunc=[chi2, f_classif, mutual_info_classif,f_regression,mutual_info_regression]

        ####for Grandient Boosting
        ####tree parameters
        self.gb_min_samples_split = [1,100] # the 0.5%~1% of the number of samples
        self.gb_min_samples_leaf = [1,100]
        self.gb_min_weight_fraction_leaf = np.arange(0.1, 0.9, 0.1)
        self.gb_max_depth = [1,int(self.sampleNum*self.max_depth)]
        self.gb_max_leaf_nodes = [1,100]

        ####boostig parameters
        self.gb_learning_rate = np.arange(0.01, 0.15, 0.05)
        self.gb_n_estimators = range(3, 10)
        self.gb_subsample = np.arange(0.1,0.9)
        self.gb_max_features = [10,int(self.totalFeatures)]

        ####for boruta
        self.boruta_perc = range(80,100)
        ####for rfe
        self.rfe_features = range(self.minFeatures,self.totalFeatures)


