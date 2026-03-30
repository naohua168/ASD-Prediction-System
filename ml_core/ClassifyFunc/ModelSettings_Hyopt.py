from hyperopt import hp
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
        self.svm_C = hp.loguniform('C', -4.0 * np.log(10.0), 4.0 * np.log(10.0))
        ### for PCA
        self.pca_n_components = hp.uniform('n_components', 0.4, 0.99)
        ####for lightGBM
        self.gbm_max_depth = hp.uniformint('max_depth', 10, int(self.sampleNum*self.max_depth))
        self.gbm_learning_rate = hp.uniform('learning_rate', 0.01, 0.15)
        self.gbm_lambda_l1 = hp.uniform('lambda_l1', 1e-8, 10.0)
        self.gbm_lambda_l2 = hp.uniform('lambda_l2', 1e-8, 10.0)
        self.gbm_num_leaves = hp.uniformint('num_leaves', 2, 256)
        self.gbm_feature_fraction = hp.uniform('feature_fraction', 0.4, 0.99)
        self.gbm_bagging_fraction = hp.uniform('bagging_fraction', 0.4, 0.99)
        self.gbm_cat_smooth = hp.uniformint('cat_smooth', 1, 35)

        ###### for random forest
        self.rf_n_estimators = hp.uniformint('n_estimators', 5, 30)
        self.rf_max_depth = hp.uniformint('max_depth', 3, int(self.sampleNum*self.max_depth))

        #########for stablity
        self.stable_threshold = hp.uniform('threshold', 0.5, 1)

        ######mrmr
        self.mrmr_n_features_select=hp.uniformint('n_features_select',self.minFeatures,self.totalFeatures)

        ######relief
        self.relief_n_features_select= hp.uniformint('n_features_select',self.minFeatures,self.totalFeatures)

        #####for SelectKBest
        self.skbest_k=hp.uniformint('k',10,self.totalFeatures)
        self.skbest_scoreFunc=hp.choice('scoreFunc',[chi2, f_classif, mutual_info_classif,f_regression,mutual_info_regression])
        # not use  SelectFdr,SelectPercentile,SelectFpr,SelectFwe,GenericUnivariateSelect

        ####for Grandient Boosting
        ####tree parameters
        self.gb_min_samples_split = hp.uniformint('min_samples_split',1,100) # the 0.5%~1% of the number of samples
        self.gb_min_samples_leaf = hp.uniformint('min_samples_leaf',1,100)
        self.gb_min_weight_fraction_leaf = hp.uniform('min_weight_fraction_leaf',0.1,0.9)
        self.gb_max_depth = hp.uniformint('max_depth',1,int(self.sampleNum*self.max_depth))
        self.gb_max_leaf_nodes = hp.uniformint('max_leaf_nodes',1,100)

        ####boostig parameters
        self.gb_learning_rate = hp.uniform('learning_rate',0.01, 0.15)
        self.gb_n_estimators = hp.uniform('n_estimators',3,10)
        self.gb_subsample = hp.uniform('subsample',0.1,0.9) # 0.8 for most cases
        self.gb_max_features = hp.uniformint('max_features',10,self.totalFeatures)

        ####for boruta
        self.boruta_perc = hp.uniformint('perc',80,100)

        ####for rfe
        self.rfe_features = hp.uniformint('n_features_to_select',self.minFeatures,self.totalFeatures)
        #hp.randint(self.totalFeatures-self.minFeatures)


