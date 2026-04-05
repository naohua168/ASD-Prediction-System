from sklearn.feature_selection import RFE,SelectKBest,chi2,f_classif,mutual_info_classif,f_regression,mutual_info_regression,SelectPercentile,SelectFdr,SelectFpr,SelectFwe,GenericUnivariateSelect

class TunedParaRang:
    def __init__(self,totalFeatures):
        self.totalFeatures=totalFeatures

        ##for SVM
        self.svm_C = 10
        ### for PCA
        self.pca_n_components = 0.98
        ####for lightGBM
        self.gbm_max_depth = 20
        self.gbm_learning_rate = 21
        self.gbm_lambda_l1 = 1
        self.gbm_lambda_l2 = 1
        self.gbm_num_leaves = 6
        self.gbm_feature_fraction = 0.7
        self.gbm_bagging_fraction = 0.7
        self.gbm_cat_smooth = 15

        ###### for random forest
        self.rf_n_estimators = 20
        self.rf_max_depth = 10

        #########for stablity
        self.stable_threshold =0.8

        ######mrmr
        self.mrmr_n_features_select=1000

        ######relief
        self.relief_n_features_select= 1000

        #####for SelectKBest
        self.skbest_k=300
        self.skbest_scoreFunc=chi2
        ####for Grandient Boosting
        ####tree parameters
        self.gb_min_samples_split = 6 # the 0.5%~1% of the number of samples
        self.gb_min_samples_leaf = 50
        self.gb_min_weight_fraction_leaf =0.5
        self.gb_max_depth = 10  #####3个范围？？？？？
        self.gb_max_leaf_nodes = 20

        ####boostig parameters
        self.gb_learning_rate = 0.01
        self.gb_n_estimators = 10
        self.gb_subsample = 0.8
        self.gb_max_features = 500

        ####for boruta
        self.boruta_perc = 90

        ####for rfe
        self.rfe_features = 500

        # ExtraTrees
        self.et_min_samples_split = 6 # the 0.5%~1% of the number of samples
        self.et_min_samples_leaf = 50
        self.et_n_estimators = 10
        self.et_max_features =500

        # knn
        self.knn_n_neighbors = 11
        self.knn_weights = "distance"

        # ada
        self.ada_n_estimators = 10

        # dtree
        self.dtree_min_samples_split = 6
        self.dtree_min_samples_leaf =50
        self.dtree_min_weight_fraction_leaf = 0.5
        self.dtree_max_depth = 10
        self.dtree_max_leaf_nodes = 500

        # log
        self.log_C = 0.01

        ####for xgboost
        ####tree parameters
        self.xgb_min_samples_split = 6
        self.xgb_min_samples_leaf = 50
        self.xgb_min_weight_fraction_leaf = 0.5
        self.xgb_max_depth =10
        self.xgb_max_leaf_nodes = 500

        ####boostig parameters
        self.xgb_learning_rate = 0.01
        self.xgb_n_estimators = 10
        self.xgb_subsample = 0.8
        self.xgb_max_features =500

        # for sgd
        self.sgd_loss = "modified_huber"
        self.sgd_penalty ="elasticnet"

        # ridge
        self.ridge_alpha = 10

        # bagging
        self.bag_n_estimators = 10
        self.bag_max_samples = 0.6
        self.bag_max_features =0.8

        # kernalpca
        self.kpca_n_components = 0.8
        self.kpca_kernel = "rbf"

        # for se
        self.se_n_components = 0.8
        self.se_affinity = "rbf"
        self.se_n_neighbors = 11
        self.se_eigen_solver ="lobpcg"

        # for feature hash
        self.fhash_n_features = 500

        # for fast ica
        self.fica_n_components = 500

        # for  vote
        self.vot_xgb_n_estimators = 11
        self.vot_gradientboosting_n_estimators = 11


